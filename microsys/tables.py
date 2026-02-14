import django_tables2 as tables
from django.contrib.auth import get_user_model
from django.apps import apps
from django.utils.safestring import mark_safe
from .translations import get_strings
from .utils import filter_context_actions
from django.conf import settings

User = get_user_model()


def _get_default_strings():
    """Get translation strings using the project default language."""
    ms_config = getattr(settings, 'MICROSYS_CONFIG', {})
    lang = ms_config.get('default_language', 'ar')
    overrides = ms_config.get('translations', None)
    return get_strings(lang, overrides=overrides)


from django.urls import reverse
import json

class UserTable(tables.Table):
    username = tables.Column(verbose_name="اسم المستخدم")
    phone = tables.Column(verbose_name="رقم الهاتف", accessor='profile.phone', default='-')
    email = tables.Column(verbose_name="البريد الالكتروني")
    scope = tables.Column(verbose_name="النطاق", accessor='profile.scope.name', default='-')
    full_name = tables.Column(
        verbose_name="الاسم الكامل",
        accessor='profile.full_name', # Assuming profile has full_name property, or use user.get_full_name
        order_by='first_name'
    )
    is_staff = tables.BooleanColumn(verbose_name="مسؤول")
    is_active = tables.BooleanColumn(verbose_name="نشط")
    last_login = tables.DateColumn(
        format="H:i Y-m-d ",
        verbose_name="اخر دخول"
    )
    # actions = tables.TemplateColumn(
    #     template_name='microsys/users/user_actions.html',
    #     orderable=False,
    #     verbose_name='',
    # )

    def __init__(self, *args, translations=None, request=None, **kwargs):
        super().__init__(*args, **kwargs)
        s = translations or _get_default_strings()
        self.request = request
        self.columns['username'].column.verbose_name = s.get('tbl_username', 'اسم المستخدم')
        self.columns['phone'].column.verbose_name = s.get('tbl_phone', 'رقم الهاتف')
        self.columns['email'].column.verbose_name = s.get('tbl_email', 'البريد الالكتروني')
        self.columns['scope'].column.verbose_name = s.get('tbl_scope', 'النطاق')
        self.columns['full_name'].column.verbose_name = s.get('tbl_full_name', 'الاسم الكامل')
        self.columns['is_staff'].column.verbose_name = s.get('tbl_is_staff', 'مسؤول')
        self.columns['is_active'].column.verbose_name = s.get('tbl_is_active', 'نشط')
        self.columns['last_login'].column.verbose_name = s.get('tbl_last_login', 'اخر دخول')
        
        # Context Menu Helper
        def get_user_actions(record):
            actions = [
                {
                    "label": s.get('view_label', 'عرض'),
                    "icon": "bi bi-eye",
                    "url": reverse('user_detail', args=[record.pk]),
                    "type": "url",
                    "dblclick": True 
                },
                {"type": "divider"},
                {
                    "label": s.get('edit_label', 'تعديل'),
                    "icon": "bi bi-pencil",
                    "url": reverse('edit_user', args=[record.pk]),
                    "type": "url"
                },
                {
                    "label": s.get('reset_password', 'إعادة تعيين كلمة المرور'),
                    "icon": "bi bi-key",
                    "type": "event",
                    "event": "micro:reset-password",
                    "data": {
                        "id": record.pk, 
                        "username": record.username,
                        "url": reverse('reset_password', args=[record.pk])
                    }
                }
            ]
            
            # Only allow delete for non-superusers
            if not record.is_superuser:
                actions.append({"type": "divider"})
                actions.append({
                    "label": s.get('delete_label', 'حذف'),
                    "icon": "bi bi-trash",
                    "textClass": "text-danger",
                    "type": "event",
                    "event": "micro:soft-delete",
                    "data": {
                        "id": record.pk,
                        "name": getattr(record, 'full_name', record.username) or record.username,
                        "url": reverse('delete_user', args=[record.pk])
                    }
                })
            
            # Filter actions based on permissions
            if self.request and self.request.user:
                actions = filter_context_actions(self.request.user, actions)

            return json.dumps(actions)

        # Inject context menu attributes
        self.row_attrs.update({
            "data-micro-context": "true",
            "data-micro-actions": get_user_actions
        })

    class Meta:
        model = User
        template_name = "django_tables2/bootstrap5.html"
        fields = ("username", "phone", "email", "full_name", "scope", "is_staff", "is_active","last_login")
        attrs = {'class': 'table table-hover align-middle'}
        # row_attrs is handled in __init__ to allow dynamic behavior

