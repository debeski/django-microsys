# Imports of the required python modules and libraries
######################################################
import django_filters
from django.contrib.auth import get_user_model
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Row, Column, Field, HTML, Hidden
from django.db.models import Q
from django.apps import apps  # Import apps
from users.utils import is_scope_enabled
User = get_user_model()  # Use custom user model

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
        # Prepare clear button URL with sort parameter if exists
        clear_url = '{% url "manage_users" %}'
        if 'sort' in self.data:
            clear_url += f"?sort={self.data['sort']}"

        self.form.helper.layout.append(
            Row(
                Column(Field('keyword', placeholder="البحث"), css_class='form-group col-auto flex-fill'),
                Column(HTML('<button type="submit" class="btn btn-secondary w-100"><i class="bi bi-search bi-font text-light me-2"></i>بحـــث</button>'), css_class='col-auto text-center'),
                Column(HTML(f'{{% if request.GET and request.GET.keys|length > 1 %}} <a href="{clear_url}" class="btn btn-warning bi-font">clear</a> {{% endif %}}'), css_class='form-group col-auto text-center'),
                css_class='form-row'
            ),
        )
    def filter_keyword(self, queryset, name, value):
        """
        Filter the queryset by matching the keyword in username, email, phone, and occupation.
        """
        return queryset.filter(
            Q(username__icontains=value) |
            Q(email__icontains=value) |
            Q(phone__icontains=value) |
            Q(scope__name__icontains=value) |
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
        queryset=apps.get_model('users', 'Scope').objects.all(),
        field_name='user__scope',
        label="النطاق",
        empty_label="الكل",
        required=False
    )
    class Meta:
        model = apps.get_model('users', 'UserActivityLog')
        fields = {
            'timestamp': ['gte', 'lte'],
        }
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Fetch distinct years dynamically
        years = self.Meta.model.objects.dates('timestamp', 'year').distinct()
        self.filters['year'].extra['choices'] = [(year.year, year.year) for year in years]
        self.filters['year'].field.widget.attrs.update({
            'onchange': 'this.form.submit();'
        })
        self.filters['scope'].field.widget.attrs.update({
            'onchange': 'this.form.submit();'
        })

        if self.request and self.request.user.scope:
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
            if not (self.request and self.request.user.scope):
                row_fields.append(Column(Field('scope', placeholder="النطاق", dir="rtl"), css_class='form-group col-auto'))

        # Prepare clear button URL with sort parameter if exists
        clear_url = '{% url "user_activity_log" %}'
        if 'sort' in self.data:
            clear_url += f"?sort={self.data['sort']}"

        row_fields.extend([
            Column(Field('year', placeholder="السنة", dir="rtl"), css_class='form-group col-auto'),
            Column(
                Row(
                    Column(Field('timestamp__gte', css_class='flatpickr', placeholder="من "), css_class='col-6'),
                    Column(Field('timestamp__lte', css_class='flatpickr', placeholder="إلى "), css_class='col-6'),
                ), 
                css_class='col-auto flex-fill'
            ),
            Column(HTML('<button type="submit" class="btn btn-secondary w-100"><i class="bi bi-search bi-font text-light me-2"></i>بحـــث</button>'), css_class='col-auto text-center'),
            Column(HTML(f'{{% if request.GET and request.GET.keys|length > 1 %}} <a href="{clear_url}" class="btn btn-warning bi-font">clear</a> {{% endif %}}'), css_class='form-group col-auto text-center'),
        ])

        self.form.helper.layout.append(Row(*row_fields, css_class='form-row'))
    def filter_keyword(self, queryset, name, value):
        """
        Filter the queryset by matching the keyword in username, email, phone, and occupation.
        """
        return queryset.filter(
            Q(user__username__icontains=value) |
            Q(user__email__icontains=value) |
            Q(user__phone__icontains=value) |
            Q(action__icontains=value) |
            Q(model_name__icontains=value) |
            Q(number__icontains=value) |
            Q(ip_address__icontains=value)
        )

