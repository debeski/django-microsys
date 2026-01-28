import django_tables2 as tables
from django.contrib.auth import get_user_model
from django.apps import apps

User = get_user_model()  # Use custom user model

class UserTable(tables.Table):
    username = tables.Column(verbose_name="اسم المستخدم")
    phone = tables.Column(verbose_name="رقم الهاتف")
    email = tables.Column(verbose_name="البريد الالكتروني")
    scope = tables.Column(verbose_name="النطاق", accessor='scope.name', default='-')
    full_name = tables.Column(
        verbose_name="الاسم الكامل",
        accessor='user.full_name',
        order_by='user__first_name'
    )
    is_staff = tables.BooleanColumn(verbose_name="مسؤول")
    is_active = tables.BooleanColumn(verbose_name="نشط")
    last_login = tables.DateColumn(
        format="H:i Y-m-d ",  # This is the format you want for the timestamp
        verbose_name="اخر دخول"
    )
    # Action buttons for edit and delete (summoned column)
    actions = tables.TemplateColumn(
        template_name='users/partials/user_actions.html',
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
        format="H:i Y-m-d ",  # This is the format you want for the timestamp
        verbose_name="وقت العملية"
    )
    full_name = tables.Column(
        verbose_name="الاسم الكامل",
        accessor='user.full_name',
        order_by='user__first_name'
    )
    scope = tables.Column(
        verbose_name="النطاق",
        accessor='user.scope.name',
        default='عام'
    )
    class Meta:
        model = apps.get_model('users', 'UserActivityLog')
        template_name = "django_tables2/bootstrap5.html"
        fields = ("timestamp", "user", "full_name", "model_name", "action", "object_id", "number", "scope")
        exclude = ("id", "ip_address", "user_agent")
        attrs = {'class': 'table table-hover align-middle'}
        row_attrs = {
            "class": lambda record: "row-deleted" if record.user and getattr(record.user, "deleted_at", None) else ""
        }

class UserActivityLogTableNoUser(UserActivityLogTable):
    class Meta(UserActivityLogTable.Meta):
        # Remove the 'user', 'user.full_name' and 'scope' columns
        exclude = ("user", "user.full_name", "scope")

class ScopeTable(tables.Table):
    actions = tables.TemplateColumn(
        template_name='users/partials/scope_actions.html',
        orderable=False,
        verbose_name=''
    )
    class Meta:
        model = apps.get_model('users', 'Scope')
        template_name = "django_tables2/bootstrap5.html"
        fields = ("name", "actions")
        attrs = {'class': 'table table-hover align-middle'}

