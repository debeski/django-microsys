# Imports of the required python modules and libraries
######################################################
from django import forms
from django.contrib.auth.models import Permission as Permissions
from django.contrib.auth.forms import UserCreationForm, UserChangeForm, PasswordChangeForm, SetPasswordForm
from django.contrib.auth import get_user_model
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Field, Div, HTML, Submit, Row
from crispy_forms.bootstrap import FormActions
from PIL import Image
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from django.db.models import Q
from django.apps import apps
from django.forms.widgets import ChoiceWidget

User = get_user_model()

def _attach_is_staff_permission(form, widget_id=None):
    perm_field = form.fields.get('permissions')
    staff_field = form.fields.get('is_staff')
    if not perm_field or not staff_field:
        return
    if not isinstance(perm_field.widget, GroupedPermissionWidget):
        return

    try:
        app_config = apps.get_app_config('microsys')
        app_name = app_config.verbose_name
    except LookupError:
        app_name = 'microsys'

    current_value = False
    if getattr(form, 'instance', None) is not None and getattr(form.instance, 'pk', None):
        current_value = bool(getattr(form.instance, 'is_staff', False))
    elif 'is_staff' in form.initial:
        current_value = bool(form.initial.get('is_staff'))
    else:
        current_value = bool(getattr(staff_field, 'initial', False))

    field_id = widget_id or 'id_permissions'
    option_id = f"{field_id}_is_staff"

    option = {
        'name': 'is_staff',
        'value': 'on',
        'label': staff_field.label or "مسؤول",
        'selected': current_value,
        'help_text': staff_field.help_text,
        'attrs': {
            'id': option_id,
            'data_action': 'other',
            'data_model': 'staff',
            'disabled': bool(getattr(staff_field, 'disabled', False)),
        }
    }

    perm_field.widget.add_extra_group(
        app_label='microsys',
        app_name=app_name,
        model_key='staff_access',
        model_name='صلاحيات الإدارة',
        option=option,
    )

