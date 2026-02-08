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
    verbose_name = "النظام"

    def ready(self):
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

