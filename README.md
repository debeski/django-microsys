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
- User permissions system  
- Activity logging (login/logout, CRUD tracking)
- Localization support
- Admin interface integration
- CRUD views and templates
- Filtering and tabulation

## Installation

```bash
pip install git+https://github.com/debeski/micro-users.git
# OR local
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


## Structure
```
users/
├── models.py      # User model, permissions, activity logs
├── views.py       # CRUD operations
├── urls.py        # URL routing
├── admin.py       # Admin integration
├── templates/     # HTML templates
└── migrations/    # Database migrations
```

## Version History

| Version  | Changes |
|----------|---------|
| v1.0.0   | Initial release as pip package |
| v1.0.1   | Fixed a couple of new issues as a pip package |
| v1.0.2   | Fixed the readme and building files |
| v1.0.3   | Still getting the hang of this pip publish thing |
| v1.0.4   | Honestly still messing with and trying settings and stuff out |
| v1.1.0   | OK, finally a working seamless micro-users app |
| v1.1.1   | Fixed a bug where a staff member can edit the admin details |
| v1.2.0   | Added User Details view with specific user activity log |
| v1.2.1   | Fixed a minot import bug |