class GroupedPermissionWidget(ChoiceWidget):
    template_name = 'microsys/users/grouped_permissions.html'
    allow_multiple_selected = True

    def add_extra_group(self, app_label, app_name, model_key, model_name, option):
        if not hasattr(self, 'extra_groups') or self.extra_groups is None:
            self.extra_groups = {}
        group = self.extra_groups.setdefault(app_label, {'name': app_name, 'models': {}})
        if app_name and not group.get('name'):
            group['name'] = app_name
        model_group = group['models'].setdefault(model_key, {'name': model_name, 'permissions': []})
        model_group['permissions'].append(option)

    def value_from_datadict(self, data, files, name):
        if hasattr(data, 'getlist'):
            return data.getlist(name)
        return data.get(name)

    def get_context(self, name, value, attrs):
        context = super().get_context(name, value, attrs)
        
        # Get current selected values (as strings/ints)
        if value is None:
            value = []
        str_values = set(str(v) for v in value)
        
        # Access the queryset directly
        qs = None
        if hasattr(self.choices, 'queryset'):
            qs = self.choices.queryset.select_related('content_type').order_by('content_type__app_label', 'codename')
        else:
             choices = list(self.choices)
             choice_ids = [c[0] for c in choices if c[0]]
             qs = Permissions.objects.filter(id__in=choice_ids).select_related('content_type').order_by('content_type__app_label', 'codename')

        grouped_perms = {}
        
        for perm in qs:
            app_label = perm.content_type.app_label
            model_name = perm.content_type.model
            codename = perm.codename

            # --- Mapping manage_staff to auth.Permission UI ---
            # if app_label == 'microsys' and codename == 'manage_staff':
            #     app_label = 'auth'
            #     model_name = 'permission'
            # # --- Mapping manage_sections to auth.Permission UI ---
            # if app_label == 'microsys' and codename == 'manage_sections':
            #     app_label = 'auth'
            #     model_name = 'section'
            # -------------------------------------------------
            # Use real verbose name from model class if available
            if app_label == 'microsys' and model_name == 'profile':
                model_verbose_name = "إدارة المستخدمين"
            # elif app_label == 'auth' and model_name == 'section':
            #     model_verbose_name = "إدارة الأقسام الفرعية"
            # else:
            model_class = perm.content_type.model_class()
            if model_class:
                model_verbose_name = str(model_class._meta.verbose_name)
            else:
                model_verbose_name = perm.content_type.name
            
            # Fetch verbose app name
            try:
                app_config = apps.get_app_config(app_label)
                app_verbose_name = app_config.verbose_name
            except LookupError:
                app_verbose_name = app_label.title()

            action = 'other'
            codename = perm.codename
            if codename.startswith('view_'): action = 'view'
            elif codename.startswith('add_'): action = 'add'
            elif codename.startswith('change_'): action = 'change'
            elif codename.startswith('delete_'): action = 'delete'
            
            # Build option dict
            current_id = attrs.get('id', 'id_permissions') if attrs else 'id_permissions'

            option = {
                'name': name,
                'value': perm.pk,
                'label': str(perm),
                'codename': codename,
                'selected': str(perm.pk) in str_values,
                'attrs': {
                    'id': f"{current_id}_{perm.pk}",
                    'data_action': action,
                    'data_model': model_name
                }
            }
            
            if app_label not in grouped_perms:
                grouped_perms[app_label] = {
                    'name': app_verbose_name,
                    'models': {}
                }
            
            if model_name not in grouped_perms[app_label]['models']:
                grouped_perms[app_label]['models'][model_name] = {
                    'name': model_verbose_name.title(),
                    'permissions': []
                }
            
            grouped_perms[app_label]['models'][model_name]['permissions'].append(option)
        
        action_order = {'view': 1, 'add': 2, 'change': 3, 'delete': 4, 'other': 5}
        for app_label, app_data in grouped_perms.items():
            for model_name, model_data in app_data['models'].items():
                model_data['permissions'].sort(
                    key=lambda x: action_order.get(x['attrs']['data_action'], 99)
                )

        extra_groups = getattr(self, 'extra_groups', None)
        if isinstance(extra_groups, dict):
            for app_label, app_data in extra_groups.items():
                if app_label not in grouped_perms:
                    grouped_perms[app_label] = {
                        'name': app_data.get('name', app_label.title()),
                        'models': {},
                    }

                target_app = grouped_perms[app_label]
                if app_data.get('name'):
                    target_app['name'] = app_data['name']

                for model_name, model_data in app_data.get('models', {}).items():
                    target_model = target_app['models'].setdefault(
                        model_name,
                        {'name': model_data.get('name', model_name), 'permissions': []}
                    )

                    existing_ids = {
                        p.get('attrs', {}).get('id') for p in target_model['permissions']
                    }
                    for option in model_data.get('permissions', []):
                        opt_id = option.get('attrs', {}).get('id')
                        if opt_id and opt_id in existing_ids:
                            continue
                        target_model['permissions'].append(option)
            
        context['widget']['grouped_perms'] = grouped_perms
        return context

    def render(self, name, value, attrs=None, renderer=None):
        from django.template.loader import render_to_string
        from django.utils.safestring import mark_safe
        
        context = self.get_context(name, value, attrs)
        return mark_safe(render_to_string(self.template_name, context))