class UserActivityLogTable(tables.Table):
    timestamp = tables.DateColumn(
        format="H:i Y-m-d ",
        verbose_name="وقت العملية"
    )
    full_name = tables.Column(
        verbose_name="الاسم الكامل",
        accessor='user.profile.full_name', # Updated accessor
        order_by='user__first_name'
    )
    scope = tables.Column(
        verbose_name="النطاق",
        accessor='user.profile.scope.name', # Updated accessor
        default='عام'
    )
    # Explicitly declare to prevent django-tables2 from using get_FOO_display()
    action = tables.Column(verbose_name="الإجراء")
    model_name = tables.Column(verbose_name="النموذج")

    def __init__(self, *args, translations=None, **kwargs):
        super().__init__(*args, **kwargs)
        s = translations or _get_default_strings()
        self.columns['timestamp'].column.verbose_name = s.get('tbl_timestamp', 'وقت العملية')
        if 'full_name' in self.columns:
            self.columns['full_name'].column.verbose_name = s.get('tbl_full_name', 'الاسم الكامل')
        if 'scope' in self.columns:
            self.columns['scope'].column.verbose_name = s.get('tbl_scope', 'النطاق')
        # Also translate auto-generated model field headers
        if 'user' in self.columns:
            self.columns['user'].column.verbose_name = s.get('tbl_username', 'اسم المستخدم')
        if 'model_name' in self.columns:
            self.columns['model_name'].column.verbose_name = s.get('tbl_model_name', 'النموذج')
        if 'action' in self.columns:
            self.columns['action'].column.verbose_name = s.get('tbl_action', 'الإجراء')
        if 'object_id' in self.columns:
            self.columns['object_id'].column.verbose_name = s.get('tbl_object_id', 'رقم العنصر')
        if 'number' in self.columns:
            self.columns['number'].column.verbose_name = s.get('tbl_number', 'الرقم')
        
        # Store translations for render methods
        self.translations = s

    def render_action(self, value, record):
        """Translate action type dynamically."""
        # Use raw value from record to ensure we get 'LOGIN' not translated text
        raw_value = record.action
        if not raw_value:
            return "-"
        return self.translations.get(f"action_{raw_value.lower()}", raw_value)

    def render_model_name(self, value):
        """Translate model name dynamically."""
        if not value:
            return "-"
        
        # Try exact match first (e.g. 'auth.User')
        # Then try just model name (e.g. 'user')
        keys_to_try = [
            f"model_{value.lower().replace('.', '_')}", 
            f"model_{value.split('.')[-1].lower()}"
        ]
        
        for key in keys_to_try:
            if key in self.translations:
                return self.translations[key]
        
        return value

    class Meta:
        model = apps.get_model('microsys', 'UserActivityLog')
        template_name = "django_tables2/bootstrap5.html"
        fields = ("timestamp", "user", "full_name", "model_name", "action", "object_id", "number", "scope")
        exclude = ("id", "ip_address", "user_agent")
        attrs = {'class': 'table table-hover align-middle'}
        row_attrs = {
            # Check for deleted_at on the profile
            "class": lambda record: "row-deleted" if record.user and hasattr(record.user, 'profile') and record.user.profile.deleted_at else ""
        }

class UserActivityLogTableNoUser(UserActivityLogTable):
    class Meta(UserActivityLogTable.Meta):
        exclude = ("user", "user.full_name", "scope")

class ScopeTable(tables.Table):
    actions = tables.TemplateColumn(
        template_name='microsys/scopes/scope_actions.html',
        orderable=False,
        verbose_name=''
    )
    class Meta:
        model = apps.get_model('microsys', 'Scope')
        template_name = "django_tables2/bootstrap5.html"
        fields = ("name", "actions")
        attrs = {'class': 'table table-hover align-middle'}
