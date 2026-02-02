from django.apps import apps

def is_scope_enabled():
    """
    Checks if the Scope system is globally enabled.
    Returns:
        bool: True if enabled, False otherwise.
    """
    try:
        ScopeSettings = apps.get_model('users', 'ScopeSettings')
        return ScopeSettings.load().is_enabled
    except LookupError:
        # Fallback if model shouldn't be loaded yet (e.g. migration)
        return True