# Custom User Creation form layout
class CustomUserCreationForm(UserCreationForm):
    # Added fields from Profile
    phone = forms.CharField(max_length=10, required=False, label="رقم الهاتف", help_text="أدخل رقم الهاتف الصحيح بالصيغة الاتية 09XXXXXXXX (اختياري)")
    scope = forms.ModelChoiceField(queryset=None, required=False, label="النطاق")
    
    permissions = forms.ModelMultipleChoiceField(
        queryset=Permissions.objects.exclude(
            Q(codename__regex=r'^(delete_)') |
            Q(content_type__app_label__in=[
                'admin',
                'contenttypes',
                'sessions',
                'django_celery_beat',
            ]) |
            (Q(content_type__app_label='microsys') & ~Q(codename='manage_staff')) |
            Q(content_type__app_label='auth', content_type__model__in=['group', 'user', 'permission'])
        ),
        required=False,
        widget=GroupedPermissionWidget,
        label="الصلاحيات"
    )

    class Meta:
        model = User
        fields = ["username", "password1", "password2", "first_name", "last_name", "email", "is_staff", "is_active"]

    def __init__(self, *args, **kwargs):
        self.user_context = kwargs.pop('user', None) # Renamed to avoid calling it self.user which conflicts with instance in some contexts? No wait, self.user in init usually refers to request.user passed in view
        super().__init__(*args, **kwargs)
        
        Scope = apps.get_model('microsys', 'Scope')
        self.fields['scope'].queryset = Scope.objects.all()

        # Permission check: Non-superusers can only assign permissions they already have
        if self.user_context and not self.user_context.is_superuser:
            user_perms = self.user_context.user_permissions.all() | Permissions.objects.filter(group__user=self.user_context)
            self.fields['permissions'].queryset = self.fields['permissions'].queryset.filter(id__in=user_perms.values_list('id', flat=True))
        
        ScopeSettings = apps.get_model('microsys', 'ScopeSettings')
        if not ScopeSettings.load().is_enabled:
            self.fields['scope'].disabled = True
            self.fields['scope'].widget = forms.HiddenInput()
            self.fields['scope'].required = False
        
        if self.user_context and not self.user_context.is_superuser and hasattr(self.user_context, 'profile') and self.user_context.profile.scope:
            self.fields['scope'].initial = self.user_context.profile.scope
            self.fields['scope'].disabled = True
            # Security Fix: Hide manage_staff
            self.fields['permissions'].queryset = self.fields['permissions'].queryset.exclude(codename='manage_staff')
        
        self.fields["email"].required = False

        # can_manage_staff logic
        if self.user_context and not self.user_context.is_superuser:
            if not self.user_context.has_perm('microsys.manage_staff'):
                self.fields['is_staff'].disabled = True
                self.fields['is_staff'].initial = False
                self.fields['is_staff'].help_text = "ليس لديك صلاحية لتعيين هذا المستخدم كمسؤول."

        self.fields["username"].label = "اسم المستخدم"
        self.fields["email"].label = "البريد الإلكتروني"
        self.fields["first_name"].label = "الاسم"
        self.fields["last_name"].label = "اللقب"
        self.fields["is_staff"].label = "صلاحيات انشاء و تعديل المستخدمين"
        self.fields["password1"].label = "كلمة المرور"
        self.fields["password2"].label = "تأكيد كلمة المرور"
        self.fields["is_active"].label = "تفعيل الحساب"

        # Help Texts
        self.fields["username"].help_text = "اسم المستخدم يجب أن يكون فريدًا، 20 حرفًا أو أقل. فقط حروف، أرقام و @ . + - _"
        self.fields["email"].help_text = "أدخل عنوان البريد الإلكتروني الصحيح (اختياري)"
        self.fields["is_active"].help_text = "يحدد ما إذا كان يجب اعتبار هذا الحساب نشطًا."
        self.fields["password1"].help_text = "كلمة المرور يجب ألا تكون مشابهة لمعلوماتك الشخصية، وأن تحتوي على 8 أحرف على الأقل، وألا تكون شائعة أو رقمية بالكامل.."
        self.fields["password2"].help_text = "أدخل نفس كلمة المرور السابقة للتحقق."

        _attach_is_staff_permission(self, self.fields['permissions'].widget.attrs.get('id'))

        self.helper = FormHelper()
        self.helper.layout = Layout(
            Row(Field("username", css_class="form-control")),            
            Row(Field("password1", css_class="form-control")),
            Row(Field("password2", css_class="form-control")),
            HTML("<hr>"),
            Row(
                Div(Field("first_name", css_class="form-control"), css_class="col-md-6"),
                Div(Field("last_name", css_class="form-control"), css_class="col-md-6"),
                css_class="row"
            ),
            Row(
                Div(Field("phone", css_class="form-control"), css_class="col-md-6"),
                Div(Field("email", css_class="form-control"), css_class="col-md-6"),
                css_class="row"
            ),
            Row(Field("scope", css_class="form-control")),
            HTML("<hr>"),
            Field("permissions", css_class="col-12"),
            "is_active",
            FormActions(
                HTML(
                    """
                    <button type="submit" class="btn btn-success rounded-pill">
                        <i class="bi bi-person-plus-fill text-light me-1 h4"></i>
                        إضافة
                    </button>
                    """
                ),
                HTML(
                    """
                    <a href="{% url 'manage_users' %}" class="btn btn-danger rounded-pill">
                        <i class="bi bi-arrow-return-left text-light me-1 h4"></i> إلغـــاء
                    </a>
                    """
                )
            )
        )

    def save(self, commit=True):
        user = super().save(commit=False)
        # We need to save the user first to get an ID for the OneToOne relationship
        if commit:
            user.save()
            # Manually set permissions
            user.user_permissions.set(self.cleaned_data["permissions"])
            
            # Save Profile fields
            Profile = apps.get_model('microsys', 'Profile')
            # Check if profile already exists (via signal) or create it
            profile, created = Profile.objects.get_or_create(user=user)
            profile.phone = self.cleaned_data.get('phone')
            profile.scope = self.cleaned_data.get('scope')
            profile.save()
            
        return user


