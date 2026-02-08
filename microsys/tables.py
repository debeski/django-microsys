import django_tables2 as tables
from django.contrib.auth import get_user_model
from django.apps import apps
from django.utils.safestring import mark_safe

User = get_user_model()

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
    actions = tables.TemplateColumn(
        template_name='microsys/users/user_actions.html',
        orderable=False,
        verbose_name='',
    )
    class Meta:
        model = User
        template_name = "django_tables2/bootstrap5.html"
        fields = ("username", "phone", "email", "full_name", "scope", "is_staff", "is_active","last_login", "actions")
        attrs = {'class': 'table table-hover align-middle'}

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
