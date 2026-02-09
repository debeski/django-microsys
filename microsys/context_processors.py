from .utils import is_scope_enabled
from django.conf import settings
import hashlib
import json
from django.core.cache import cache
from django.urls import reverse, NoReverseMatch
from .discovery import discover_list_urls, get_sidebar_config

# Helper functions for Sidebar - KEPT PRIVATE
def _get_config_hash(config):
    """Generate a hash of the config for cache key."""
    # Exclude EXTRA_ITEMS from hash since they're processed separately
    config_copy = {k: v for k, v in config.items() if k != 'EXTRA_ITEMS'}
    config_str = json.dumps(config_copy, sort_keys=True)
    return hashlib.md5(config_str.encode()).hexdigest()[:8]

def _process_extra_items(config, request):
    """
    Process EXTRA_ITEMS config into sidebar-ready format.
    
    Returns dict of groups, each with icon and list of items with resolved URLs.
    """
    extra_items = config.get('EXTRA_ITEMS', {})
    processed_groups = {}
    
    for group_name, group_config in extra_items.items():
        group_icon = group_config.get('icon', 'bi-gear')
        items = []
        
        for item in group_config.get('items', []):
            url_name = item.get('url_name', '')
            
            # Check permission if specified (supports string or list/tuple/set)
            permission = item.get('permission')
            if permission:
                perms = permission if isinstance(permission, (list, tuple, set)) else [permission]
                allowed = False
                for perm in perms:
                    if perm == 'is_staff':
                        allowed = request.user.is_staff
                    elif perm == 'is_superuser':
                        allowed = request.user.is_superuser
                    else:
                        allowed = request.user.has_perm(perm)
                    if allowed:
                        break
                if not allowed:
                    continue
            
            # Resolve URL
            try:
                url = reverse(url_name)
                active = request.path == url or request.path.startswith(url.rstrip('/') + '/')
            except NoReverseMatch:
                url = '#'
                active = False
            
            items.append({
                'url_name': url_name,
                'url': url,
                'label': item.get('label', url_name),
                'icon': item.get('icon', 'bi-link'),
                'active': active,
            })
        
        if items:  # Only add group if it has visible items
            processed_groups[group_name] = {
                'icon': group_icon,
                'items': items,
                'has_active': any(item['active'] for item in items),
            }
    
    return processed_groups

def microsys_context(request):
    """
    Unified context processor for the entire Microsys package.
    Combines:
    1. Branding Configuration (APP_CONFIG)
    2. Scope Settings
    3. Sidebar Navigation items
    4. Theme Settings
    """
    context = {}

    # 1. Branding / App Config
    # Default configuration
    default_config = {
        'name': 'microsys',
        'verbose_name': 'ادارة النظام',
        'logo': '/static/img/base_logo.png',
        'login_logo': '/static/img/login_logo.webp',
        'favicon': '/static/favicon.ico',
        'home_url': '/sys/',  # Default home link in titlebar
    }
    
    # Get user config from settings.py
    user_config = getattr(settings, 'MICROSYS_CONFIG', {})
    
    # Merge configurations
    final_config = default_config.copy()
    final_config.update(user_config)
    
    context['APP_CONFIG'] = final_config


    # 2. Scope Settings
    # We add this boolean so templates know if the scope feature is ON globally
    context['scope_settings'] = {'is_enabled': is_scope_enabled()}


    # 3. Sidebar Context
    # Sidebar logic logic
    config = get_sidebar_config()
    # Include config hash in cache key so settings changes invalidate cache
    cache_key = f'sidebar_auto_items_{_get_config_hash(config)}'
    items = cache.get(cache_key)
    
    if items is None:
        items = discover_list_urls()
        cache.set(cache_key, items, timeout=config['CACHE_TIMEOUT'])
    
    # Filter by user permissions
    sidebar_items = []
    extra_groups = {}

    if request.user.is_authenticated:
        if request.user.is_superuser:
            # Superusers see everything
            sidebar_items = items
        else:
            visible = []
            for item in items:
                if not item.get('permissions'):
                    visible.append(item)
                elif any(request.user.has_perm(p) for p in item['permissions']):
                    visible.append(item)
            sidebar_items = visible
        
        # Process extra items for authenticated users
        extra_groups = _process_extra_items(config, request)
    
    context['sidebar_auto_items'] = sidebar_items
    context['sidebar_extra_groups'] = extra_groups
    
    # 4. Sidebar State (Collapsed/Expanded)
    context['sidebar_collapsed'] = request.session.get('sidebarCollapsed', False)

    return context


def clear_sidebar_cache():
    """
    Clear the sidebar items cache.
    Call this when models or URLs change and sidebar needs refresh.
    """
    # Note: We can't easily clear specific hash keys, so we might need a more robust clearing strategy
    # or just rely on timeout. For now, this function is a placeholder or partial implementation.
    # To truly clear, we'd need to track keys or use a specific prefix clear if supported by backend.
    # Simpler: Just rely on short timeout during dev.
    pass
