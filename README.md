# Micro Users - Arabic Django User Management App

[![PyPI version](https://badge.fury.io/py/micro-users.svg)](https://pypi.org/project/micro-users/)

<p align="center">
  <img src="https://raw.githubusercontent.com/debeski/micro-users/main/users/static/img/login_logo.webp" alt="Micro Users Login Logo" width="450"/>
</p>

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
- Scope Management System (Optional)
- Custom Grouped User permissions system
- Automatic Activity logging (login/logout, CRUD for all models)
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

2. Add Middleware in `settings.py` (Required for logging):
```python
MIDDLEWARE = [
    # ...
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    # ...
    'users.middleware.ActivityLogMiddleware',  # Add this line
]
```

3. Set custom user model in `settings.py`:
```python
AUTH_USER_MODEL = 'users.CustomUser'
```

4. Include URLs in your main project folder `urls.py`:
```python
urlpatterns = [
    ...
    path('manage/', include('users.urls')),
]
```

5. Run migrations:
```bash
python manage.py migrate users
```

## How to Use

Once configured, the app automatically handles user management and activity logging. Ensure your project has a `base.html` template in the root templates directory, as all user management templates extend it.

### Activity Logging

The app provides a fully **automated** activity logging system. No manual configuration is required in your views.

- **Login/Logout**: Automatically tracked.
- **Create/Update/Delete**: Any change to any model in your app (including `Scope` and `User`) is automatically logged via Django Signals.
- **Log content**: Tracks the user, action type, model name, object ID, and timestamp.
    - *Note*: `last_login` field updates are automatically filtered out to prevent redundant "Update" logs on login.

To view logs, navigate to `manage/logs/` or use the Django Admin interface ("حركات السجل").

## Available URLs

All user management URLs are prefixed with `manage/` as configured above. Below is the complete list:

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
| `manage/scopes/manage/` | `views.manage_scopes` | Scope Manager (Modal) |

## Structure
```
users/
├── views.py        # CRUD operations
├── urls.py         # URL routing
├── tables.py       # User and Activity Log tables
├── signals.py      # Logging signals
├── middleware.py   # Request capture for signals
├── models.py       # User model, permissions, activity logs
├── forms.py        # Creation, edit,. etc.
├── filter.py       # Search filters
├── apps.py         # Permissions Localization
├── admin.py        # Admin UI integration
├── __init__.py     # Python init
├── templates/      # HTML templates (includes partials)
├── static/         # CSS classes
└── migrations/     # Database migrations
```

## Customization

### Replacing Login Logo
To replace the default login logo, simply place your own `login_logo.webp` image in your project's static directory at `static/img/login_logo.webp`.

### Theme Configuration
You can configure the login page colors by defining `MICRO_USERS_THEME` in your project's `settings.py`. This dictionary overrides the default CSS variables.

```python
MICRO_USERS_THEME = {
    'right_bg': '#474745',
    'left_bg': 'white',
    'selection_bg': '#dbdbdb',
    'gradient_start': '#a2a2a7',
    'gradient_end': '#474745',
    # Additional keys supported:
    # 'selection_moz_bg', 'left_shadow', 'right_shadow', 'right_text',
    # 'label_color', 'input_text', 'submit_color', 'submit_focus', 'submit_active'
}
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
| v1.5.0   | • Department Management (Modal-based CRUD)<br> • Department field implementation<br> • Template refactoring (partials/, profile/, users/ for logs)<br> • Verbose names for models |
| v1.6.0   | • **Automated Activity Logging**: dynamic logging for all CREATE/UPDATE/DELETE actions via Middleware & Signals<br> • **Refactor**: Renamed `Department` model to `Scope` (Scope Management)<br> • Removed manual logging requirement<br> • **Architecture**: Decoupled models, forms, and tables using dynamic imports and `apps.get_model` <br> • **Soft Delete**: Users are now marked as inactive with a timestamp instead of being permanently deleted<br> • **Activity Log**: Deleted users appear with a strikethrough<br> • **CSS Refactor**: Extracted and cleaned up styling with CSS variables<br> • **Login**: Refactored login page with separated JS/CSS and a new modern default logo |
| v1.6.1   | • **Theme Configuration**: Added `MICRO_USERS_THEME` setting for easy color customization <br> • **Bug Fixes**: Explicitly excluded unwanted columns (id, ip_address, user_agent) from Activity Log table <br> • **UI**: Improved Scope Manager button visibility |
| v1.6.2   | • **UI**: Improved some tooltips for buttons and descriptions |
| v1.6.3   | • **Bug Fixes**: Fixed a crash with table tooltips "disabled" |
| v1.7.0   | • **New Theme**: Complete visual overhaul with modern, consistent styling <br> • **Refactor**: Updated Login, Profile, and Detail templates for better UX <br> • **Feature**: Added Scope filter to Activity Logs (superuser only) <br> • **UX**: Clear button in filters now preserves current sort order |
| v1.7.1   | • **Bug Fixes**: Fixed login/next url was not being passed correctly |
| v1.8.0   | • **Permissions UI**: Complete redesign with App/Model-based grouping and hierarchical checkboxes<br>• **Aesthetics**: Applied modern glassmorphism theme to permission cards with interactive toggles<br>• **Security**: Implemented 3-level security logic (GM, SM, User) and "invisible" Superuser protection<br>• **Foolproofing**: Added self-editing protection for staff and scope enforcement for managers<br>• **Localization**: Fully translated system auth labels and metadata to Arabic |
| v1.8.1   | • **UI Refinement**: Swapped `Email` and `Phone` positions across all forms, tables, and detail views<br>• **Field Logic**: Set `Email` and `Phone` as optional (not required) for all users<br>• **Security**: Added `manage_staff` custom permission to restrict `is_staff` management to authorized managers only<br>• **Bug Fix**: Reserved `manage_staff` assignment power strictly for Superusers and fixed UI grouping for custom permissions |