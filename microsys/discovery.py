"""
Auto-discovery module for sidebar navigation items.

Scans Django URL patterns for list views and matches them to models
to automatically generate sidebar navigation items.
"""
from django.urls import get_resolver, URLPattern, URLResolver
from django.apps import apps
from django.conf import settings
from difflib import get_close_matches


def get_sidebar_config():
    """Get sidebar configuration from Django settings with defaults."""
    system_group = {
        'name': 'إدارة النظام',
        'icon': 'bi-sliders',
        'items': [
            {
                'url_name': 'manage_sections',
                'label': 'إدارة الاقسام',
                'icon': 'bi-diagram-3',
                'permission': ['is_staff', 'microsys.manage_sections', 'microsys.view_sections'],
            },
            {
                'url_name': 'manage_users',
                'label': 'إدارة المستخدمين',
                'icon': 'bi-people',
                'permission': 'is_staff',
            },
            {
                'url_name': 'user_activity_log',
                'label': 'سجل النشاط',
                'icon': 'bi-clock-history',
                'permission': 'microsys.view_activity_log',
            },
            {
                'url_name': 'options_view',
                'label': 'خيارات التطبيق',
                'icon': 'bi-gear',
            },
        ],
    }
    defaults = {
        'ENABLED': True,
        'URL_PATTERNS': ['list'],
        'EXCLUDE_APPS': ['admin', 'auth', 'contenttypes', 'sessions'],
        'EXCLUDE_MODELS': [],
        'CACHE_TIMEOUT': 3600,
        'DEFAULT_ICON': 'bi-list',
        # Extra items that don't require model matching
        # Format: {'group_name': {'icon': 'bi-gear', 'items': [{'url_name': 'x', 'label': 'X', 'icon': 'bi-x'}]}}
        'EXTRA_ITEMS': {},
        # Built-in system group (appended after user EXTRA_ITEMS when enabled)
        'SYSTEM_GROUP_ENABLED': True,
        'SYSTEM_GROUP': system_group,
        # Default overrides for auto-discovered items
        # Format: {'url_name': {'label': 'X', 'icon': 'bi-x', 'order': 10}}
        'DEFAULT_ITEMS': {},
    }
    user_config = getattr(settings, 'SIDEBAR_AUTO', {})
    config = {**defaults, **user_config}

    # Merge EXTRA_ITEMS so user groups don't overwrite the system group
    merged_extra = {}
    user_extra = user_config.get('EXTRA_ITEMS', {})
    if isinstance(user_extra, dict):
        merged_extra.update(user_extra)

    if config.get('SYSTEM_GROUP_ENABLED', True):
        sys_group = config.get('SYSTEM_GROUP', system_group)
        sys_name = sys_group.get('name', 'إدارة النظام')
        sys_icon = sys_group.get('icon', 'bi-sliders')
        sys_items = list(sys_group.get('items', []))

        if sys_name in merged_extra:
            existing = merged_extra[sys_name]
            if not existing.get('icon'):
                existing['icon'] = sys_icon
            existing_items = list(existing.get('items', []))
            existing_urls = {item.get('url_name') for item in existing_items}
            for item in sys_items:
                if item.get('url_name') in existing_urls:
                    continue
                existing_items.append(item)
            existing['items'] = existing_items
            merged_extra[sys_name] = existing
        else:
            merged_extra[sys_name] = {'icon': sys_icon, 'items': sys_items}

    config['EXTRA_ITEMS'] = merged_extra
    return config



def discover_list_urls():
    """
    Scan all URL patterns for names containing configured keywords.
    Match them to Django models and extract verbose_name_plural.
    
    Returns:
        List of sidebar item dictionaries sorted by order.
    """
    config = get_sidebar_config()
    
    if not config['ENABLED']:
        return []
    
    resolver = get_resolver()
    items = []
    
    for pattern in _iterate_patterns(resolver.url_patterns):
        url_name = getattr(pattern, 'name', '') or ''
        
        # Check if URL name contains any of the configured patterns
        matched_keyword = None
        for kw in config['URL_PATTERNS']:
            if kw in url_name.lower():
                matched_keyword = kw
                break
        
        if matched_keyword:
            # Extract model hint (e.g., 'decree' from 'decree_list')
            model_hint = url_name
            for kw in config['URL_PATTERNS']:
                model_hint = model_hint.replace(f'_{kw}', '').replace(f'-{kw}', '').replace(kw, '')
            
            model_hint = model_hint.strip('_-')
            
            # Try to find model - first with stripped hint, then with keyword itself
            model = None
            if model_hint:
                model = _find_model(model_hint, config)
            
            # If no model found and keyword looks like it could be a model name, try that
            if not model and matched_keyword not in ['list', 'index', 'view', 'page']:
                model = _find_model(matched_keyword, config)
            
            if model:
                # Check exclusions
                if model._meta.app_label in config['EXCLUDE_APPS']:
                    continue
                if f"{model._meta.app_label}.{model.__name__}" in config['EXCLUDE_MODELS']:
                    continue
                
                items.append({
                    'url_name': url_name,
                    'label': getattr(model._meta, 'sidebar_label', None) or str(model._meta.verbose_name_plural),
                    'icon': getattr(model._meta, 'sidebar_icon', config['DEFAULT_ICON']),
                    'order': getattr(model._meta, 'sidebar_order', 100),
                    'app_label': model._meta.app_label,
                    'model_name': model._meta.model_name,
                    'permissions': [f'{model._meta.app_label}.view_{model._meta.model_name}'],
                })

            # Override with DEFAULT_ITEMS if present
            default_items = config.get('DEFAULT_ITEMS', {})
            if url_name in default_items:
                item_config = default_items[url_name]
                # Update last added item
                if items:
                    item = items[-1]
                    if 'label' in item_config:
                        item['label'] = item_config['label']
                    if 'icon' in item_config:
                        item['icon'] = item_config['icon']
                    if 'order' in item_config:
                        item['order'] = item_config['order']
    
    return sorted(items, key=lambda x: (x['order'], x['label']))


def _iterate_patterns(patterns, prefix=''):
    """Recursively iterate through URL patterns."""
    for pattern in patterns:
        if isinstance(pattern, URLResolver):
            yield from _iterate_patterns(pattern.url_patterns, prefix + str(pattern.pattern))
        elif isinstance(pattern, URLPattern):
            yield pattern


def _find_model(hint, config):
    """
    Find model by name using exact and fuzzy matching.
    
    Args:
        hint: The model name hint extracted from URL
        config: Sidebar configuration dictionary
        
    Returns:
        Model class or None if not found
    """
    all_models = apps.get_models()
    
    # Build lookup excluding configured apps
    model_names = {}
    for m in all_models:
        if m._meta.app_label not in config['EXCLUDE_APPS']:
            model_names[m.__name__.lower()] = m
    
    hint_lower = hint.lower()
    
    # Exact match first
    if hint_lower in model_names:
        return model_names[hint_lower]
    
    # Handle common pluralization (simple 's' suffix)
    if hint_lower.endswith('s') and hint_lower[:-1] in model_names:
        return model_names[hint_lower[:-1]]
    
    # Fuzzy match as fallback
    matches = get_close_matches(hint_lower, model_names.keys(), n=1, cutoff=0.8)
    return model_names[matches[0]] if matches else None
