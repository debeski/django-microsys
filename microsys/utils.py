from django.apps import apps
from django.utils.module_loading import import_string
from django.forms import modelform_factory
import django_tables2 as tables
from django.http import JsonResponse
# try-except for django_filters as it might not be installed (though likely is)
try:
    import django_filters
except ImportError:
    django_filters = None

from django.db.models import ManyToManyField, ManyToManyRel, Q
from django.db import models as dj_models
from decimal import Decimal, InvalidOperation
import inspect


def _get_model_app_bases(model):
    """
    Return possible import bases for a model's app.
    Uses AppConfig.name (full python path) and falls back to module/app_label.
    """
    bases = []
    try:
        app_config = apps.get_app_config(model._meta.app_label)
        if app_config and app_config.name:
            bases.append(app_config.name)
    except LookupError:
        pass

    module_base = model.__module__.rsplit('.', 1)[0]
    if module_base not in bases:
        bases.append(module_base)

    if model._meta.app_label not in bases:
        bases.append(model._meta.app_label)

    return bases


def _import_by_convention(model, submodule, class_suffix):
    """
    Try importing a class following App.<submodule>.ModelName<class_suffix>.
    Returns class or None if not found.
    """
    class_name = f"{model.__name__}{class_suffix}"
    for base in _get_model_app_bases(model):
        try:
            return import_string(f"{base}.{submodule}.{class_name}")
        except ImportError:
            continue
    return None


def _resolve_model_class(model, getter_name):
    """
    Resolve class from model method/attr that may return a class or a string path.
    """
    if not hasattr(model, getter_name):
        return None

    try:
        value = getattr(model, getter_name)
        value = value() if callable(value) else value
    except Exception:
        return None

    if isinstance(value, str):
        try:
            return import_string(value)
        except (ImportError, ValueError, AttributeError, TypeError):
            return None

    if inspect.isclass(value):
        return value

    return None


def _model_is_section(model):
    """
    Determine if a model should be treated as a section model.
    Accepts class attr, Meta attr, or any non-falsey marker.
    """
    val = getattr(model, 'is_section', None)
    if isinstance(val, bool):
        return val
    if val is not None:
        return True
    return bool(getattr(model._meta, 'is_section', False))


def resolve_form_class_for_model(model):
    """
    Resolve a ModelForm class for a model using conventions or fallbacks.
    """
    form_class = _import_by_convention(model, "forms", "Form")
    if not form_class:
        form_class = (
            _resolve_model_class(model, "get_form_class")
            or _resolve_model_class(model, "get_form_class_path")
        )
    if not form_class:
        try:
            has_scope_field = model._meta.get_field("scope") is not None
        except Exception:
            has_scope_field = False

        if has_scope_field and not is_scope_enabled():
            form_class = modelform_factory(model, exclude=["scope"])
        else:
            form_class = modelform_factory(model, fields='__all__')
    return form_class


def _build_generic_table_class(model):
    """
    Build a minimal django-tables2 Table for a model.
    Build Meta dynamically so django-tables2 sees Meta.model at class creation.
    """
    meta_attrs = {
        "model": model,
        "template_name": "django_tables2/bootstrap5.html",
        "attrs": {'class': 'table table-striped table-sm table align-middle'},
    }
    Meta = type("Meta", (), meta_attrs)
    table_attrs = {"Meta": Meta}
    return type(f"{model.__name__}AutoTable", (tables.Table,), table_attrs)


