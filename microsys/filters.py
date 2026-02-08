# Imports of the required python modules and libraries
######################################################
import django_filters
from django.contrib.auth import get_user_model
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Row, Column, Field, HTML, Hidden
from django.db.models import Q
from django.apps import apps
from microsys.utils import is_scope_enabled

User = get_user_model()

class UserFilter(django_filters.FilterSet):
    keyword = django_filters.CharFilter(
        method='filter_keyword',
        label='',
    )
    class Meta:
        model = User
        fields = []
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.form.helper = FormHelper()
        self.form.helper.form_method = 'GET'
        self.form.helper.form_class = 'form-inline'
        self.form.helper.form_show_labels = False
        self.form.helper.layout = Layout()
        
        if 'sort' in self.data:
            self.form.helper.layout.append(Hidden('sort', self.data['sort']))
        
        clear_url = '{% url "manage_users" %}'
        query_params = []
        if 'sort' in self.data:
            query_params.append(f"sort={self.data['sort']}")
        
        if query_params:
            clear_url += "?" + "&".join(query_params)

        ignore_params = ['sort', 'page']
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

        self.form.helper.layout.append(
            Row(
                Column(Field('keyword', placeholder="البحث", css_class='form-control glass-input h-100'), css_class='form-group col-auto flex-fill'),
                *buttons_html,
                css_class='form-row align-items-stretch'
            ),
        )
    def filter_keyword(self, queryset, name, value):
        return queryset.filter(
            Q(username__icontains=value) |
            Q(email__icontains=value) |
            Q(profile__phone__icontains=value) | # Updated lookup
            Q(profile__scope__name__icontains=value) | # Updated lookup
            Q(first_name__icontains=value) |
            Q(last_name__icontains=value)
        )


class UserActivityLogFilter(django_filters.FilterSet):
    keyword = django_filters.CharFilter(
        method='filter_keyword',
        label='',
    )
    year = django_filters.ChoiceFilter(
        field_name="timestamp__year",
        lookup_expr="exact",
        choices=[],
        empty_label="السنة",
    )
    scope = django_filters.ModelChoiceFilter(
        queryset=apps.get_model('microsys', 'Scope').objects.all(),
        field_name='user__profile__scope', # Updated lookup
        label="النطاق",
        empty_label="الكل",
        required=False
    )
    class Meta:
        model = apps.get_model('microsys', 'UserActivityLog')
        fields = {
            'timestamp': ['gte', 'lte'],
        }
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        years = self.Meta.model.objects.dates('timestamp', 'year').distinct()
        self.filters['year'].extra['choices'] = [(year.year, year.year) for year in years]
        self.filters['year'].field.widget.attrs.update({
            'class': 'auto-submit-filter'
        })
        self.filters['scope'].field.widget.attrs.update({
            'class': 'auto-submit-filter'
        })

        if self.request and hasattr(self.request.user, 'profile') and self.request.user.profile.scope:
            del self.filters['scope']
        
        self.form.helper = FormHelper()
        self.form.helper.form_method = 'GET'
        self.form.helper.form_class = 'form-inline'
        self.form.helper.form_show_labels = False
        
        self.form.helper.layout = Layout()
        if 'sort' in self.data:
            self.form.helper.layout.append(Hidden('sort', self.data['sort']))
            
        row_fields = [
            Column(Field('keyword', placeholder="البحث"), css_class='form-group col-auto flex-fill'),
        ]
        if is_scope_enabled():
            # Check profile for scope
            if not (self.request and hasattr(self.request.user, 'profile') and self.request.user.profile.scope):
                row_fields.append(Column(Field('scope', placeholder="النطاق", dir="rtl"), css_class='form-group col-auto'))

        clear_url = '{% url "user_activity_log" %}'
        query_params = []
        if 'sort' in self.data:
            clear_url += f"?sort={self.data['sort']}"
        if query_params:
            clear_url += "?" + "&".join(query_params)
        ignore_params = ['sort', 'page']
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
        
        row_fields.extend([
            Column(Field('year', placeholder="السنة", dir="rtl"), css_class='form-group col-auto'),
            Column(
                Row(
                    Column(Field('timestamp__gte', css_class='flatpickr', placeholder="من "), css_class='col-6'),
                    Column(Field('timestamp__lte', css_class='flatpickr', placeholder="إلى "), css_class='col-6'),
                ), 
                css_class='col-auto flex-fill'
            ),
            *buttons_html,
        ])

        self.form.helper.layout.append(Row(*row_fields, css_class='form-row'))
    def filter_keyword(self, queryset, name, value):
        return queryset.filter(
            Q(user__username__icontains=value) |
            Q(user__email__icontains=value) |
            Q(user__profile__phone__icontains=value) | # Updated lookup
            Q(action__icontains=value) |
            Q(model_name__icontains=value) |
            Q(number__icontains=value) |
            Q(ip_address__icontains=value)
        )
