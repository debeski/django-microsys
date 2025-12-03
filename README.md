# Micro Users - Django User Management App

[![PyPI version](https://badge.fury.io/py/micro-users.svg)](https://pypi.org/project/micro-users/)

A lightweight, reusable Django app providing user management with abstract user, permissions, localization, and activity logging.

## Features
- Custom AbstractUser model
- User permissions system  
- Activity logging (login/logout tracking)
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
    ...
    'django_tables2',
    'django_filters', 
    'crispy_forms',
    'users',  # Add this
]
```

2. Set custom user model in settings.py:
```python
AUTH_USER_MODEL = 'users.User'
```

3. Include URLs in your main project folder `urls.py`:
```python
urlpatterns = [
    ...
    path('users/', include('users.urls')),
]
```

4. make migrations and migrate:
```bash
python manage.py makemigrations users
python manage.py migrate users
```

## Requirements
- Python 3.9+
- Django 5.1+
- See setup.py for full dependencies

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
```

## **Directory structure:**
```
micro-users/
├── users/          # This is the actual package name
│   ├── __init__.py
│   ├── models.py
│   ├── views.py
│   ├── urls.py
│   ├── admin.py
│   └── templates/
├── setup.py
└── README.md
```