# Custom User Editing form layout
class CustomUserChangeForm(UserChangeForm):
    phone = forms.CharField(max_length=10, required=False, label="رقم الهاتف", help_text="أدخل رقم الهاتف الصحيح بالصيغة الاتية 09XXXXXXXX (اختياري)")
    scope = forms.ModelChoiceField(queryset=None, required=False, label="النطاق")

    permissions = forms.ModelMultipleChoiceField(
        queryset=Permissions.objects.exclude(
            Q(codename__regex=r'^(delete_)') |
            Q(content_type__app_label__in=[
                'admin',
                'contenttypes',
                'sessions',
                'django_celery_beat',
            ]) |
            (Q(content_type__app_label='microsys') & ~Q(codename='manage_staff')) |
            Q(content_type__app_label='auth', content_type__model__in=['group', 'user', 'permission'])
        ),
        required=False,
        widget=GroupedPermissionWidget,
        label="الصلاحيات"
    )

    class Meta:
        model = User
        fields = ["username", "first_name", "last_name", "email", "is_staff", "permissions", "is_active"]

    def __init__(self, *args, **kwargs):
        self.user_context = kwargs.pop('user', None)
        user_instance = kwargs.get('instance')
        super().__init__(*args, **kwargs)
        
        Scope = apps.get_model('microsys', 'Scope')
        self.fields['scope'].queryset = Scope.objects.all()

        # Permission check
        if self.user_context and not self.user_context.is_superuser:
            user_perms = self.user_context.user_permissions.all() | Permissions.objects.filter(group__user=self.user_context)
            self.fields['permissions'].queryset = self.fields['permissions'].queryset.filter(id__in=user_perms.values_list('id', flat=True))

        # Initialize Profile Fields
        if user_instance and hasattr(user_instance, 'profile'):
            self.fields['phone'].initial = user_instance.profile.phone
            self.fields['scope'].initial = user_instance.profile.scope

        # Labels
        self.fields["username"].label = "اسم المستخدم"
        self.fields["email"].label = "البريد الإلكتروني"
        self.fields["first_name"].label = "الاسم الاول"
        self.fields["last_name"].label = "اللقب"
        self.fields["is_staff"].label = "صلاحيات انشاء و تعديل المستخدمين"
        self.fields["is_active"].label = "الحساب مفعل"
        
        # Help Texts
        self.fields["username"].help_text = "اسم المستخدم يجب أن يكون فريدًا، 20 حرفًا أو أقل. فقط حروف، أرقام و @ . + - _"
        self.fields["email"].help_text = "أدخل عنوان البريد الإلكتروني الصحيح (اختياري)"
        self.fields["is_active"].help_text = "يحدد ما إذا كان يجب اعتبار هذا الحساب نشطًا. قم بإلغاء تحديد هذا الخيار بدلاً من الحذف."

        if user_instance:
            self.fields["permissions"].initial = user_instance.user_permissions.all()

        ScopeSettings = apps.get_model('microsys', 'ScopeSettings')
        if not ScopeSettings.load().is_enabled:
            self.fields['scope'].disabled = True
            self.fields['scope'].widget = forms.HiddenInput()
            self.fields['scope'].required = False

        # --- Foolproofing & Role-based logic ---
        if self.user_context and not self.user_context.is_superuser:
            # 1. Self-Editing Protection
            if self.user_context == user_instance:
                if self.user_context.is_staff:
                    self.fields['scope'].disabled = True
                    self.fields['is_staff'].disabled = True
                    self.fields['is_active'].disabled = True
                    self.fields['scope'].help_text = "لا يمكنك تغيير نطاقك الخاص لمنع تجريد نفسك من صلاحيات المدير العام."
                    self.fields['permissions'].queryset = self.fields['permissions'].queryset.exclude(codename='manage_staff')
            
            # 2. Scope Manager Restrictions
            elif hasattr(self.user_context, 'profile') and self.user_context.profile.scope:
                self.fields['scope'].disabled = True
                self.fields['scope'].initial = self.user_context.profile.scope
        
        self.fields["email"].required = False

        # --- can_manage_staff logic ---
        if self.user_context and not self.user_context.is_superuser:
            if not self.user_context.has_perm('microsys.manage_staff'):
                self.fields['is_staff'].disabled = True
                self.fields['is_staff'].help_text = "ليس لديك صلاحية لتغيير وضع هذا المستخدم لمسؤول ."

        _attach_is_staff_permission(self, self.fields['permissions'].widget.attrs.get('id'))

        self.helper = FormHelper()
        self.helper.form_tag = False
        self.helper.layout = Layout(
            Row(Field("username", css_class="form-control")),            
            HTML("<hr>"),
            Row(
                Div(Field("first_name", css_class="form-control"), css_class="col-md-6"),
                Div(Field("last_name", css_class="form-control"), css_class="col-md-6"),
                css_class="row"
            ),
            Row(
                Div(Field("phone", css_class="form-control"), css_class="col-md-6"),
                Div(Field("email", css_class="form-control"), css_class="col-md-6"),
                css_class="row"
            ),
            Row(Field("scope", css_class="form-control")),
            HTML("<hr>"),
            Field("permissions", css_class="col-12"),
            "is_active",
            FormActions(
                HTML(
                    """
                    <button type="submit" class="btn btn-success rounded-pill">
                        <i class="bi bi-person-plus-fill text-light me-1 h4"></i>
                        تحديث
                    </button>
                    """
                ),
                HTML(
                    """
                    <a href="{% url 'manage_users' %}" class="btn btn-danger rounded-pill">
                        <i class="bi bi-arrow-return-left text-light me-1 h4"></i> إلغـــاء
                    </a>
                    """
                ),
                HTML(
                    """
                    <button type="button" class="btn btn-warning rounded-pill" data-bs-toggle="modal" data-bs-target="#resetPasswordModal">
                        <i class="bi bi-key-fill text-light me-1 h4"></i> إعادة تعيين كلمة المرور
                    </button>
                    """
                )
            )
        )

    def save(self, commit=True):
        user = super().save(commit=False)
        if commit:
            user.save()
            user.user_permissions.set(self.cleaned_data["permissions"])
            
            # Save Profile fields
            Profile = apps.get_model('microsys', 'Profile')
            profile, created = Profile.objects.get_or_create(user=user)
            profile.phone = self.cleaned_data.get('phone')
            profile.scope = self.cleaned_data.get('scope')
            profile.save()
            
        return user


