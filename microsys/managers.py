from django.db import models
from django.apps import apps
from .middleware import get_current_user

class ScopedManager(models.Manager):
    """
    A manager that automatically filters queries by the current user's scope.
    Also handles soft-deletion if 'deleted_at' field is present.
    """
    
    def get_queryset(self):
        qs = super().get_queryset()
        
        # 1. Soft Delete Check
        # If the model has a 'deleted_at' field, exclude deleted records
        if hasattr(self.model, 'deleted_at'):
             # We need to check if 'deleted_at' is actually a field in the model
             # to avoid errors if it's just a property or method
             try:
                 self.model._meta.get_field('deleted_at')
                 qs = qs.filter(deleted_at__isnull=True)
             except Exception:
                 pass

        # 2. Scope Filtering
        # Check if Scope system is globally enabled
        try:
            ScopeSettings = apps.get_model('microsys', 'ScopeSettings')
            if not ScopeSettings.load().is_enabled:
                return qs
        except (LookupError, Exception):
            # If ScopeSettings table doesn't exist yet (e.g. migration), skip
            return qs

        user = get_current_user()
        
        # If no user or user is superuser, return all
        if not user or not user.is_authenticated or user.is_superuser:
            return qs

        # If user has a scope, filter by it
        # Note: We use 'scope' string, assuming the field name on the model is 'scope'
        if hasattr(user, 'profile') and user.profile.scope:
             # Check if the model actually has a 'scope' field
             try:
                 self.model._meta.get_field('scope')
                 qs = qs.filter(scope=user.profile.scope)
             except Exception:
                 pass
        elif hasattr(user, 'scope') and user.scope: # Layout for old CustomUser (will be removed later)
             try:
                 self.model._meta.get_field('scope')
                 qs = qs.filter(scope=user.scope)
             except Exception:
                 pass
                 
        return qs