def _build_generic_filter_class(model):
    """
    Build a minimal django-filters FilterSet:
    - keyword search across text fields (and numeric fields if value is numeric)
    - optional year dropdown if any date/datetime field exists
    """
    if not django_filters:
        return None

    text_fields = []
    int_fields = []
    num_fields = []
    date_field = None

    for field in model._meta.get_fields():
        if not hasattr(field, 'attname'):
            continue
        if field.many_to_many or field.one_to_many:
            continue

        if isinstance(field, (dj_models.CharField, dj_models.TextField, dj_models.EmailField, dj_models.SlugField, dj_models.URLField)):
            text_fields.append(field.name)
        elif isinstance(field, (dj_models.IntegerField, dj_models.BigIntegerField, dj_models.SmallIntegerField, dj_models.PositiveIntegerField, dj_models.PositiveSmallIntegerField)):
            int_fields.append(field.name)
        elif isinstance(field, (dj_models.FloatField, dj_models.DecimalField)):
            num_fields.append(field.name)
        elif date_field is None and isinstance(field, (dj_models.DateField, dj_models.DateTimeField)):
            date_field = field.name

    def _parse_number(value):
        if value is None:
            return None
        try:
            return Decimal(str(value))
        except (InvalidOperation, ValueError):
            return None

    def _init(self, *args, **kwargs):
        super(self.__class__, self).__init__(*args, **kwargs)

        if date_field and 'year' in self.filters:
            years = self.Meta.model.objects.dates(date_field, 'year').distinct()
            self.filters['year'].extra['choices'] = [(year.year, year.year) for year in years]
            self.filters['year'].field.widget.attrs.update({
                'class': 'auto-submit-filter'
            })

        if not hasattr(self.form, 'helper') or self.form.helper is None:
            from crispy_forms.helper import FormHelper
            from crispy_forms.layout import Layout, Row, Column, Field, HTML, Hidden

            self.form.helper = FormHelper()
            self.form.helper.form_method = 'GET'
            self.form.helper.form_class = 'form-inline'
            self.form.helper.form_show_labels = False
            self.form.helper.layout = Layout()

            if 'sort' in self.data:
                self.form.helper.layout.append(Hidden('sort', self.data['sort']))
            if 'model' in self.data:
                self.form.helper.layout.append(Hidden('model', self.data['model']))

            row_fields = [
                Column(Field('keyword', placeholder="البحث"), css_class='form-group col-auto flex-fill'),
            ]
            if date_field and 'year' in self.filters:
                row_fields.append(Column(Field('year', placeholder="السنة", dir="rtl"), css_class='form-group col-auto'))

            clear_url = '{% url "manage_sections" %}'
            query_params = []
            if 'model' in self.data:
                query_params.append(f"model={self.data['model']}")
            if 'sort' in self.data:
                query_params.append(f"sort={self.data['sort']}")
            if query_params:
                clear_url += "?" + "&".join(query_params)

            ignore_params = ['sort', 'page', 'model']
            has_active_filters = any(key for key in self.data if key not in ignore_params)

            if has_active_filters:
                search_btn = '<button type="submit" class="btn btn-secondary rounded-start-pill rounded-end-0"><i class="bi bi-search"></i></button>'
                clear_btn = f'<a href="{clear_url}" class="btn btn-warning rounded-end-pill rounded-start-0"><i class="bi bi-x-lg"></i></a>'
                buttons_html = [
                    Column(HTML(search_btn), css_class='form-group col-auto pe-0'),
                    Column(HTML(clear_btn), css_class='form-group col-auto ps-0'),
                ]
            else:
                search_btn = '<button type="submit" class="btn btn-secondary rounded-pill"><i class="bi bi-search"></i></button>'
                buttons_html = [
                    Column(HTML(search_btn), css_class='form-group col-auto text-center'),
                ]

            row_fields.extend(buttons_html)
            self.form.helper.layout.append(Row(*row_fields, css_class='form-row'))

    def _filter_keyword(self, queryset, name, value, text_fields=text_fields, int_fields=int_fields, num_fields=num_fields):
        if not value:
            return queryset

        q_obj = Q()
        for field_name in text_fields:
            q_obj |= Q(**{f"{field_name}__icontains": value})

        numeric_value = _parse_number(value)
        if numeric_value is not None:
            is_int = numeric_value == numeric_value.to_integral_value()
            if is_int:
                int_value = int(numeric_value)
                for field_name in int_fields:
                    q_obj |= Q(**{field_name: int_value})
            for field_name in num_fields:
                q_obj |= Q(**{field_name: numeric_value})

        return queryset.filter(q_obj) if q_obj else queryset

    meta_attrs = {"model": model, "fields": []}
    Meta = type("Meta", (), meta_attrs)

    attrs = {
        "Meta": Meta,
        "__init__": _init,
        "filter_keyword": _filter_keyword,
        "keyword": django_filters.CharFilter(method='filter_keyword', label=''),
    }
    if date_field:
        attrs["year"] = django_filters.ChoiceFilter(
            field_name=f"{date_field}__year",
            lookup_expr="exact",
            choices=[],
            empty_label="السنة",
        )

    return type(f"{model.__name__}AutoFilter", (django_filters.FilterSet,), attrs)