# Custom User Reset Password form layout
class ResetPasswordForm(SetPasswordForm):
    username = forms.CharField(label="اسم المستخدم", widget=forms.TextInput(attrs={"readonly": "readonly"}))

    def __init__(self, user, *args, **kwargs):
        super().__init__(user, *args, **kwargs)
        self.fields['username'].initial = user.username
        self.helper = FormHelper()
        self.fields["new_password1"].label = "كلمة المرور الجديدة"
        self.fields["new_password2"].label = "تأكيد كلمة المرور"
        self.helper.layout = Layout(
            Div(
                Field('username', css_class='col-md-12'),
                Field('new_password1', css_class='col-md-12'),
                Field('new_password2', css_class='col-md-12'),
                css_class='row'
            ),
            Submit('submit', 'تغيير كلمة المرور', css_class='btn btn-danger rounded-pill'),
        )

    def save(self, commit=True):
        user = super().save(commit=False)
        if commit:
            user.save()
        return user


class UserProfileEditForm(forms.ModelForm):
    # Add fields from profile
    phone = forms.CharField(max_length=15, required=False, label="رقم الهاتف")
    profile_picture = forms.ImageField(required=False, label="الصورة الشخصية")

    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        user_instance = kwargs.get('instance')
        if user_instance and hasattr(user_instance, 'profile'):
            self.fields['phone'].initial = user_instance.profile.phone
            self.fields['profile_picture'].initial = user_instance.profile.profile_picture

        self.fields['username'].disabled = True
        self.fields['first_name'].label = "الاسم الاول"
        self.fields['last_name'].label = "اللقب"
        self.fields['email'].label = "البريد الالكتروني"
        
        self.fields["email"].required = False

    def clean_profile_picture(self):
        profile_picture = self.cleaned_data.get('profile_picture')

        # Check if the uploaded file is a valid image
        if profile_picture:
            try:
                img = Image.open(profile_picture)
                img.verify()
                if img.width > 1200 or img.height > 1200: # Increased limit a bit
                    raise ValidationError("The image must not exceed 1200x1200 pixels.")
            except Exception as e:
                raise ValidationError("Invalid image file.")
        return profile_picture

    def save(self, commit=True):
        user = super().save(commit=False)
        if commit:
            user.save()
            
            Profile = apps.get_model('microsys', 'Profile')
            profile, created = Profile.objects.get_or_create(user=user)
            
            profile.phone = self.cleaned_data.get('phone')
            if self.cleaned_data.get('profile_picture'):
                profile.profile_picture = self.cleaned_data.get('profile_picture')
            profile.save()
            
        return user


class ArabicPasswordChangeForm(PasswordChangeForm):
    old_password = forms.CharField(
        label=_('كلمة المرور القديمة'),
        widget=forms.PasswordInput(attrs={'autocomplete': 'current-password', 'dir': 'rtl'}),
    )
    new_password1 = forms.CharField(
        label=_('كلمة المرور الجديدة'),
        widget=forms.PasswordInput(attrs={'autocomplete': 'new-password', 'dir': 'rtl'}),
    )
    new_password2 = forms.CharField(
        label=_('تأكيد كلمة المرور الجديدة'),
        widget=forms.PasswordInput(attrs={'autocomplete': 'new-password', 'dir': 'rtl'}),
    )

class ScopeForm(forms.ModelForm):
    class Meta:
        model = apps.get_model('microsys', 'Scope')
        fields = ['name']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['name'].label = "اسم النطاق"
        self.helper = FormHelper()
        self.helper.form_tag = False
        self.helper.layout = Layout(
            Field('name', css_class='col-12'),
        )
