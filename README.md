# MicroSys - Arabic Django System Integration Services

[![PyPI version](https://badge.fury.io/py/django-microsys.svg)](https://pypi.org/project/django-microsys/)

<p align="center">
  <img src="https://raw.githubusercontent.com/debeski/microsys/static/img/login_logo.webp" alt="MicroSys Login Logo" width="450"/>
</p>

**Arabic** lightweight, reusable Django app providing comprehensive system integration services, including user management, profile extension, permissions, localization, dynamic sidebar, and automated activity logging.

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
- **System Integration**: Centralized management for users and system scopes.
- **Profile Extension**: Automatically links a `Profile` to your existing User model.
- **Scope Management**: Optional, dynamic scope isolation system with abstract `ScopedModel`.
- **Dynamic Sidebar**: Auto-discovery of list views and customizable menu items.
- **Permissions**: Custom grouped permission UI (App/Model/Action).
- **Automated Logging**: Full activity tracking (CRUD, Login/Logout) via Signals.
- **Localization**: Native Arabic support for all interfaces.
- **Theming & Accessibility**: Built-in dark/light modes and accessibility tools (High Contrast, Zoom, etc.).
- **Security**: CSP compliance, role-based access control (RBAC).

## Installation

```bash
pip install git+https://github.com/debeski/microsys.git
# OR
pip install django-microsys
```

## Quick Start & Configuration

1. **Add to `INSTALLED_APPS`:**
   ```python
   INSTALLED_APPS = [
       'microsys',  # Preferably on top
       'django.contrib.admin',
       'django.contrib.auth',
       # ... dependencies
       'crispy_forms',
       'crispy_bootstrap5',
       'django_filters',
       'django_tables2',
   ]
   ```

2. **Add Middleware:**
   Required for activity logging and request caching.
   ```python
   MIDDLEWARE = [
       # ...
       'django.contrib.auth.middleware.AuthenticationMiddleware',
       # ...
       'microsys.middleware.ActivityLogMiddleware',
   ]
   ```

3. **Add Context Processor:**
   Unified context processor for branding, sidebar, and scope settings.
   ```python
   TEMPLATES = [
       {
           # ...
           'OPTIONS': {
               'context_processors': [
                   # ...
                   'microsys.context_processors.microsys_context',
               ],
           },
       },
   ]
   ```

4. **Include URLs:**
   Mount at **root** for seamless Django auth integration:
   ```python
   from django.urls import path, include

   urlpatterns = [
       # ...
       path('', include('microsys.urls')),  # Mount at root
   ]
   ```
   
   This provides:
   - `/accounts/login/` and `/accounts/logout/` (Django defaults)
   - `/sys/` for all system management routes

   > ⚠️ **Warning:** If your project already uses `/accounts/` URLs (e.g., `django-allauth`), you'll have conflicts. In that case, mount with a prefix and configure custom auth URLs:
   > ```python
   > # urls.py
   > path('microsys/', include('microsys.urls')),
   > 
   > # settings.py
   > LOGIN_URL = '/microsys/accounts/login/'
   > LOGIN_REDIRECT_URL = '/microsys/sys/'
   > LOGOUT_REDIRECT_URL = '/microsys/accounts/login/'
   > ```

5. **Run Setup Command:**
   ```bash
   python manage.py microsys_setup
   ```
   This will create migrations, apply them, and validate your configuration.

## Management Commands

### `microsys_setup`
Initial setup command that handles migrations and configuration validation.

```bash
# Full setup (recommended for first install)
python manage.py microsys_setup

# Skip configuration check
python manage.py microsys_setup --skip-check

# Only validate config (skip migrations)
python manage.py microsys_setup --no-migrate
```

### `microsys_check`
Validates your Django settings and shows exact code snippets for any missing configuration.

```bash
python manage.py microsys_check
```

**Output example:**
```
🔍 MicroSys Configuration Check
==================================================

📋 INSTALLED_APPS: ✓ OK
📋 MIDDLEWARE: ✗ MISSING
📋 CONTEXT_PROCESSORS: ✓ OK
📋 URLS: ✓ OK
📋 CRISPY_FORMS: ✓ OK

==================================================
❌ REQUIRED CONFIGURATION MISSING:

▶ MIDDLEWARE:

MIDDLEWARE = [
    # ... after AuthenticationMiddleware
    'microsys.middleware.ActivityLogMiddleware',
]
```

> **Note:** microsys also validates your configuration at runtime and will emit warnings if required middleware or context processors are missing.

## App Configuration

Customize branding and behavior by adding `MICROSYS_CONFIG` and `SIDEBAR_AUTO` to your `settings.py`:

```python
MICROSYS_CONFIG = {
    'name': 'My System Name',           # App title in navbar/pages
    'verbose_name': 'ادارة النظام',      # App title in navbar/pages
    'logo': '/static/img/logo.png',     # Base/logo shown in the titlebar
    'login_logo': '/static/img/login_logo.webp',  # Logo on login screen
    'description': 'System Desc',       # Optional description
    'home_url': '/sys/',                 # Titlebar home link (default: /sys/)
    
    # ... branding fields only
}

# Auth redirects (defaults are set by microsys if not provided)
LOGIN_REDIRECT_URL = '/sys/'
LOGOUT_REDIRECT_URL = '/accounts/login/'

SIDEBAR_AUTO = {
    'ENABLED': True,                    # Enable auto-discovery
    'URL_PATTERNS': ['list'],           # Keywords to match in URL names for auto-menu
    'EXCLUDE_APPS': ['admin', 'auth'],  # Apps to exclude
    'CACHE_TIMEOUT': 3600,              # Cache timeout in seconds
    'DEFAULT_ICON': 'bi-list',          # Default Bootstrap icon

    # Built-in system group (accordion) can be disabled if desired
    'SYSTEM_GROUP_ENABLED': True,

    # Override auto-discovered items
    'DEFAULT_ITEMS': {
        'decree_list': {          # Key is the URL name
            'label': 'Decisions', # Override label
            'icon': 'bi-gavel',   # Override icon
            'order': 10,          # Sort order
        },
    },

    # Add manual items (e.g. for views without models)
    'EXTRA_ITEMS': {
        'الإدارة': {  # Accordion Group Name
            'icon': 'bi-gear',
            'items': [
                {
                    'url_name': 'manage_sections',
                    'label': 'إدارة الأقسام',
                    'icon': 'bi-diagram-3',
                    'permission': 'is_staff',
                },
            ]
        }
    }
}
```

## Core Components Usage

### 1. Profile Access
`microsys` automatically creates a `Profile` for every user via signals.
```python
# Accessing profile data
phone = user.profile.phone
scope = user.profile.scope
```

### 2. ScopedModel (Data Isolation)
To enable automatic scope filtering and soft-delete, **YOUR MODELS MUST** inherit from:
```python
from microsys.models import ScopedModel

class MyModel(ScopedModel):
    name = models.CharField(...)
    # ...
```
- **Automatic Scope Recognition**: `ScopedModel` already uses global scope settings, so you don't need to do anything.
- **Automatic Filtering**: Queries are automatically filtered by the current user's scope.
- **Soft Delete**: `MyModel.objects.get(pk=1).delete()` sets `deleted_at` instead of removing the row.

### 3. Sidebar Features
- **Auto-Discovery**: Automatically finds views like `*_list` and adds them to the sidebar.
- **Toggle**: Users can collapse/expand the sidebar; preference is saved in the session.
- **Reordering**: Drag-and-drop reordering is supported for authorized users.

### 4. Themes & Accessibility
Built-in support for:
- **Themes**: Dark / Light and colors.
- **Accessibility Modes**:
  - High Contrast
  - Grayscale
  - Invert Colors
  - x1.5 Zoom
  - Disable Animations
- **Location**: Accessible via the User Options menu (`options.html`) and Sidebar toolbar.

### 5. Sections (Auto Forms/Tables)
When a section model does not provide a custom Form/Table class, microsys generates them automatically.
You can exclude fields from those auto-generated classes by setting model attributes:

```python
class Department(models.Model):
    name = models.CharField(...)
    code = models.CharField(...)
    internal_notes = models.TextField(...)

    form_exclude = ["internal_notes"]
    table_exclude = ["internal_notes"]
```

Notes:
- These attributes apply only to the auto-generated form/table.
- If you provide a custom Form/Table class, it takes full precedence.

## Templates & Theming

### Base Template
The system provides a robust base template located at `microsys/templates/microsys/base.html`.
You can extend this template in your own views to maintain consistent layout and functionality:

```html
{% extends "microsys/base.html" %}

{% block extra_head %}
    <!-- Extra CSS or Meta tags -->
{% endblock %}

{% block content %}
    <h1>Page Content</h1>
{% endblock %}

{% block scripts %}
    <!-- Extra JS scripts -->
{% endblock %}
```

> **Note:** The base template automatically handles the sidebar, title bar, messages, and theme loading. Replacing it entirely will break core system functionality.

### Theming
- **Framework**: Built on **Bootstrap 5 (RTL)**.
- **Colors**: The `primary` color automatically adapts to the selected theme. Secondary/Success/Danger colors are slightly desaturated for better visual ergonomics.
- **Customization**:
  - Use standard Bootstrap classes (`btn-primary`, `text-success`, etc.).
  - Dark mode is supported out of the box. If you encounter issues, you can override styles via `extra_head` or report them.

---

## Dynamic Section Mode

Microsys offers a powerful "Zero-Boilerplate" CRUD interface for managing auxiliary data models (like Departments, Categories, etc.).

### How It Works
1. **Mark Your Model**: Add `is_section = True` to your model (or Meta class).
   ```python
   class Department(ScopedModel):
       name = models.CharField(...)
       is_section = True
   ```
2. **Auto-Discovery**: The system automatically generates a management UI with:
   - Searchable Table (with pagination & sorting)
   - Add/Edit Modals (using Crispy Forms)
   - Delete protection (checks for related records)
   - Filters (Keyword search + Date ranges if applicable)

   > **Note**: You can customize the auto-generated components by adding `form_exclude` and `table_exclude` lists to your model:
   > ```python
   > class Department(ScopedModel):
   >     # ...
   >     form_exclude = ['internal_notes']
   >     table_exclude = ['internal_notes', 'created_at']
   > ```

### Auto Subsections (Parent-Child Relations)
If a Section model has a `ManyToManyField` to another model that is **not** a standalone section (i.e. a "child" model), the system automatically nests it:

```python
class SubUnit(ScopedModel):  # Child model (no is_section=True)
    name = models.CharField(...)

class MainUnit(ScopedModel): # Parent section
    is_section = True
    sub_units = models.ManyToManyField(SubUnit)
```

**Result:**
- When editing a `MainUnit`, you will see a list of `SubUnits`.
- You can **Add/Edit/Delete** `SubUnits` directly from the `MainUnit` modal via AJAX.
- This creates a seamless "Master-Detail" management experience without writing a single view or form.

## File Structure

```
microsys/
├── models.py               # Profile, Scope, Logs
├── views.py                # User management views
├── forms.py                # User/Profile forms
├── signals.py              # Auto-create profile logic
├── context_processors.py   # Global variables & Scope
├── middleware.py           # Request capture
├── discovery.py            # Sidebar auto-discovery logic
├── templates/              # microsys/ (flattened structure)
└── static/                 # microsys/ (js/css/img)
```

## Version History

| Version  | Changes |
|----------|---------|
| v1.0.0   | • Initial release as pip package |
| v1.1.0   | • URL restructure: auth at `/accounts/`, system at `/sys/` • Added `microsys_setup` and `microsys_check` management commands • Runtime configuration validation |
| v1.2.0   | • PyPI name changed to `django-microsys` • Section model discovery hardened (dynamic app resolution, generic forms/tables/filters) • Scope fields now hide automatically when scopes are disabled • System sidebar group ships by default (configurable) • `is_staff` moved into the permissions UI |
| v1.3.0   | • Fixed subsection display: subsections now show correctly regardless of user scope • Fixed SessionInterrupted error: reduced session writes in section management • Scope toggle now accepts explicit target state to prevent race conditions • Improved error messaging in Arabic for scope operations |
| v1.4.0   | • Section table context menu: right-click on table rows for Edit/Delete actions • View Subsections modal: sections with M2M subsections show linked items • AJAX-based section deletion with related-record protection • Auto-generated tables now include row data attributes for JS binding |
| v1.5.0   | • Auto-generated section filters now include date range pickers (from/to) with flatpickr integration • Added clarifying inline comments to complex view logic • Fixed login Enter key submission |
