# Imports of the required python modules and libraries
######################################################
from django.apps import AppConfig
from django.apps import apps


def custom_permission_str(self):
    """Custom Arabic translations for Django permissions"""
    permission_name = str(self.name)

    # Translation map for keywords
    replacements = {
        "Can add": "إضافة",
        "Can change": "تعديل",
        "Can delete": "حذف",
        "Can view": "عرض",
        "permission": "الصلاحيات",
    }

    for en, ar in replacements.items():
        permission_name = permission_name.replace(en, ar)

    return permission_name.strip()

class MicrosysConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'microsys'
    verbose_name = "ادارة النظام"

    def ready(self):
        # Runtime configuration validation
        self._validate_configuration()

        # Provide sane default auth redirects if user didn't set them
        try:
            from django.conf import settings
            if not getattr(settings, 'LOGIN_REDIRECT_URL', None):
                settings.LOGIN_REDIRECT_URL = '/sys/'
            if not getattr(settings, 'LOGOUT_REDIRECT_URL', None):
                settings.LOGOUT_REDIRECT_URL = '/accounts/login/'
        except Exception:
            pass
        
        # Set Arabic verbose names for Auth app and Permission model
        try:
            from django.contrib.auth.models import Permission
            auth_config = apps.get_app_config('auth')
            auth_config.verbose_name = "نظام المصادقة" # "Auth" -> Identity/Authentication
            
            Permission.add_to_class("__str__", custom_permission_str)
            Permission._meta.verbose_name = "ادارة الصلاحيات"
            Permission._meta.verbose_name_plural = "الصلاحيات"
        except (LookupError, AttributeError):
            pass

        import microsys.signals
        import microsys.discovery

    def _validate_configuration(self):
        """Validate microsys configuration at startup and emit warnings."""
        import warnings
        from django.conf import settings

        # Check Middleware
        middleware_path = 'microsys.middleware.ActivityLogMiddleware'
        if middleware_path not in getattr(settings, 'MIDDLEWARE', []):
            warnings.warn(
                f"\n⚠️  microsys: '{middleware_path}' not found in MIDDLEWARE.\n"
                "   Activity logging will not work. Run 'python manage.py microsys_check' for details.",
                UserWarning
            )

        # Check Context Processors
        context_proc = 'microsys.context_processors.microsys_context'
        context_ok = False
        try:
            for template in getattr(settings, 'TEMPLATES', []):
                processors = template.get('OPTIONS', {}).get('context_processors', [])
                if context_proc in processors:
                    context_ok = True
                    break
        except (AttributeError, TypeError):
            pass

        if not context_ok:
            warnings.warn(
                f"\n⚠️  microsys: '{context_proc}' not found in TEMPLATES context_processors.\n"
                "   Sidebar and branding will not work. Run 'python manage.py microsys_check' for details.",
                UserWarning
            )
