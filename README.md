# Micro Users - Arabic Django User Management App

[![PyPI version](https://badge.fury.io/py/micro-users.svg)](https://pypi.org/project/micro-users/)

**Arabic** lightweight, reusable Django app providing user management with abstract user, permissions, localization, and activity logging.

## Requirements
- **Must be installed on a fresh database.**
- Python 3.11+
- Django 5.1+
- django-crispy-forms 2.4+
- django-tables2 2.7+
- django-filter 24.3+
- pillow 11.0+
- babel 2.1+

## Features
- Custom AbstractUser model
- Custom Grouped User permissions system *NEW*
- Activity logging (login/logout, CRUD tracking)
- Specific User detail and log view
- Localization support
- Admin interface integration
- CRUD views and templates
- Filtering and tabulation
> *Future updates are planned to support dynamic language switching between RTL and LTR.*

## Installation

```bash
pip install git+https://github.com/debeski/micro-users.git
# OR
pip install micro-users
```

## Configuration

1. Add to `INSTALLED_APPS`:
```python
INSTALLED_APPS = [
    'users',  # Preferably on top
    'django.contrib.admin',
    'django.contrib.auth',
    ...
]
```

2. Set custom user model in settings.py:
```python
AUTH_USER_MODEL = 'users.CustomUser'
```

3. Include URLs in your main project folder `urls.py`:
```python
urlpatterns = [
    ...
    path('manage/', include('users.urls')),
]
```

4. Run migrations:
```bash
python manage.py migrate users
```

## How to Use

Once configured, the app automatically handles user management and activity logging. Ensure your project has a `base.html` template in the root templates directory, as all user management templates extend it.

### Activity Logging

The app automatically logs **LOGIN** and **LOGOUT** actions. For custom logging of other actions in your application, you can use the following helper functions:

#### Available Helper Functions

1. **Get Client IP** - Extract the user's IP address from request:
```python
from users.signals import get_client_ip

# Usage in views
ip_address = get_client_ip(request)
```

2. **Log User Action** - Create a reusable logging function:
```python
from django.utils import timezone
from users.models import UserActivityLog
from users.signals import get_client_ip

def log_user_action(request, instance, action, model_name):
    """
    Logs a user action to the activity log.
    
    Args:
        request: HttpRequest object
        instance: The model instance being acted upon
        action: Action type (see ACTION_TYPES below)
        model_name: Name of the model/entity (in Arabic or English)
    """
    UserActivityLog.objects.create(
        user=request.user,
        action=action,
        model_name=model_name,
        object_id=instance.pk,
        number=instance.number if hasattr(instance, 'number') else '',
        timestamp=timezone.now(),
        ip_address=get_client_ip(request),
        user_agent=request.META.get("HTTP_USER_AGENT", ""),
    )
```

#### Action Types Available
Use these constants when logging actions:

| Action Constant | Arabic Display | Description |
|-----------------|----------------|-------------|
| `'LOGIN'` | تسجيل دخـول | User login (auto-logged) |
| `'LOGOUT'` | تسجيل خـروج | User logout (auto-logged) |
| `'CREATE'` | انشـاء | Object creation |
| `'UPDATE'` | تعديـل | Object modification |
| `'DELETE'` | حــذف | Object deletion |
| `'VIEW'` | عـرض | Object viewing |
| `'DOWNLOAD'` | تحميل | File download |
| `'CONFIRM'` | تأكيـد | Action confirmation |
| `'REJECT'` | رفــض | Action rejection |
| `'RESET'` | اعادة ضبط | Password/Data reset |

#### Usage Examples

1. **Logging a CREATE action**:
```python
def create_document(request):
    # ... create logic ...
    document = Document.objects.create(...)
    
    # Log the action
    from users.models import UserActivityLog
    from users.signals import get_client_ip
    
    UserActivityLog.objects.create(
        user=request.user,
        action='CREATE',
        model_name='وثيقة',
        object_id=document.pk,
        number=document.number,
        ip_address=get_client_ip(request),
        user_agent=request.META.get("HTTP_USER_AGENT", ""),
    )
```

2. **Using the helper function**:
```python
# Create a helper function in your app
def log_action(request, instance, action, model_name):
    from users.models import UserActivityLog
    from users.signals import get_client_ip
    from django.utils import timezone
    
    UserActivityLog.objects.create(
        user=request.user,
        action=action,
        model_name=model_name,
        object_id=instance.pk,
        number=getattr(instance, 'number', ''),
        timestamp=timezone.now(),
        ip_address=get_client_ip(request),
        user_agent=request.META.get("HTTP_USER_AGENT", ""),
    )

# Usage in views
def update_order(request, order_id):
    order = get_object_or_404(Order, pk=order_id)
    # ... update logic ...
    log_action(request, order, 'UPDATE', 'طلب')
```

3. **Logging without an instance** (for general actions):
```python
def log_general_action(request, action, model_name, description=''):
    from users.models import UserActivityLog
    from users.signals import get_client_ip
    from django.utils import timezone
    
    UserActivityLog.objects.create(
        user=request.user,
        action=action,
        model_name=model_name,
        object_id=None,
        number=description,
        timestamp=timezone.now(),
        ip_address=get_client_ip(request),
        user_agent=request.META.get("HTTP_USER_AGENT", ""),
    )

# Usage
log_general_action(request, 'CONFIRM', 'نظام', 'تم تأكيد الإعدادات')
```

## Available URLs

All user management URLs are prefixed with `manage/` as configured. Below is the complete list:

| URL Pattern | View/Function | Description |
|-------------|---------------|-------------|
| `manage/login/` | `auth_views.LoginView.as_view()` | User login |
| `manage/logout/` | `auth_views.LogoutView.as_view()` | User logout |
| `manage/users/` | `views.UserListView.as_view()` | List all users |
| `manage/users/create/` | `views.create_user` | Create new user |
| `manage/users/edit/<int:pk>/` | `views.edit_user` | Edit existing user |
| `manage/users/delete/<int:pk>/` | `views.delete_user` | Delete user |
| `manage/users/<int:pk>/` | `views.UserDetailView.as_view()` | View user details |
| `manage/profile` | `views.user_profile` | View current user profile |
| `manage/profile/edit/` | `views.edit_profile` | Edit current profile |
| `manage/logs/` | `views.UserActivityLogView.as_view()` | View activity logs |
| `manage/reset_password/<int:pk>/` | `views.reset_password` | Reset user password |

## Structure
```
users/
├── views.py        # CRUD operations
├── urls.py         # URL routing
├── tables.py       # User and Activity Log tables
├── signals.py      # Logging signals
├── models.py       # User model, permissions, activity logs
├── forms.py        # Creation, edit,. etc.
├── filter.py       # Search filters
├── apps.py         # Permissions Localization
├── admin.py        # Admin UI integration
├── __init__.py     # Python init
├── templates/      # HTML templates
├── static/         # CSS classes
└── migrations/     # Database migrations
```

## Version History

| Version  | Changes |
|----------|---------|
| v1.0.0   | • Initial release as pip package |
| v1.0.1   | • Fixed a couple of new issues as a pip package |
| v1.0.2   | • Fixed the readme and building files |
| v1.0.3   | • Still getting the hang of this pip publish thing |
| v1.0.4   | • Honestly still messing with and trying settings and stuff out |
| v1.1.0   | • OK, finally a working seamless micro-users app |
| v1.1.1   | • Fixed an expolit where a staff member could disable the ADMIN user |
| v1.2.0   | • Added User Details view with specific user activity log |
| v1.2.1   | • Fixed a minor import bug |
| v1.2.2   | • Separated user detail view from table for consistency<br> • Optimized the new detail + log view for optimal compatibiliyy with users |
| v1.2.3   | • Fixed a couple of visual inconsistencies |
| v1.3.0   | • Patched a critical security permission issue<br> • Disabled ADMIN from being viewed/edited from all other members<br> • Fixed a crash when sorting with full_name<br> • Enabled Logging for all actions |
| v1.3.1   | • Corrected a misplaced code that caused a crash when editing profile |
| v1.3.2   | • Minor table modifications |
| v1.4.0   | • Redesigned Permissions UI (Grouped by App/Action) <br> • Added Global Bulk Permission Selectors <br> • Improved Arabic Localization for Permissions <br> • Optimized printing (hidden forms/buttons) <br> • Fixed various bugs and crashes |
| v1.4.1   | • Changed "Administrative User" translation to "Responsible User" (مستخدم مسؤول) <br> • Enforced custom sorting order for Permissions (View -> Add -> Change -> Other) |