def is_scope_enabled():
    """
    Checks if the Scope system is globally enabled.
    Returns:
        bool: True if enabled, False otherwise.
    """
    try:
        ScopeSettings = apps.get_model('microsys', 'ScopeSettings')
        return ScopeSettings.load().is_enabled
    except LookupError:
        # Fallback if model shouldn't be loaded yet (e.g. migration)
        return True


def _is_child_model(model, app_name=None):
    """
    Detect if a model is a "child model" - one that exists primarily 
    to be linked via M2M to a parent model.
    
    A model is considered a child if:
    - It has a ManyToManyRel (is the target of a M2M from another model)
    - It doesn't have its own table classmethod (won't be displayed standalone)
    """
    meta = model._meta
    
    # Check if this model is referenced via M2M from another model
    has_m2m_rel = any(
        isinstance(f, ManyToManyRel) 
        for f in meta.get_fields()
    )
    
    # Check if model lacks table classmethod (not meant for standalone display)
    lacks_table = not hasattr(model, 'get_table_class_path') and not hasattr(model, 'get_table_class')
    
    return has_m2m_rel and lacks_table


def has_related_records(instance, ignore_relations=None):
    """
    Check if a model instance has any related records (FK, M2M, OneToOne).
    Returns True if any related objects exist, False otherwise.
    Used for locking logic (preventing deletion/unlinking).
    
    ignore_relations: list of accessor names to skip (e.g. ['affiliates', 'company_set'])
    """
    if not instance:
        return False
    
    if ignore_relations is None:
        ignore_relations = []
        
    for related_object in instance._meta.get_fields():
        if related_object.is_relation and related_object.auto_created:
            # Reverse relationship (Someone points to us)
            accessor_name = related_object.get_accessor_name()
            if not accessor_name or accessor_name in ignore_relations:
                continue
                
            try:
                # Get the related manager/descriptor
                related_item = getattr(instance, accessor_name)
                
                # Check based on relationship type
                if related_object.one_to_many or related_object.many_to_many:
                     if related_item.exists():
                         return True
                elif related_object.one_to_one:
                     # OneToOne
                     pass 
            except Exception:
                # DoesNotExist or other issues
                continue
            
            # For O2O
            if related_object.one_to_one and related_item:
                return True
                
    return False


