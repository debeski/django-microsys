# Imports of the required python modules and libraries
######################################################
from django import forms
from django.contrib.auth.models import Permission as Permissions
from django.contrib.auth.forms import UserCreationForm, UserChangeForm, PasswordChangeForm, SetPasswordForm
from django.contrib.auth import get_user_model
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Field, Div, HTML, Submit
from crispy_forms.bootstrap import FormActions
from PIL import Image
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from django.db.models import Q


from django.forms.widgets import ChoiceWidget
from .models import Department

User = get_user_model()

class GroupedPermissionWidget(ChoiceWidget):
    template_name = 'users/widgets/grouped_permissions.html'
    allow_multiple_selected = True

    def value_from_datadict(self, data, files, name):
        if hasattr(data, 'getlist'):
            return data.getlist(name)
        return data.get(name)

    def get_context(self, name, value, attrs):
        from django.apps import apps
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
            
            # Fetch verbose app name
            try:
                app_config = apps.get_app_config(app_label)
                app_verbose_name = app_config.verbose_name
            except LookupError:
                app_verbose_name = app_label.title()

            # Determine action
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
                'label': str(perm), # Force string conversion to use custom __str__ method
                'selected': str(perm.pk) in str_values,
                'attrs': {
                    'id': f"{current_id}_{perm.pk}",
                    'data_action': action  # Critical for JS global select
                }
            }
            
            if app_label not in grouped_perms:
                grouped_perms[app_label] = {
                    'name': app_verbose_name,
                    'actions': {}
                }
            
            grouped_perms[app_label]['actions'].setdefault(action, []).append(option)
        
        # Sort actions within each app: View -> Add -> Change -> Delete -> Other
        action_order = {'view': 1, 'add': 2, 'change': 3, 'delete': 4, 'other': 5}
        for app_label, app_data in grouped_perms.items():
            app_data['actions'] = dict(sorted(
                app_data['actions'].items(),
                key=lambda item: action_order.get(item[0], 99)
            ))
            
        context['widget']['grouped_perms'] = grouped_perms
        return context

    def render(self, name, value, attrs=None, renderer=None):
        from django.template.loader import render_to_string
        from django.utils.safestring import mark_safe
        
        context = self.get_context(name, value, attrs)
        return mark_safe(render_to_string(self.template_name, context))


# Custom User Creation form layout
class CustomUserCreationForm(UserCreationForm):
    permissions = forms.ModelMultipleChoiceField(
        queryset=Permissions.objects.exclude(
            Q(codename__regex=r'^(delete_)') |
            Q(content_type__app_label__in=[
                'admin',
                'auth',
                'contenttypes',
                'sessions',
                'django_celery_beat',
                'users'
            ])
        ),
        required=False,
        widget=GroupedPermissionWidget,
        label="الصلاحيات"
    )

    class Meta:
        model = User
        fields = ["username", "email", "password1", "password2", "first_name", "last_name", "phone", "department", "is_staff", "permissions", "is_active"]

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        if self.user and not self.user.is_superuser and self.user.department:
            self.fields['department'].initial = self.user.department
            self.fields['department'].disabled = True
        
        self.fields["username"].label = "اسم المستخدم"
        self.fields["email"].label = "البريد الإلكتروني"
        self.fields["first_name"].label = "الاسم"
        self.fields["last_name"].label = "اللقب"
        self.fields["is_staff"].label = "صلاحيات انشاء و تعديل المستخدمين"
        self.fields["password1"].label = "كلمة المرور"
        self.fields["password2"].label = "تأكيد كلمة المرور"
        self.fields["is_active"].label = "تفعيل الحساب"

        # Help Texts
        self.fields["username"].help_text = "اسم المستخدم يجب أن يكون فريدًا، 50 حرفًا أو أقل. فقط حروف، أرقام و @ . + - _"
        self.fields["email"].help_text = "أدخل عنوان البريد الإلكتروني الصحيح"
        self.fields["is_staff"].help_text = "يحدد ما إذا كان بإمكان المستخدم الوصول إلى قسم ادارة المستخدمين."
        self.fields["is_active"].help_text = "يحدد ما إذا كان يجب اعتبار هذا الحساب نشطًا."
        self.fields["password1"].help_text = "كلمة المرور يجب ألا تكون مشابهة لمعلوماتك الشخصية، وأن تحتوي على 8 أحرف على الأقل، وألا تكون شائعة أو رقمية بالكامل.."
        self.fields["password2"].help_text = "أدخل نفس كلمة المرور السابقة للتحقق."

        # Use Crispy Forms Layout helper
        self.helper = FormHelper()
        self.helper.layout = Layout(
            "username",
            "email",
            "password1",
            "password2",
            HTML("<hr>"),
            Div(
                Div(Field("first_name", css_class="col-md-6"), css_class="col-md-6"),
                Div(Field("last_name", css_class="col-md-6"), css_class="col-md-6"),
                css_class="row"
            ),
            Div(
                Div(Field("phone", css_class="col-md-6"), css_class="col-md-6"),
                Div(Field("department", css_class="col-md-6"), css_class="col-md-6"),
                css_class="row"
            ),
            HTML("<hr>"),
            Field("permissions", css_class="col-12"),
            "is_staff",
            "is_active",
            FormActions(
                HTML(
                    """
                    <button type="submit" class="btn btn-success">
                        <i class="bi bi-person-plus-fill text-light me-1 h4"></i>
                        إضافة
                    </button>
                    """
                ),
                HTML(
                    """
                    <a href="{% url 'manage_users' %}" class="btn btn-secondary">
                        <i class="bi bi-arrow-return-left text-light me-1 h4"></i> إلغـــاء
                    </a>
                    """
                )
            )
        )

    def save(self, commit=True):
        user = super().save(commit=False)
        if commit:
            user.save()
            # Manually set permissions
            user.user_permissions.set(self.cleaned_data["permissions"])
        return user


