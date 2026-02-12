# Imports of the required python modules and libraries
######################################################
from django.db import models
from django.conf import settings
from .managers import ScopedManager


class Scope(models.Model):
    name = models.CharField(max_length=100, verbose_name="النطاق")

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "نطاق"
        verbose_name_plural = "النطاقات"


class ScopeSettings(models.Model):
    is_enabled = models.BooleanField(default=False, verbose_name="تفعيل النطاقات")

    class Meta:
        verbose_name = "إعدادات النطاق"
        verbose_name_plural = "إعدادات النطاق"

    def save(self, *args, **kwargs):
        self.pk = 1
        super(ScopeSettings, self).save(*args, **kwargs)

    @classmethod
    def load(cls):
        obj, created = cls.objects.get_or_create(pk=1)
        return obj

    def __str__(self):
        return "إعدادات النطاق"


class ScopeForeignKey(models.ForeignKey):
    """
    ForeignKey that hides itself from ModelForms when scopes are disabled.
    Keeps schema identical to a normal ForeignKey.
    """

    def formfield(self, **kwargs):
        try:
            from .utils import is_scope_enabled
            if not is_scope_enabled():
                return None
        except Exception:
            pass
        return super().formfield(**kwargs)

    def deconstruct(self):
        name, path, args, kwargs = super().deconstruct()
        # Treat as a normal ForeignKey in migrations to avoid churn.
        path = "django.db.models.ForeignKey"
        return name, path, args, kwargs


class ScopedModel(models.Model):
    """
    Abstract base class for models that should be isolated by Scope.
    """
    scope = ScopeForeignKey('microsys.Scope', on_delete=models.PROTECT, null=True, blank=True, verbose_name="النطاق")
    
    objects = ScopedManager()
    all_objects = models.Manager()

    class Meta:
        abstract = True


class Profile(ScopedModel):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='profile', verbose_name="المستخدم")
    phone = models.CharField(max_length=15, blank=True, null=True, verbose_name="رقم الهاتف")
    profile_picture = models.ImageField(upload_to='profile_pictures/', null=True, blank=True)
    deleted_at = models.DateTimeField(null=True, blank=True, verbose_name="تاريخ الحذف")

    @property
    def full_name(self):
        return f"{self.user.first_name} {self.user.last_name}".strip()

    def __str__(self):
        return self.user.username

    class Meta:
        verbose_name = "ملف المستخدم"
        verbose_name_plural = "ملفات المستخدمين"
        permissions = [
            ("manage_staff", "صلاحيات مستخدم مسؤول"),
        ]


class UserActivityLog(ScopedModel):
    ACTION_TYPES = [
        ('LOGIN', 'تسجيل دخـول'),
        ('LOGOUT', 'تسجيل خـروج'),
        ('CREATE', 'انشـاء'),
        ('UPDATE', 'تعديـل'),
        ('DELETE', 'حــذف'),
        ('VIEW', 'عـرض'),
        ('DOWNLOAD', 'تحميل'),
        ('CONFIRM', 'تأكيـد'),
        ('REJECT', 'رفــض'),
        ('RESET', 'اعادة ضبط'),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, verbose_name="اسم المستخدم", null=True, blank=True)
    action = models.CharField(max_length=10, choices=ACTION_TYPES, verbose_name="العملية")
    model_name = models.CharField(max_length=100, blank=True, null=True, verbose_name="القسم")
    object_id = models.IntegerField(blank=True, null=True, verbose_name="ID")
    number = models.CharField(max_length=50, null=True, blank=True, verbose_name="المستند")
    ip_address = models.GenericIPAddressField(blank=True, null=True, verbose_name="عنوان IP")
    user_agent = models.TextField(blank=True, null=True, verbose_name="agent")
    timestamp = models.DateTimeField(auto_now_add=True, verbose_name="الوقت")

    def __str__(self):
        return f"{self.user} {self.action} {self.model_name or 'General'} at {self.timestamp}"

    class Meta:
        verbose_name = "حركة سجل"
        verbose_name_plural = "حركات السجل"
        permissions = [
            ("view_activity_log", "عرض سجل النشاط"),
        ]

class Section(models.Model):
    """Dummy Model for section permissions."""
    class Meta:
        managed = False
        default_permissions = ()
        permissions = [
            ("view_sections", "عرض الاقسام"),
            ("manage_sections", "إدارة الاقسام"),
        ]
