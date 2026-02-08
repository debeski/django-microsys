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

from django.db.models import ManyToManyField, ManyToManyRel
from django.utils.module_loading import import_string

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
    Discover section models based on explicit `is_section = True` in class.
    Automatically resolves Form, Table, and Filter classes (by convention or generation).
    Identifies 'subsection' models (M2M children) for automatic modal handling.
    
    Args:
        app_name: Optional. If provided, filter results to this app only.
        include_children: If True, includes child models (M2M targets) in results.
                          Default False - excludes child models from main tab list.
    
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
            
            # REQUIRED: Must have is_section = True class attribute
            is_section = getattr(model, 'is_section', False)
            if not is_section:
                continue
            
            # Detect if this is a child model (M2M target without table)
            is_child = _is_child_model(model, app_config.label)
            
            # Skip children unless explicitly requested for main list
            if is_child and not include_children:
                continue
            
            # --- Resolve Classes (Form, Table, Filter) ---
            # 1. Form
            form_class = None
            # Try convention: App.forms.ModelNameForm
            form_path = f"{meta.app_label}.forms.{model.__name__}Form"
            try:
                form_class = import_string(form_path)
            except ImportError:
                # Fallback: get_form_class / get_form_class_path (Legacy support)
                if hasattr(model, 'get_form_class'):
                     try: form_class = import_string(model.get_form_class())
                     except: pass
                elif hasattr(model, 'get_form_class_path'):
                     try: form_class = import_string(model.get_form_class_path())
                     except: pass
            
            # Generate if not found
            if not form_class:
                form_class = modelform_factory(model, fields='__all__')

            # 2. Table
            table_class = None
            # Try convention: App.tables.ModelNameTable
            table_path = f"{meta.app_label}.tables.{model.__name__}Table"
            try:
                table_class = import_string(table_path)
            except ImportError:
                # Fallback: legacy methods
                if hasattr(model, 'get_table_class'):
                     try: table_class = import_string(model.get_table_class())
                     except: pass
                elif hasattr(model, 'get_table_class_path'):
                     try: table_class = import_string(model.get_table_class_path())
                     except: pass
            
            # Generate if not found
            if not table_class:
                 class GenericTable(tables.Table):
                     class Meta:
                         model = model
                         template_name = "django_tables2/bootstrap5.html"
                         attrs = {'class': 'table table-striped table-sm table align-middle'}
                 table_class = GenericTable

            # 3. Filter
            filter_class = None
            # Try convention: App.filters.ModelNameFilter
            filter_path = f"{meta.app_label}.filters.{model.__name__}Filter"
            try:
                filter_class = import_string(filter_path)
            except ImportError:
                 # Fallback
                 if hasattr(model, 'get_filter_class'):
                     try: filter_class = import_string(model.get_filter_class())
                     except: pass
                 elif hasattr(model, 'get_filter_class_path'):
                     try: filter_class = import_string(model.get_filter_class_path())
                     except: pass
            
            # Generate if not found (optional, requires django_filters)
            if not filter_class and django_filters:
                 # Minimal generation or just leave None
                 pass

            # --- Identify Subsections (M2M Children) ---
            subsections = []
            for field in meta.get_fields():
                if isinstance(field, ManyToManyField):
                    child_model = field.related_model
                    child_meta = child_model._meta
                    
                    # Verify it's a "subsection/child" type model
                    if _is_child_model(child_model):
                         # Resolve child form for the "Add" modal
                         child_form_class = None
                         child_form_path = f"{child_meta.app_label}.forms.{child_model.__name__}Form"
                         try:
                             child_form_class = import_string(child_form_path)
                         except ImportError:
                             if hasattr(child_model, 'get_form_class'):
                                 try: child_form_class = import_string(child_model.get_form_class())
                                 except: pass
                         
                         if not child_form_class:
                             child_form_class = modelform_factory(child_model, fields='__all__')
                             
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


def get_default_section_model(app_name='main'):
    """
    Get the first available section model name for auto-selection.
    
    Returns:
        String model_name of the first section model, or None if none found.
    """
    section_models = discover_section_models(app_name=app_name)
    if section_models:
        return section_models[0]['model_name']
    return None


def get_model_classes(model_name, app_label='main'):
    """
    Dynamically import model, form, table, and filter classes for a given model.
    """
    if not model_name:
        return None
    
    try:
        model = apps.get_model(app_label, model_name)
    except LookupError:
        return None
    
    # We can use discover_section_models to find it or just resolve manually
    # For now, manually resolution based on conventions
    meta = model._meta
    
    # Form
    form_class = None
    form_path = f"{meta.app_label}.forms.{model.__name__}Form"
    try:
        form_class = import_string(form_path)
    except ImportError:
        if hasattr(model, 'get_form_class'):
            try: form_class = import_string(model.get_form_class())
            except: pass
    if not form_class:
        form_class = modelform_factory(model, fields='__all__')
        
    # Table
    table_class = None
    table_path = f"{meta.app_label}.tables.{model.__name__}Table"
    try:
        table_class = import_string(table_path)
    except ImportError:
         if hasattr(model, 'get_table_class'):
            try: table_class = import_string(model.get_table_class())
            except: pass
    if not table_class:
         class GenericTable(tables.Table):
             class Meta:
                 model = model
                 template_name = "django_tables2/bootstrap5.html"
                 attrs = {'class': 'table table-striped table-sm table align-middle'}
         table_class = GenericTable

    # Filter
    filter_class = None
    filter_path = f"{meta.app_label}.filters.{model.__name__}Filter"
    try:
        filter_class = import_string(filter_path)
    except ImportError:
         pass

    return {
        'model': model,
        'form': form_class,
        'table': table_class,
        'filter': filter_class,
        'ar_name': meta.verbose_name,
        'ar_names': meta.verbose_name_plural,
    }


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