# Custom User Editing form layout
class CustomUserChangeForm(UserChangeForm):
    permissions = forms.ModelMultipleChoiceField(
        queryset=Permissions.objects.exclude(
            Q(codename__regex=r'^(delete_)') |
            Q(content_type__app_label__in=[
                'admin',
                'auth',
                'contenttypes',
                'sessions',
                'django_celery_beat',
                'users'
            ])
        ),
        required=False,
        widget=GroupedPermissionWidget,
        label="الصلاحيات"
    )

    class Meta:
        model = User
        fields = ["username", "email", "first_name", "last_name", "phone", "department", "is_staff",  "permissions", "is_active"]

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        user_instance = kwargs.get('instance')
        super().__init__(*args, **kwargs)

        if self.user and not self.user.is_superuser and self.user.department:
            self.fields['department'].disabled = True
        
        # Labels
        self.fields["username"].label = "اسم المستخدم"
        self.fields["email"].label = "البريد الإلكتروني"
        self.fields["first_name"].label = "الاسم الاول"
        self.fields["last_name"].label = "اللقب"
        self.fields["is_staff"].label = "صلاحيات انشاء و تعديل المستخدمين"
        self.fields["is_active"].label = "الحساب مفعل"
        
        # Help Texts
        self.fields["username"].help_text = "اسم المستخدم يجب أن يكون فريدًا، 50 حرفًا أو أقل. فقط حروف، أرقام و @ . + - _"
        self.fields["email"].help_text = "أدخل عنوان البريد الإلكتروني الصحيح"
        self.fields["is_staff"].help_text = "يحدد ما إذا كان بإمكان المستخدم الوصول إلى قسم ادارة المستخدمين."
        self.fields["is_active"].help_text = "يحدد ما إذا كان يجب اعتبار هذا الحساب نشطًا. قم بإلغاء تحديد هذا الخيار بدلاً من الحذف."
        
        if user_instance:
            self.fields["permissions"].initial = user_instance.user_permissions.all()

        # Use Crispy Forms Layout helper
        self.helper = FormHelper()
        self.helper.form_tag = False
        self.helper.layout = Layout(
            "username",
            "email",
            HTML("<hr>"),
            Div(
                Div(Field("first_name", css_class="col-md-6"), css_class="col-md-6"),
                Div(Field("last_name", css_class="col-md-6"), css_class="col-md-6"),
                css_class="row"
            ),
            Div(
                Div(Field("phone", css_class="col-md-6"), css_class="col-md-6"),
                Div(Field("department", css_class="col-md-6"), css_class="col-md-6"),
                css_class="row"
            ),
            HTML("<hr>"),
            Field("permissions", css_class="col-12"),
            "is_staff",
            "is_active",
            FormActions(
                HTML(
                    """
                    <button type="submit" class="btn btn-success">
                        <i class="bi bi-person-plus-fill text-light me-1 h4"></i>
                        تحديث
                    </button>
                    """
                ),
                HTML(
                    """
                    <a href="{% url 'manage_users' %}" class="btn btn-secondary">
                        <i class="bi bi-arrow-return-left text-light me-1 h4"></i> إلغـــاء
                    </a>
                    """
                ),
                HTML(
                    """
                    <button type="button" class="btn btn-primary" data-bs-toggle="modal" data-bs-target="#resetPasswordModal">
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
            # Manually set permissions
            user.user_permissions.set(self.cleaned_data["permissions"])
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
            Submit('submit', 'تغيير كلمة المرور', css_class='btn btn-primary'),
        )

    def save(self, commit=True):
        user = super().save(commit=False)
        if commit:
            user.save()
        return user


class UserProfileEditForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name', 'phone', 'profile_picture']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].disabled = True  # Prevent the user from changing their username
        self.fields['email'].label = "البريد الالكتروني"  # Prevent the user from changing their email
        self.fields['first_name'].label = "الاسم الاول"
        self.fields['last_name'].label = "اللقب"
        self.fields['phone'].label = "رقم الهاتف"
        self.fields['profile_picture'].label = "الصورة الشخصية"

    def clean_profile_picture(self):
        profile_picture = self.cleaned_data.get('profile_picture')

        # Check if the uploaded file is a valid image
        if profile_picture:
            try:
                img = Image.open(profile_picture)
                img.verify()  # Verify the image is not corrupt
                # Check if the image size is within the limits
                if img.width > 600 or img.height > 600:
                    raise ValidationError("The image must not exceed 600x600 pixels.")
            except Exception as e:
                raise ValidationError("Invalid image file.")
        return profile_picture


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

class DepartmentForm(forms.ModelForm):
    class Meta:
        model = Department
        fields = ['name']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['name'].label = "اسم القسم"
        self.helper = FormHelper()
        self.helper.form_tag = False
        self.helper.layout = Layout(
            Field('name', css_class='col-12'),
        )