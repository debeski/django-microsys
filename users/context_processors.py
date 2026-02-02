from .utils import is_scope_enabled

def scope_settings(request):
    """
    Context processor to add scope settings to all templates.
    """
    return {
        'scope_enabled': is_scope_enabled()
    }
