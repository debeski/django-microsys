# Django microSYS - System Integration Service

[![PyPI version](https://badge.fury.io/py/django-microsys.svg)](https://pypi.org/project/django-microsys/)

<p align="center">
  <img src="https://raw.githubusercontent.com/debeski/django-microsys/main/microsys/static/img/login_logo.webp" alt="microSys Logo" width="450"/>
</p>

<center>**Multilingual** lightweight, dynamic Django app providing a comprehensive, highly customizable system integration service, including user management, profile extension, permissions, language switching, dynamic sidebar, automated activity logging, dynamic auxiliary model detection, global autofill feature and more.</center>

---

## 📋 Requirements
- Python 3.11+
- Django 5.1.4+
- django-crispy-forms 2.3+
- crispy-bootstrap5 2025.3+
- django-tables2 2.5+
- django-filter 24.1+
- django-health-check 3.20+
- psutil

---

## 🚀 Installation

```bash
pip install git+https://github.com/debeski/django-microsys.git
# OR
pip install django-microsys
```

---

## ⚙️ Quick Start & Configuration

1. **Add to `INSTALLED_APPS`:**
   ```python
   INSTALLED_APPS = [
       'django.contrib.admin',
       'django.contrib.auth',
       # ... dependencies
       'crispy_forms',
       'crispy_bootstrap5',
       'django_filters',
       'django_tables2',

       'microsys', # Place anywhere.
   ]
   ```

2. **Add Middleware:**
   Required for activity logging and request caching.
   ```python
   MIDDLEWARE = [
       # ...
       'django.contrib.auth.middleware.AuthenticationMiddleware',
       # ... Must be below Auth Middleware
       'microsys.middleware.ActivityLogMiddleware',
   ]
   ```

3. **Add Context Processor:**
   Unified context processor for branding, sidebar config, scope settings, auto-fill, and more.
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

---

### 🛠️ Management Commands

- `microsys_setup`
Initial setup command that handles migrations and configuration validation.

```bash
# Full setup (recommended for first install)
python manage.py microsys_setup

# Skip configuration check
python manage.py microsys_setup --skip-check

# Only validate config (skip migrations)
python manage.py microsys_setup --no-migrate
```

- `microsys_check`
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

---

### 🖥️ App Configuration

Customize branding and behavior by adding `MICROSYS_CONFIG` to your `settings.py`:

```python
MICROSYS_CONFIG = {
    'name': 'My System Name',           # App title in navbar/pages
    'verbose_name': 'ادارة النظام',      # App title in navbar/pages
    'logo': '/static/img/logo.png',     # Base/logo shown in the titlebar
    'login_logo': '/static/img/login_logo.webp',  # Logo on login screen
    'description': 'System Desc',       # Optional description
    'home_url': '/sys/',                 # Controls Titlebar home link AND default login redirect
    
    # ... branding fields only

    # Language switching (optional, Arabic-only by default)
    'languages': {
        'ar': {'name': 'العربية', 'dir': 'rtl', 'flag': '🇱🇾'},
        'en': {'name': 'English', 'dir': 'ltr', 'flag': '🇬🇧'},
    },
    'default_language': 'ar',  # Fallback language

    # Override or extend built-in translation strings (optional)
    # 'translations': {
    #     'en': {'dashboard_welcome': 'Welcome to My Custom System.'},
    # },
}

# Auth redirects
# 1. 'next' query param (highest priority)
# 2. LOGIN_REDIRECT_URL in settings (if set)
# 3. MICROSYS_CONFIG['home_url'] (if set)
# 4. '/sys/' (default fallback)
LOGIN_REDIRECT_URL = '/sys/' 
LOGOUT_REDIRECT_URL = '/accounts/login/'
```

---

## ✨ Features:
- **System Integration**: Centralized management for users, permissions and system scopes.
- **Profile Extension**: Automatically links a `Profile` to your existing User model.
- **Scope Management**: Optional, dynamic scope isolation system with abstract `ScopedModel`.
- **Permissions**: Custom grouped permission UI (App/Model/Action).
- **User Detail View**: Detailed page for user profile, activity, and last login.
- **Dynamic Auxiliary Model Detection**: Zero-Boilerplate Zero-Code Detection of auxiliary models using model attrs.
- **Dynamic Forms, Filters and Tables**: Automatically detects and registers or creates forms, filters and tables to auxiliary models.
- **Global Autofill**: Dynamic Smart Autofill tool that fills form fields based on related FK models, or model last entry.
- **Automated Logging**: Full automatic activity tracking (CRUD, Login/Logout) via Signals.
- **Dynamic Sidebar**: Auto-discovery of list views and customizable, reorderable menu items.
- **Dynamic Titlebar**: Show-Hide autofill-toggle, dynamic home url, and title.
- **Options View**: Options view to enable, disable, and configure system features and details.
- **Language Selector**: Native Arabic support with dynamic language switching with optional additional languages (RTL/LTR).
- **Themes & Accessibility**: Bootstrap5 integration with built-in dark/light modes and accessibility tools (High Contrast, Zoom, etc.).
- **Native Mobile Support**: Responsive design for all screen sizes.
- **Health Checks**: Built-in health checks for common issues.
- **Tutorial**: Built-in help/tutorial for microSYS views and features.
- **Security**: CSP compliance, role-based access control (RBAC), Backend A&A enforcement.

---

### 👤 User Management

1. Profile Access
`microsys` automatically creates a `Profile` for every user via signals.
```python
# Accessing profile data
phone = user.profile.phone
scope = user.profile.scope
```

2. Grouped Permissions
Microsys provides a custom, intuitive UI for managing permissions. Permissions are automatically grouped by **Application**, **Model**, and **Action** (View, Add, Change, Delete), making it easy to manage complex access controls.

3. Automated Activity Logging
Every action (CRUD, Login/Logout, etc.) is automatically recorded in the `UserActivityLog`.
- **Global Middleware**: Tracks IP address and User Agent.
- **Signal-Based**: Captures changes even from the Django Admin.
- **Searchable**: View and filter activity logs directly from the system dashboard.

4. Unified Preferences
User UI settings (Theme, Language, Sidebar State, Autofill status) are persisted in the database (`Profile.preferences`), ensuring a consistent experience across different browsers and devices.

---

### 🏗️ Core Integration (ScopedModel)

The foundation of the Microsys ecosystem is the `ScopedModel`. By inheriting from this abstract base, your models immediately gain advanced system features that ensure seamless integration with the dashboard and auxiliary management tools:

```python
from microsys.models import ScopedModel

class MyModel(ScopedModel):
    name = models.CharField(...)
    # ... your fields
```

- **Data Isolation**: Automatically partitions data by the user's assigned `Scope`.
- **Zero-Boilerplate Filtering**: The `ScopedManager` ensures users only see authorized data without manual `.filter(scope=...)` calls.
- **Soft-Delete**: Deleting a record sets a `deleted_at` timestamp instead of removing the row, allowing for easy recovery and audit trails.
- **Deep Integration**: `ScopedModel` allows the system to automatically handle complex relationships, section discovery, and subsection management flawlessly.

---

### 📂 Dynamic Section Mode

Microsys offers a powerful "Zero-Boilerplate" CRUD interface for managing auxiliary data models (like Departments, Categories, etc.).

- **How It Works**
1. **Mark Your Model**: Add `is_section = True` to your model attrs.
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

- **Auto Subsections (Parent-Child Relations)**
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

Notes:
- These attributes apply only to the auto-generated form/table.
- If you provide a custom Form/Table class, it takes full precedence.

---

### ⚡ Global Autofill

`microsys` includes a powerful client-side autofill engine designed to eliminate repetitive data entry.

- **Features**
1.  **Smart FK Autofill**:
    -   Selecting a ForeignKey (e.g., `User`, `Employee`) automatically populates related fields in the form (like `email`, `phone`, `department`).
    -   **Recursive Data Fetching**: It intelligently fetches data from related `OneToOne` models (e.g., `User.profile.phone`) without extra configuration.
    -   **Auto-Clear**: Deselecting a value or toggling autofill **OFF** instantly clears the related fields to prevent stale data.

2.  **Sticky Forms (Clone Last Entry)**:
    -   Perfect for high-volume data entry. When enabled, the form automatically pre-fills with values from the **last created record** upon load.
    -   Submitting the form saves the state, allowing rapid sequential entry.

3.  **Global Toggle**:
    -   A toggle switch automatically appears in the top-right title bar whenever autofill is available on the page.
    -   The state (ON/OFF) is saved in your browser's local storage.

- **How to Use**

1. **Foreign Key Autofill (Zero Config)**
The system automatically detects standard Django ForeignKey widgets and injects the necessary `data-autofill-source` attributes. **It works out of the box.**

> **Note**: Only works for fields that have a corresponding input in the form with a matching name (e.g., `User.email` -> `<input name="email">`).

2. **Enable Sticky Forms**
To enable the "Clone Last Entry" feature for a specific form, simply add the `data-model-name` attribute to your HTML form tag:

```html
<form method="post" data-app-label="myapp" data-model-name="mymodel">
    <!-- ... fields ... -->
</form>
```

---

### ↔️ Interactive Sidebar 

The sidebar is a dynamic, highly customizable navigation hub that supports both auto-discovery and manual configuration.

- **Auto-Discovery Mode**
Microsys can automatically introspect your project's URL patterns and Models to generate navigation items. By default, it looks for URLs containing `_list`.

```python
SIDEBAR_AUTO = {
    'ENABLED': True,                    # Enable auto-discovery
    'URL_PATTERNS': ['list'],           # Keywords to match in URL names
    'EXCLUDE_APPS': ['admin', 'auth'],  # Apps to exclude from sidebar
    'CACHE_TIMEOUT': 3600,              # Cache timeout in seconds
    'DEFAULT_ICON': 'bi-list',          # Default Bootstrap icon
    'SYSTEM_GROUP_ENABLED': True,       # Toggle the built-in "System Management" group
}
```

- **Advanced Customization**
Fine-tune the sidebar behavior using `SIDEBAR_AUTO` settings in your `settings.py`:

- **Reordering**: Users with `is_staff` or specific permissions can toggle **Reorder Mode** from the sidebar toolbar. Drag and drop items to customize the layout; the new order is persisted to the database preferences.
- **Label & Icon Overrides**: Use `DEFAULT_ITEMS` to customize labels, icons, or sort order for auto-discovered views without modifying the models.
- **Custom Groups (Accordions)**: Use `EXTRA_ITEMS` to add manual groups and links for non-model views or external URLs. Supports permission-based visibility.

```python
SIDEBAR_AUTO = {
    'DEFAULT_ITEMS': {
        'decree_list': {
            'label': 'Decisions', 
            'icon': 'bi-gavel', 
            'order': 10
        },
    },
    'EXTRA_ITEMS': {
        'Management': {
            'icon': 'bi-gear',
            'items': [
                {
                    'url_name': 'custom_report', 
                    'label': 'Yearly Report', 
                    'icon': 'bi-file-earmark-bar-graph',
                    'permission': 'is_staff'
                },
            ]
        }
    }
}
```

- Template Tags
If you are building a custom sidebar template, you can use these tags:
- `{% auto_sidebar %}`: Renders all auto-discovered items.
- `{% extra_sidebar %}`: Renders the groups and items defined in `EXTRA_ITEMS`.

---

### 🖱️ Micro Context Menu ("Right-Click")

A global, data-driven context menu that can be attached to any element to provide quick actions.

- **How it works**
1. **Mark Element**: Add `data-micro-context="true"` to any HTML element.
2. **Define Actions**: Provide a JSON list of actions in `data-micro-actions`.

```html
<tr data-micro-context="true" 
    data-micro-actions='[{"label": "Edit", "url": "/edit/1", "icon": "bi-pencil"}]'>
    ...
</tr>
```

- **Features**:
  - **Global**: Works anywhere, automatically initialized.
  - **Dynamic**: Actions are defined per-element via data attributes.
  - **Mobile Ready**: Supports long-press on touch devices.
  - **Standardized**: Used by system tables (Users, Sections) for a consistent experience.
  - **Double Click**: Supports double-click actions (e.g. View) if `dblclick: true` is set on an action.
  - **Smart Actions**: Includes "View Content" and "Smart Delete" handling for Sections using dynamic modals.

- **Usage with Django Tables2**

You can inject the context menu directly from your `tables.py` without modifying templates.

1.  **Define Row Attributes**: Use `row_attrs` in `Meta` or `__init__`.
2.  **Define Actions**: Create a list of actions and serialize to JSON.

```python
import json
from django.urls import reverse

class MyTable(tables.Table):
    class Meta:
        model = MyModel
        # ...

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Define Actions Helper
        def get_actions(record):
            actions = [
                {
                    "label": "View", 
                    "icon": "bi bi-eye", 
                    "url": reverse('my_view', args=[record.pk]),
                    "dblclick": True  # OPTIONAL: Trigger on double-click
                },
                {"type": "divider"},
                {
                    "label": "Delete", 
                    "icon": "bi bi-trash", 
                    "url": reverse('my_delete', args=[record.pk]),
                    "textClass": "text-danger"
                }
            ]
            return json.dumps(actions)

        # Inject Attributes
        self.row_attrs.update({
            "data-micro-context": "true",
            "data-micro-actions": get_actions
        })
```

---

### 🌍 Translation Framework
 
microsys ships with Arabic and English translations. Add more languages via `MICROSYS_CONFIG['languages']`.

**How it works:**
- The system automatically discovers and loads translations from all installed apps.
- It looks for `translations.py` in each app and merges the `MS_TRANSLATIONS` dictionary.
- Language is resolved: **user preference** → **`default_language`** → **`'ar'`**
- Templates use `{{ MS_TRANS.key }}` for all UI strings.
- The `<html>` tag gets dynamic `lang`/`dir` attributes.
- Bootstrap CSS auto-switches between RTL and LTR variants.

**Template variables available:**
| Variable | Type | Description |
|---|---|---|
| `CURRENT_LANG` | `str` | Active language code (e.g. `'ar'`, `'en'`) |
| `CURRENT_DIR` | `str` | Active direction (`'rtl'` or `'ltr'`) |
| `LANGUAGES` | `dict` | All configured languages |
| `MS_TRANS` | `dict` | Translated strings for the active language |

**Adding custom strings:**
Simply add a `translations.py` file to any of your apps:
```python
# my_app/translations.py
MS_TRANSLATIONS = {
    'ar': {'my_key': 'قيمة مخصصة'},
    'en': {'my_key': 'Custom Value'},
}
```
Then in templates: `{{ MS_TRANS.my_key }}`

---

### 🎨 Templates & Theming

- **Base Template**
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

- **Customizing Base Template (Injection)**

You can inject custom HTML, CSS, or JavaScript into the `microsys` base template globally without overriding the entire template.
This is useful for adding analytics scripts, global styles, or meta tags.

**How to use:**
Create the following files in your project's `templates/` directory:

1.  **Head Content (Meta, CSS)**: `microsys/includes/custom_head.html`
    - Renders in `<head>`, **before** `{% block extra_head %}`.
    - Ideal for global CSS overrides or meta tags.

2.  **Scripts**: `microsys/includes/custom_scripts.html`
    - Renders just before `</body>`.
    - Ideal for global JS libraries or analytics.

> **Note**: Because these are templates (not static files), you can use template tags like `{% static %}` or `{% url %}` inside them, in addition to conditional logic!

- **Theming**
- **Framework**: Built on **Bootstrap 5**.
- **Colors**: The `primary` color automatically adapts to the selected theme. Secondary/Success/Danger colors are slightly desaturated for better visual ergonomics.
- **Customization**:
  - Use standard Bootstrap classes (`btn-primary`, `text-success`, etc.).
  - Dark mode is supported out of the box. If you encounter issues, you can override styles via `extra_head` or report them.

- **Unified User Preferences (DB-Backed)**
The system now centralizes user UI settings in the database instead of relying on `localStorage` or server sessions. This ensures that a user's chosen theme, sidebar state, and item ordering are consistent across all their devices.

- **Storage**: Preferences are stored in a `JSONField` named `preferences` within the `Profile` model.
- **Syncing**: An API endpoint (`/sys/api/preferences/update/`) handles real-time updates from the frontend.
- **Persistence**:
  - **Sidebar**: Collapsed/Expanded state and open accordion groups are persisted.
  - **Reordering**: Drag-and-drop order of sidebar items is saved globally.
  - **Theme**: Selected UI theme (Light, Dark, Royal, etc.) is synced.
  - **Language**: Selected language is synced.
  - **Autofill**: Selected autofill state is synced.

> [!IMPORTANT]
> To enable this feature, ensure you have applied migrations (`makemigrations microsys` and `migrate microsys`).

- **Dashboard Activity Chart**
The dashboard now includes a built-in activity chart powered by **Plotly.js**:
- **Visualizes**: System activity for the last 24 hours.
- **Design**: Seamless, transparent, lightweight line chart with no axis labels for a clean look.
- **Data Source**: Aggregates `UserActivityLog` entries.
- **Responsive**: Automatically resizes with the window and sidebar toggles using `ResizeObserver`.

----

## 📁 File Structure

```
microsys/
├── management/             # Custom Management commands.
├── migrations/             # App Migrations.
├── static/                 # microsys/ (js/css/img).
├── templates/              # microsys/ (flattened structure).
├── templatetags/           # Custom template tags.
├── tests/                  # Development tests.
├── admin.py                # Admin Panel Registration.
├── api.py                  # Autofill Api Configuration, Permission Checker, Serializer.
├── apps.py                 # Django App configuration.
├── context_processors.py   # Branding, Scope, Sidebar order and Themes.
├── discovery.py            # Sidebar auto-discovery logic.
├── fetcher.py              # Universal Dynamic Downlolader.
├── filters.py              # User and ActivityLog filters.
├── forms.py                # User, Profile, Permissions, and Section forms
├── managers.py             # ScopedModel Manager.
├── middleware.py           # ActivityLog middleware.
├── models.py               # Profile, Scope, Logs.
├── signals.py              # Auto-create profile logic, Auto soft-delete logic, ActivityLog.
├── tables.py               # User, ActivityLog, and Scope tables.
├── urls.py                 # URL routing.
├── utils.py                # Helping Dynamic functions.
└── views.py                # User and Scope management, Dynamic Zero-Boilerplate Section management.
```

## 📜 Version History

| Version  | Changes |
|----------|---------|
| v1.0.0   | • Initial release as pip package |
| v1.1.0   | • **Application Complete Restructure** with moudular files, templates, static, etc. <br> • URL restructure: auth at `/accounts/`, system at `/sys/` <br> • Added `microsys_setup` and `microsys_check` management commands <br> • Runtime configuration validation |
| v1.2.0   | • **Dynamic Section Management** New Powerful Zero-Boilerplate Section management mode <br> • Name changed to `django-microsys` <br> • Scope fields now hide automatically when scopes are disabled <br> • System sidebar group ships by default (configurable) <br> • `is_staff` moved into the permissions UI |
| v1.2.1   | • Fixed subsection display: subsections now show correctly regardless of user scope <br> • Fixed SessionInterrupted error: reduced session writes in section management <br> • Scope toggle now accepts explicit target state to prevent race conditions <br> • Improved error messaging in Arabic for scope operations |
| v1.3.0   | • **Section table context menu**: right-click on table rows for Edit/Delete actions <br> • **View Subsections modal**: sections with M2M subsections show linked items in a modal <br> • AJAX-based section deletion with related-record protection <br> • Auto-generated tables now include row data attributes for JS binding |
| v1.3.1   | • Auto-generated section filters now include date range pickers (from/to) with flatpickr integration <br> • Added clarifying inline comments to complex view logic <br> • Fixed login Enter key submission <br> • Pypi Release |
| v1.3.2   | • Fixed Readme file and added detailed instructions |
| v1.3.3   | • Optimized form and filters auto generation and layout |
| v1.3.4   | • Added global head and scripts injection |
| v1.3.5   | • Switch to Database JSON attached to user profile for consistent prefrences accross devices |
| v1.3.6   | • Fixed theme picker popup positioning in LTR mode (CSS logical properties) |
| v1.4.0   | • **Comprehensive Translation Framework**: table headers, filter labels/placeholders, and template strings now resolved from `translations.py` per user language <br> • Tables, filters, and templates (`manage_users`, `user_activity_log`, `manage_sections`) fully translated <br> • Reset Defaults now purges sidebar reordering from DB and localStorage <br> • Reset UI redesigned to match other options (inline Confirm/Cancel animation) <br> • Fixed activity log actions always showing in Arabic regardless of language (duplicate `get_table_kwargs`) |
| v1.4.1   | • Translation related fixes and UI enhancements |
| v1.5.0   | • **Global Dynamic Autofill Feature**: Automatically fill forms from related ForeignKeys (e.g. User Profile data) with smart clearing and toggle controls |
| v1.5.1   | • Autofill fixes: Resolved 500/404 errors during clearing, refined toggle behavior, and standardized console logging |
| v1.5.2  | • Completely Restructured README for a clearer understanding of the system and its setup |
| v1.6.0  | • **Context Menu**: Added global, data-driven context menu support for interactive elements |
| v1.6.1  | • **Translation Upgrade**: Improved translation system and coverage <br> • Various bug fixes and stability improvements |
| v1.6.2  | • **Custom Password Form**: Refactored password change form with dynamic translations and helpful descriptions <br> • **RTL/LTR Fixes**: Fixed Login screen text direction in English mode <br> • **Profile Translations**: Fully translated profile view and edit pages |
| v1.6.3  | • **Login Enhancements**: Added language switcher, session-based language persistence, and fixed RTL alignment bug <br> • **Smart Redirects**: Login now automatically redirects authenticated users and supports `home_url` config fallback <br> • **Unified Translations**: Refactored internal translation helper to support anonymous sessions |