def discover_section_models(app_name=None, include_children=False):
    """
    Discover section models based on explicit `is_section = True` in class/meta.
    Automatically resolves Form, Table, and Filter classes (by convention or generation).
    Identifies 'subsection' models (M2M children) for automatic modal handling.
    
    Args:
        app_name: Optional. If provided, filter results to this app only.
        include_children: If True, includes child models (M2M targets) even if not
                          explicitly marked as sections. Default False.
    
    Returns:
        List of dicts containing section model info:
        {
            'model': Model class,
            'model_name': Model name (lowercase),
            'app_label': App label,
            'verbose_name': Arabic verbose name,
            'verbose_name_plural': Arabic verbose name plural,
            'form_class': Form class (imported or generated),
            'table_class': Table class (imported or generated),
            'filter_class': Filter class (imported or generated),
            'subsections': List of dicts for child models (M2M targets):
                {
                    'model': ChildModel,
                    'model_name': ...,
                    'verbose_name': ...,
                    'related_field': field_name (in parent),
                    'form_class': ChildFormClass (imported or generated)
                }
        }
    """
    section_models = []
    
    # Get app configs to iterate
    if app_name:
        try:
            app_configs = [apps.get_app_config(app_name)]
        except LookupError:
            return []
    else:
        app_configs = apps.get_app_configs()
    
    for app_config in app_configs:
        # Skip Django's built-in apps
        if app_config.name.startswith('django.'):
            continue
        
        for model in app_config.get_models():
            meta = model._meta
            
            # SKIP: Dummy models (managed = False)
            if not meta.managed:
                continue
            
            # SKIP: Abstract models
            if meta.abstract:
                continue
            
            # Detect if this is a child model (M2M target without table)
            is_child = _is_child_model(model, app_config.label)

            # Include models explicitly marked as sections, plus children if requested
            is_section = _model_is_section(model)
            if not is_section and not (include_children and is_child):
                continue
            
            # --- Resolve Classes (Form, Table, Filter) ---
            # 1. Form
            form_class = resolve_form_class_for_model(model)

            # 2. Table
            table_class = _import_by_convention(model, "tables", "Table")
            if not table_class:
                # Fallback: legacy methods
                table_class = (
                    _resolve_model_class(model, "get_table_class")
                    or _resolve_model_class(model, "get_table_class_path")
                )
            
            # Generate if not found
            if not table_class:
                 table_class = _build_generic_table_class(model)

            # 3. Filter
            filter_class = _import_by_convention(model, "filters", "Filter")
            if not filter_class:
                # Fallback
                filter_class = (
                    _resolve_model_class(model, "get_filter_class")
                    or _resolve_model_class(model, "get_filter_class_path")
                )
            
            # Generate if not found (optional, requires django_filters)
            if not filter_class and django_filters:
                 filter_class = _build_generic_filter_class(model)

            # --- Identify Subsections (M2M Children) ---
            subsections = []
            for field in meta.get_fields():
                if isinstance(field, ManyToManyField):
                    child_model = field.related_model
                    child_meta = child_model._meta
                    
                    # Verify it's a "subsection/child" type model
                    if _is_child_model(child_model):
                         # Resolve child form for the "Add" modal
                         child_form_class = resolve_form_class_for_model(child_model)
                             
                         subsections.append({
                             'model': child_model,
                             'model_name': child_meta.model_name,
                             'verbose_name': child_meta.verbose_name,
                             'verbose_name_plural': child_meta.verbose_name_plural,
                             'related_field': field.name,
                             'form_class': child_form_class
                         })

            section_models.append({
                'model': model,
                'model_name': meta.model_name,
                'app_label': meta.app_label,
                'verbose_name': meta.verbose_name,
                'verbose_name_plural': meta.verbose_name_plural,
                'form_class': form_class,
                'table_class': table_class,
                'filter_class': filter_class,
                'subsections': subsections,
                'is_child': is_child,
            })
    
    return section_models


def get_default_section_model(app_name=None):
    """
    Get the first available section model name for auto-selection.
    
    Returns:
        String model_name of the first section model, or None if none found.
    """
    section_models = discover_section_models(app_name=app_name)
    if section_models:
        return section_models[0]['model_name']
    return None


def get_model_classes(model_name, app_label=None):
    """
    Dynamically import model, form, table, and filter classes for a given model.
    """
    if not model_name:
        return None
    
    model = resolve_model_by_name(model_name, app_label=app_label)
    if not model:
        return None
    
    # We can use discover_section_models to find it or just resolve manually
    # For now, manually resolution based on conventions
    meta = model._meta
    
    # Form
    form_class = resolve_form_class_for_model(model)
        
    # Table
    table_class = _import_by_convention(model, "tables", "Table")
    if not table_class:
         table_class = _resolve_model_class(model, "get_table_class")
    if not table_class:
         table_class = _build_generic_table_class(model)

    # Filter
    filter_class = _import_by_convention(model, "filters", "Filter")
    if not filter_class and django_filters:
         filter_class = _build_generic_filter_class(model)

    return {
        'model': model,
        'form': form_class,
        'table': table_class,
        'filter': filter_class,
        'ar_name': meta.verbose_name,
        'ar_names': meta.verbose_name_plural,
    }


def resolve_model_by_name(model_name, app_label=None):
    """
    Resolve a model by name, optionally constrained to an app label.
    Falls back to scanning all apps if app_label is not provided.
    """
    if not model_name:
        return None

    normalized = model_name.lower()

    if app_label:
        try:
            return apps.get_model(app_label, model_name)
        except LookupError:
            return None

    for model in apps.get_models():
        meta = model._meta
        if meta.model_name == normalized or model.__name__.lower() == normalized:
            return model

    return None


def get_class_from_string(class_path):
    """Dynamically imports and returns a class from a string path."""
    return import_string(class_path)

# Helper Function that handles the sidebar toggle and state
def toggle_sidebar(request):
    if request.method == "POST" and request.user.is_authenticated:
        collapsed = request.POST.get("collapsed") == "true"
        request.session["sidebarCollapsed"] = collapsed
        return JsonResponse({"status": "success"})
    return JsonResponse({"status": "error"}, status=400)
