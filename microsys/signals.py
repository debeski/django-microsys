# Imports of the required python modules and libraries
######################################################
from django.dispatch import receiver
from django.db.models.signals import post_save, post_delete, pre_save
from django.utils.timezone import now
from django.apps import apps
from django.contrib.auth.signals import user_logged_in, user_logged_out
from django.contrib.auth import get_user_model
from .middleware import get_current_user, get_current_request

def get_client_ip(request):
    """Extract client IP address from request."""
    if not request:
        return None
    x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
    if x_forwarded_for:
        ip = x_forwarded_for.split(",")[0]
    else:
        ip = request.META.get("REMOTE_ADDR")
    return ip

@receiver(user_logged_in)
def log_login(sender, request, user, **kwargs):
    """Log user login actions."""
    UserActivityLog = apps.get_model('microsys', 'UserActivityLog')
    UserActivityLog.objects.create(
        user=user,
        action="LOGIN",
        model_name="مصادقة",
        object_id=None,
        ip_address=get_client_ip(request),
        user_agent=request.META.get("HTTP_USER_AGENT", ""),
        timestamp=now(),
    )

@receiver(user_logged_out)
def log_logout(sender, request, user, **kwargs):
    """Log user logout actions."""
    UserActivityLog = apps.get_model('microsys', 'UserActivityLog')
    UserActivityLog.objects.create(
        user=user,
        action="LOGOUT",
        model_name="مصادقة",
        object_id=None,
        ip_address=get_client_ip(request),
        user_agent=request.META.get("HTTP_USER_AGENT", ""),
        timestamp=now(),
    )

@receiver(pre_save)
def capture_soft_delete_state(sender, instance, **kwargs):
    """Capture state to detect soft delete in post_save."""
    if instance.pk and hasattr(instance, 'deleted_at'):
        try:
            old_instance = sender.objects.get(pk=instance.pk)
            instance._was_not_deleted = (old_instance.deleted_at is None)
        except sender.DoesNotExist:
            pass

@receiver(post_save)
def create_user_profile(sender, instance, created, **kwargs):
    """Auto-create Profile for new users."""
    # Check if sender is the AUTH_USER_MODEL
    if sender == get_user_model():
        if created:
             Profile = apps.get_model('microsys', 'Profile')
             Profile.objects.create(user=instance)

# Models to exclude from activity logging (e.g., internal Django models with non-integer PKs)
EXCLUDED_MODELS = [
    'django.contrib.sessions.models.Session',
]

def get_model_path(sender):
    """Get full model path for comparison."""
    return f"{sender.__module__}.{sender.__name__}"

@receiver(post_save)
def log_save(sender, instance, created, **kwargs):
    """Log create and update actions for all models."""
    # Prevent infinite recursion by skipping the log model itself
    UserActivityLog = apps.get_model('microsys', 'UserActivityLog')
    if sender == UserActivityLog:
        return
    
    # Skip excluded models (like Session)
    if get_model_path(sender) in EXCLUDED_MODELS:
        return

    # Get the current user from thread locals
    user = get_current_user()
    if not user or not user.is_authenticated:
        return

    # Ignore implicit updates to last_login (handled by user_logged_in signal)
    update_fields = kwargs.get('update_fields')
    if update_fields and 'last_login' in update_fields and len(update_fields) == 1:
        return

    action = "CREATE" if created else "UPDATE"
    
    # Check for soft delete transition
    if not created and getattr(instance, '_was_not_deleted', False) and getattr(instance, 'deleted_at', None):
        action = "DELETE"

    model_name = instance._meta.verbose_name
    
    # Use string representation of the object for 'number' or reference
    try:
        obj_str = str(instance)
    except TypeError:
        # Fallback if __str__ returns non-string (e.g. int)
        obj_str = str(instance.pk)

    request = get_current_request()
    ip = get_client_ip(request)
    user_agent = request.META.get("HTTP_USER_AGENT", "") if request else ""

    # Handle non-integer PKs gracefully
    try:
        obj_id = int(instance.pk) if instance.pk is not None else None
    except (ValueError, TypeError):
        obj_id = None

    UserActivityLog.objects.create(
        user=user,
        action=action,
        model_name=model_name,
        object_id=obj_id,
        number=obj_str[:50] if obj_str else None,
        ip_address=ip,
        user_agent=user_agent,
        timestamp=now()
    )

@receiver(post_delete)
def log_delete(sender, instance, **kwargs):
    """Log delete actions for all models."""
    UserActivityLog = apps.get_model('microsys', 'UserActivityLog')
    if sender == UserActivityLog:
        return
    
    # Skip excluded models (like Session)
    if get_model_path(sender) in EXCLUDED_MODELS:
        return

    user = get_current_user()
    if not user or not user.is_authenticated:
        return

    action = "DELETE"
    model_name = instance._meta.verbose_name
    
    try:
        obj_str = str(instance)
    except TypeError:
        obj_str = str(instance.pk)

    request = get_current_request()
    ip = get_client_ip(request)
    user_agent = request.META.get("HTTP_USER_AGENT", "") if request else ""

    # Handle non-integer PKs gracefully
    try:
        obj_id = int(instance.pk) if instance.pk is not None else None
    except (ValueError, TypeError):
        obj_id = None

    UserActivityLog.objects.create(
        user=user,
        action=action,
        model_name=model_name,
        object_id=obj_id,
        number=obj_str[:50] if obj_str else None,
        ip_address=ip,
        user_agent=user_agent,
        timestamp=now()
    )