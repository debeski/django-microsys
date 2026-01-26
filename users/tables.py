import django_tables2 as tables
from django.contrib.auth import get_user_model
from .models import UserActivityLog, Department

User = get_user_model()  # Use custom user model

class UserTable(tables.Table):
    username = tables.Column(verbose_name="اسم المستخدم")
    email = tables.Column(verbose_name="البريد الالكتروني")
    department = tables.Column(verbose_name="القسم", accessor='department.name', default='-')
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
        verbose_name=''
    )
    class Meta:
        model = User
        template_name = "django_tables2/bootstrap5.html"
        fields = ("username", "email", "full_name", "phone", "department", "is_staff", "is_active","last_login", "actions")
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
    department = tables.Column(
        verbose_name="القسم",
        accessor='user.department.name',
        default='عام'
    )
    class Meta:
        model = UserActivityLog
        template_name = "django_tables2/bootstrap5.html"
        fields = ("timestamp", "user", "full_name", "department", "action", "model_name", "object_id", "number")
        attrs = {'class': 'table table-hover align-middle'}

class UserActivityLogTableNoUser(UserActivityLogTable):
    class Meta(UserActivityLogTable.Meta):
        # Remove the 'user', 'user.full_name' and 'department' columns
        exclude = ("user", "user.full_name", "department")

class DepartmentTable(tables.Table):
    actions = tables.TemplateColumn(
        template_name='users/partials/department_actions.html',
        orderable=False,
        verbose_name=''
    )
    class Meta:
        model = Department
        template_name = "django_tables2/bootstrap5.html"
        fields = ("name", "actions")
        attrs = {'class': 'table table-hover align-middle'}

