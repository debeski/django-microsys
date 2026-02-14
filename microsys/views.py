# Fundemental imports
######################################################
import json
from django.utils import timezone
from django.contrib import messages
from django.contrib.auth import get_user_model, update_session_auth_hash, login, authenticate
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.http import HttpResponseForbidden, JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django_tables2 import RequestConfig, SingleTableView, SingleTableMixin
from django_filters.views import FilterView
from django.views.generic.detail import DetailView
from django.apps import apps
from django.utils.module_loading import import_string
from django.contrib.auth.views import LoginView
from django.conf import settings
from django.template.loader import render_to_string
import os
import re
import json
import urllib.request
import psutil
import platform
import sys
import django
import inspect
from django.urls import reverse
from django import forms
from django.core.exceptions import FieldDoesNotExist
from django.db import models as dj_models
from django.db.models import ManyToManyField, Count, ProtectedError
from django.db.models.functions import TruncHour
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Submit

# Project imports
#################

from .signals import get_client_ip
from .tables import UserTable
from .forms import CustomUserCreationForm, CustomUserChangeForm, CustomPasswordChangeForm, ResetPasswordForm, UserProfileEditForm
from .filters import UserFilter
from .utils import is_scope_enabled, discover_section_models, resolve_model_by_name, resolve_form_class_for_model, has_related_records, collect_related_objects, _get_request_translations
from .translations import get_strings

User = get_user_model() # Use custom user model




def _get_m2m_through_defaults(model, field_name, request):
    """
    Provide through_defaults for M2M relations when the through model is scoped.
    This prevents relations from disappearing when scope filtering is enabled.
    """
    try:
        field = model._meta.get_field(field_name)
    except FieldDoesNotExist:
        return None

    # Only M2M fields can have through tables
    if not getattr(field, "many_to_many", False):
        return None

    through = field.remote_field.through
    if not through:
        return None

    defaults = {}
    if is_scope_enabled():
        # Resolve scope from profile first, then direct user attribute
        scope = None
        if hasattr(request.user, 'profile') and getattr(request.user.profile, 'scope', None):
            scope = request.user.profile.scope
        elif hasattr(request.user, 'scope') and getattr(request.user, 'scope', None):
            scope = request.user.scope
        if scope:
            try:
                through._meta.get_field('scope')
                defaults['scope'] = scope
            except Exception:
                pass

    return defaults or None

def _create_minimal_instance_from_post(model, data, request):
    """
    Fallback: create a minimal instance from POST data when a simple
    inline add is used (e.g., just a `name` field).
    Only proceeds if all required concrete fields are present.
    """
    field_map = {}
    missing_required = []

    # Identify truly required fields (skip auto-managed and optional ones)
    for field in model._meta.fields:
        if field.primary_key or field.auto_created:
            continue
        if getattr(field, "auto_now", False) or getattr(field, "auto_now_add", False):
            continue
        if field.has_default() or field.blank or field.null:
            continue

        if field.name not in data:
            missing_required.append(field.name)

    if missing_required:
        return None, missing_required

    for field in model._meta.fields:
        if field.primary_key or field.auto_created:
            continue
        if field.name in data:
            if isinstance(field, dj_models.ForeignKey):
                try:
                    field_map[field.name] = field.remote_field.model.objects.get(pk=data[field.name])
                except Exception:
                    return None, [field.name]
            else:
                field_map[field.name] = data[field.name]

    instance = model(**field_map)
    if hasattr(instance, 'created_by'):
        instance.created_by = request.user
    # Ensure scope is set for scoped models
    if is_scope_enabled() and hasattr(instance, 'scope'):
        try:
            user_scope = getattr(getattr(request.user, 'profile', None), 'scope', None)
            if not user_scope and hasattr(request.user, 'scope'):
                user_scope = request.user.scope
            # Non-superusers always get their scope forced; superusers only if unset
            if user_scope:
                if not request.user.is_superuser:
                    instance.scope = user_scope
                elif not getattr(instance, 'scope', None):
                    instance.scope = user_scope
        except Exception:
            pass
    instance.save()
    return instance, []

# Helper Function to log actions
def log_user_action(request, instance, action, model_name):
    UserActivityLog = apps.get_model('microsys', 'UserActivityLog')
    UserActivityLog.objects.create(
        user=request.user,
        action=action,
        model_name=model_name,
        object_id=instance.pk,
        number=instance.number if hasattr(instance, 'number') else '',
        timestamp=timezone.now(),
        ip_address=get_client_ip(request),
        user_agent=request.META.get("HTTP_USER_AGENT", ""),
    )

#####################################################################

# Index/Dashboard View
@login_required
def dashboard(request):
    """
    Dashboard/Landing page that reflects dynamic branding.
    """
    # Prepare Activity Chart Data
    UserActivityLog = apps.get_model('microsys', 'UserActivityLog')
    now = timezone.now()
    
    # 1. Last 24 Hours (Group by Hour)
    last_24h = now - timezone.timedelta(hours=24)
    activity_24h = UserActivityLog.objects.filter(timestamp__gte=last_24h) \
        .annotate(hour=TruncHour('timestamp')) \
        .values('hour') \
        .annotate(count=Count('id')) \
        .order_by('hour')
    
    data_24h_labels = [entry['hour'].strftime('%H:00') for entry in activity_24h]
    data_24h_values = [entry['count'] for entry in activity_24h]

    context = {
        'current_time': now,
        'chart_data': {
            'last_24h': json.dumps({'labels': data_24h_labels, 'values': data_24h_values}),
        }
    }
    return render(request, 'microsys/includes/dashboard.html', context)

# Custom Login View with Theme Injection
class CustomLoginView(LoginView):
    redirect_authenticated_user = True  # Automatically redirect logged-in users
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # 1. Check for manual language switch via GET param
        lang_param = self.request.GET.get('lang')
        
        # Only set if provided (the helper will read it from session automatically)
        if lang_param in ['ar', 'en']:
            self.request.session['lang'] = lang_param
            
        # 2. Use the smart helper (now handles session automatically)
        context['MS_TRANS'] = _get_request_translations(self.request)

        return context

    def get_success_url(self):
        """
        Overwrite default redirect to use 'sys_dashboard' (or custom config home_url)
        if no 'next' param is provided and LOGIN_REDIRECT_URL is the default.
        """
        # 1. Check for 'next' parameter (standard behavior)
        url = self.get_redirect_url()
        if url:
            return url
            
        # 2. Check if project settings have a custom redirect URL
        # The default Django value is '/accounts/profile/'
        project_redirect = getattr(settings, 'LOGIN_REDIRECT_URL', '/accounts/profile/')
        
        if project_redirect == '/accounts/profile/':
             # If it's the default, override it.
             ms_config = getattr(settings, 'MICROSYS_CONFIG', {})
             home_url = ms_config.get('home_url')
             
             if home_url:
                 from django.shortcuts import resolve_url
                 try:
                     return resolve_url(home_url)
                 except:
                     return home_url

             # Fallback to default dashboard
             from django.urls import reverse_lazy
             return reverse_lazy('sys_dashboard')
        
        # 3. Otherwise use the project setting
        return super().get_success_url()


# Function to recognize staff
def is_staff(user):
    return user.is_staff


# Function to recognize superuser
def is_superuser(user):
    return user.is_superuser 


# Class Function for managing users
class UserListView(LoginRequiredMixin, UserPassesTestMixin, FilterView, SingleTableView):
    model = User
    table_class = UserTable
    filterset_class = UserFilter  # Set the filter class to apply filtering
    template_name = "microsys/users/manage_users.html"
    paginate_by = 10
    
    # Restrict access to only staff users
    def test_func(self):
        return self.request.user.is_staff

    
    def get_queryset(self):
        # Apply the filter and order by any logic you need
        qs = super().get_queryset().order_by('date_joined')
        # Exclude soft-deleted users by checking profile's deleted_at
        qs = qs.filter(profile__deleted_at__isnull=True)
        
        # Hide superuser entries from non-superusers
        if not self.request.user.is_superuser:
            qs = qs.exclude(is_superuser=True)
            # Restrict to same scope
            if hasattr(self.request.user, 'profile') and self.request.user.profile.scope:
                qs = qs.filter(profile__scope=self.request.user.profile.scope)
        return qs

    def get_table_kwargs(self):
        kwargs = super().get_table_kwargs()
        kwargs['translations'] = _get_request_translations(self.request)
        kwargs['request'] = self.request
        return kwargs

    def get_table(self, **kwargs):
        table = super().get_table(**kwargs)
        # Hide scope column when scopes are off, or when user is already scoped
        if not is_scope_enabled():
            table.exclude = ('scope',)
        elif hasattr(self.request.user, 'profile') and self.request.user.profile.scope and not self.request.user.is_superuser:
            table.exclude = ('scope',)
        return table

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user_filter = self.get_filterset(self.filterset_class)
        scope_enabled = is_scope_enabled()
        
        context["filter"] = user_filter
        context["users"] = user_filter.qs
        context["scope_enabled"] = scope_enabled
        
        # Disabling scopes is only safe if no users are currently assigned to any scope
        can_toggle_scope = True
        if scope_enabled:
            can_toggle_scope = not User.objects.filter(profile__scope__isnull=False).exists()
        
        context["can_toggle_scope"] = can_toggle_scope

        # Add Reset Password Form for Modal (Dummy user to generate fields)
        if self.request.user.is_authenticated:
            context["form_reset"] = ResetPasswordForm(user=self.request.user)
            
        return context


# Function for creating a new User
@user_passes_test(is_staff)
def create_user(request):
    if request.method == "POST":
        form = CustomUserCreationForm(request.POST or None, user=request.user)
        if form.is_valid():
            user = form.save(commit=False)
            # Auto-assign scope for non-superusers
            if not request.user.is_superuser and hasattr(request.user, 'profile') and request.user.profile.scope:
                # This logic is handled inside form.save via passed params.
                pass 
                
            user = form.save() # Saves user + profile
            return redirect("manage_users")
        else:
            return render(request, "microsys/users/user_form.html", {"form": form})
    else:
        form = CustomUserCreationForm(user=request.user)
    
    return render(request, "microsys/users/user_form.html", {"form": form})


# Function for editing an existing User
@user_passes_test(is_staff)
def edit_user(request, pk):
    user = get_object_or_404(User, pk=pk)
    # 🚫 Superusers can only be edited by THEMSELVES
    if user.is_superuser and request.user != user:
        messages.error(request, "ليس لديك صلاحية لتعديل هذا الحساب!")
        return redirect('manage_users')


    # Restrict to same scope
    if not request.user.is_superuser:
        user_scope = user.profile.scope if hasattr(user, 'profile') else None
        requester_scope = request.user.profile.scope if hasattr(request.user, 'profile') else None
        
        if requester_scope and user_scope != requester_scope:
             messages.error(request, "ليس لديك صلاحية لتعديل هذا المستخدم!")
             return redirect('manage_users')

    form_reset = ResetPasswordForm(user, data=request.POST or None)

    if request.method == "POST":
        form = CustomUserChangeForm(request.POST, instance=user, user=request.user)
        if form.is_valid():
            user = form.save() # Saves user + profile
            return redirect("manage_users")
        else:
            # Validation errors will be automatically handled by the form object
            return render(request, "microsys/users/user_form.html", {"form": form, "edit_mode": True, "form_reset": form_reset})

    else:
        form = CustomUserChangeForm(instance=user, user=request.user)

    return render(request, "microsys/users/user_form.html", {"form": form, "edit_mode": True, "form_reset": form_reset})


# Function for deleting a User
@user_passes_test(is_superuser)
def delete_user(request, pk):
    user = get_object_or_404(User, pk=pk)

    # Prevent deletion of any superuser
    if user.is_superuser:
        messages.error(request, "لا يمكن حذف المشرف الرئيسي للنظام!")
        return redirect('manage_users')

    # Restrict to same scope
    if not request.user.is_superuser:
        user_scope = user.profile.scope if hasattr(user, 'profile') else None
        requester_scope = request.user.profile.scope if hasattr(request.user, 'profile') else None
        if requester_scope and user_scope != requester_scope:
             messages.error(request, "ليس لديك صلاحية لحذف هذا المستخدم!")
             return redirect('manage_users')

    if request.method == "POST":
        # Capture original username for logging
        original_username = user.username
        
        # Soft delete the user
        user.is_active = False
        user.skip_signal_logging = True # Prevent "UPDATE" log
        user.save()
        
        # Set deleted_at on profile
        Profile = apps.get_model('microsys', 'Profile')
        # Use all_objects to include already-deleted profiles
        profile, created = Profile.all_objects.get_or_create(user=user)
        profile.deleted_at = timezone.now()
        profile.save()
        
        # Rename username to free it for reuse (e.g. admin -> admin_del, admin_del2)
        base_username = f"{user.username}_del"
        new_username = base_username
        counter = 2
        
        # Check if username_del already exists, increment if needed
        while User.objects.filter(username=new_username).exists():
            new_username = f"{base_username}{counter}"
            counter += 1
        
        user.username = new_username
        user.skip_signal_logging = True # Prevent "UPDATE" log for rename
        user.save()

        # Manually Log the Delete Action with original username
        UserActivityLog = apps.get_model('microsys', 'UserActivityLog')
        UserActivityLog.objects.create(
            user=request.user,
            action="DELETE",
            model_name="User", # Or user._meta.verbose_name
            object_id=user.pk,
            number=original_username, # Use original username here!
            timestamp=timezone.now(),
            ip_address=get_client_ip(request),
            user_agent=request.META.get("HTTP_USER_AGENT", ""),
        )

        return redirect("manage_users")
    return redirect("manage_users")  # Redirect instead of rendering a separate page


# Class Function for the Log
class UserActivityLogView(LoginRequiredMixin, UserPassesTestMixin, SingleTableMixin, FilterView):
    model = apps.get_model('microsys', 'UserActivityLog')
    table_class = import_string('microsys.tables.UserActivityLogTable')
    filterset_class = import_string('microsys.filters.UserActivityLogFilter')
    template_name = "microsys/users/user_activity_log.html"

    def test_func(self):
        return self.request.user.is_staff  # Only staff can access logs
    
    def get_queryset(self):
        # Order by timestamp descending by default
        qs = super().get_queryset().order_by('-timestamp')
        # When scopes are disabled, defer the scope column to avoid loading unused data
        if not is_scope_enabled():
            try:
                self.model._meta.get_field('scope')
                qs = qs.defer('scope')
            except FieldDoesNotExist:
                pass
        if not self.request.user.is_superuser:
            qs = qs.exclude(user__is_superuser=True)
            if hasattr(self.request.user, 'profile') and self.request.user.profile.scope:
                qs = qs.filter(user__profile__scope=self.request.user.profile.scope)
        return qs

    def get_table(self, **kwargs):
        table = super().get_table(**kwargs)
        if not is_scope_enabled():
            table.exclude = ('scope',)
        elif hasattr(self.request.user, 'profile') and self.request.user.profile.scope:
            table.exclude = ('scope',)
        return table

    def get_table_kwargs(self):
        kwargs = super().get_table_kwargs()
        kwargs['translations'] = _get_request_translations(self.request)
        kwargs['request'] = self.request
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Handle the filter object
        context['filter'] = self.filterset
        return context


class UserDetailView(LoginRequiredMixin, UserPassesTestMixin, DetailView):
    model = User
    template_name = "microsys/users/user_detail.html"

    def test_func(self):
        # only staff can view user detail page
        return self.request.user.is_staff

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # self.object is the User instance
        UserActivityLog = apps.get_model('microsys', 'UserActivityLog')
        logs_qs = UserActivityLog.objects.filter(user=self.object).order_by('-timestamp')
        
        # Create table manually
        UserActivityLogTableNoUser = import_string('microsys.tables.UserActivityLogTableNoUser')
        table = UserActivityLogTableNoUser(logs_qs, translations=_get_request_translations(self.request))
        RequestConfig(self.request, paginate={'per_page': 10}).configure(table)
        
        context['table'] = table
        return context


# Function that resets a user password
@user_passes_test(is_staff)
def reset_password(request, pk):
    user = get_object_or_404(User, id=pk)

    # 🚫 Superusers can only have their password reset by THEMSELVES
    if user.is_superuser and request.user != user:
        messages.error(request, "ليس لديك صلاحية لتعديل هذا الحساب!")
        return redirect('manage_users')

    # Restrict to same scope
    if not request.user.is_superuser:
        user_scope = user.profile.scope if hasattr(user, 'profile') else None
        requester_scope = request.user.profile.scope if hasattr(request.user, 'profile') else None
        if requester_scope and user_scope != requester_scope:
             messages.error(request, "ليس لديك صلاحية لتعديل هذا المستخدم!")
             return redirect('manage_users')

    if request.method == "POST":
        form = ResetPasswordForm(user=user, data=request.POST)  # ✅ Correct usage with SetPasswordForm
        if form.is_valid():
            form.save()
            log_user_action(request, user, "RESET", "password")
            return redirect("manage_users")
        else:
            print("Form errors:", form.errors)
            return redirect("edit_user", pk=pk)
    
    return redirect("manage_users")  # Fallback redirect


# API for updating user preferences
@login_required
def update_preferences(request):
    if request.method == "POST":
        import json
        try:
             # Support both JSON body and Form data
            if request.content_type == 'application/json':
                data = json.loads(request.body)
            else:
                data = request.POST

            # 1. Get or create profile
            Profile = apps.get_model('microsys', 'Profile')
            profile, created = Profile.all_objects.get_or_create(user=request.user)

            # 2. Get existing prefs safely
            current_prefs = profile.preferences
            if not isinstance(current_prefs, dict):
                if isinstance(current_prefs, str) and current_prefs.strip():
                    try:
                        current_prefs = json.loads(current_prefs)
                    except:
                        current_prefs = {}
                else:
                    current_prefs = {}
            
            # Start with a clean dict for merging
            prefs = dict(current_prefs)
            
            # 3. Update with new data
            import logging
            logger = logging.getLogger('microsys')
            
            for key, value in data.items():
                if key != 'csrfmiddlewaretoken':
                    prefs[key] = value
                    
                    # Sync sidebar state to session for server-side consistency
                    if key == 'sidebar_collapsed':
                         val = value
                         if isinstance(val, str):
                             val = val.lower() == 'true'
                         request.session['sidebarCollapsed'] = val

            # 4. Save
            profile.preferences = prefs
            profile.save(update_fields=['preferences'])
            request.session.modified = True
            
            logger.debug(f"Preferences updated for {request.user.username}: {prefs}")
            return JsonResponse({'status': 'success', 'preferences': profile.preferences})
        except Exception as e:
            import logging
            error_msg = f"Error updating preferences for {request.user.username}: {str(e)}"
            logging.getLogger('microsys').error(error_msg)
            return JsonResponse({'status': 'error', 'message': error_msg}, status=400)
    return JsonResponse({'status': 'error', 'message': 'Invalid method'}, status=405)


# Function for the user profile
@login_required
def user_profile(request):
    user = request.user
    
    # Use dynamic form
    password_form = CustomPasswordChangeForm(user)
    
    if request.method == 'POST':
        password_form = CustomPasswordChangeForm(user, request.POST)
        if password_form.is_valid():
            password_form.save()
            log_user_action(request, user, "UPDATE", "password")
            update_session_auth_hash(request, password_form.user)  # Prevent user from being logged out
            
            # Translated success message
            s = _get_request_translations(request)
            messages.success(request, s.get('msg_password_changed', 'Password changed successfully!'))
            
            return redirect('user_profile')
        else:
            # Log form errors
            s = _get_request_translations(request)
            messages.error(request, s.get('msg_form_error', "There was an error with the submitted data"))
            print(password_form.errors)

    return render(request, 'microsys/profile/profile.html', {
        'user': user,
        'password_form': password_form
    })


# Function for editing the user profile
@login_required
def edit_profile(request):
    if request.method == 'POST':
        form = UserProfileEditForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            user = form.save()
            log_user_action(request, user, "UPDATE", "profile")
            messages.success(request, 'تم حفظ التغييرات بنجاح')
            return redirect('user_profile')
        else:
            messages.error(request, 'حدث خطأ أثناء حفظ التغييرات')
    else:
        form = UserProfileEditForm(instance=request.user)
    return render(request, 'microsys/profile/profile_edit.html', {'form': form})


# Scope Management Views
# ###########################
@login_required
@user_passes_test(is_superuser)
def manage_scopes(request):
    """
    Returns the initial modal content with the table.
    """
    if not is_scope_enabled():
         return JsonResponse({'error': 'Scope management is disabled.'}, status=403)

    Scope = apps.get_model('microsys', 'Scope')
    ScopeTable = import_string('microsys.tables.ScopeTable')
    table = ScopeTable(Scope.objects.all())
    RequestConfig(request, paginate={'per_page': 5}).configure(table)
    
    context = {'table': table}
    html = render_to_string('microsys/scopes/scope_manager.html', context, request=request)
    return JsonResponse({'html': html})

@login_required
@user_passes_test(is_superuser)
def get_scope_form(request, pk=None):
    """
    Returns the Add/Edit form partial.
    """
    ScopeForm = import_string('microsys.forms.ScopeForm')
    Scope = apps.get_model('microsys', 'Scope')

    if pk:
        scope = get_object_or_404(Scope, pk=pk)
        form = ScopeForm(instance=scope)
    else:
        form = ScopeForm()
        
    html = render_to_string('microsys/scopes/scope_form.html', {'form': form, 'scope_id': pk}, request=request)
    return JsonResponse({'html': html})

@login_required
@user_passes_test(is_superuser)
def save_scope(request, pk=None):
    """
    Handles form submission. Returns updated table on success, or form with errors on failure.
    """
    ScopeForm = import_string('microsys.forms.ScopeForm')
    Scope = apps.get_model('microsys', 'Scope')
    ScopeTable = import_string('microsys.tables.ScopeTable')

    if request.method == "POST":
        if pk:
            scope = get_object_or_404(Scope, pk=pk)
            form = ScopeForm(request.POST, instance=scope)
        else:
            form = ScopeForm(request.POST)

        if form.is_valid():
            form.save()
            # Return updated table
            table = ScopeTable(Scope.objects.all())
            RequestConfig(request, paginate={'per_page': 5}).configure(table)
            html = render_to_string('microsys/scopes/scope_manager.html', {'table': table}, request=request)
            return JsonResponse({'success': True, 'html': html})
        else:
            # Return form with errors
            html = render_to_string('microsys/scopes/scope_form.html', {'form': form, 'scope_id': pk}, request=request)
            return JsonResponse({'success': False, 'html': html})
    
    return JsonResponse({'success': False, 'error': 'Invalid method'})

@login_required
@user_passes_test(is_superuser)
def delete_scope(request, pk):
    return JsonResponse({'success': False, 'error': 'تم تعطيل حذف النطاقات لأسباب أمنية.'})

@login_required
@user_passes_test(is_superuser)
def toggle_scopes(request):
    if request.method == "POST":
        import json
        ScopeSettings = apps.get_model('microsys', 'ScopeSettings')
        settings = ScopeSettings.load()
        
        # Get explicit target state from POST body (prevents race conditions)
        target_enabled = None
        try:
            body = json.loads(request.body)
            target_enabled = body.get('target_enabled')
        except (json.JSONDecodeError, ValueError):
            pass
        
        # If no explicit state was sent, invert the current state
        if target_enabled is None:
            target_enabled = not settings.is_enabled
        
        # Safety Check: Prevent disabling if users are assigned to scopes
        if settings.is_enabled and not target_enabled:
            if User.objects.filter(profile__scope__isnull=False).exists():
                return JsonResponse({
                    'success': False, 
                    'error': 'لا يمكن تعطيل النطاقات لوجود مستخدمين معينين لنطاقات حالية. يرجى إزالة النطاقات من كافة المستخدمين أولاً.'
                }, status=200)
        
        settings.is_enabled = target_enabled
        settings.save()
        log_user_action(request, request.user, "UPDATE", "scope_settings")
        return JsonResponse({'success': True, 'is_enabled': settings.is_enabled})
    return JsonResponse({'success': False}, status=400)


# Section Management Views
# ###########################
# Dynamic View and CRUD function for section and subsection models
@login_required
def core_models_view(request):
    """
    Manages section models dynamically discovered from the app.
    Uses ?model= query param with session fallback for tab persistence.
    """
    # Discover section models dynamically
    section_models = discover_section_models(app_name=None, include_children=False)
    
    # Build map for easy lookup
    models_map = {sm['model_name']: sm for sm in section_models}
    
    # Get model from query param or session fallback
    default_model = section_models[0]['model_name'] if section_models else None
    model_param = request.GET.get('model') or request.session.get('last_active_model', default_model)
    
    # Fallback to first discovered model if invalid
    if model_param not in models_map:
        model_param = default_model
    
    if not model_param or not models_map:
        return render(request, 'microsys/sections/manage_sections.html', {
            'error': 'لا توجد موديلات متاحة.',
        })
    
    # Store in session only when user explicitly changes tab via GET param
    if request.GET.get('model'):
        request.session['last_active_model'] = model_param
    
    selected_data = models_map[model_param]
    selected_model = selected_data['model']
    
    # Get classes from discovery result
    FormClass = selected_data['form_class']
    TableClass = selected_data['table_class']
    FilterClass = selected_data['filter_class']
    
    if not FormClass or not TableClass:
        return render(request, 'microsys/sections/manage_sections.html', {
            'error': 'هناك خطأ في تحميل المودل.',
            'active_model': model_param,
            'models': [{'name': sm['model_name'], 'ar_names': sm['verbose_name_plural'], 'count': sm['model'].objects.count()} for sm in section_models],
        })
    
    # Check for edit mode
    instance_id = request.GET.get('id')
    instance = None
    if instance_id:
        try:
            instance = selected_model.objects.get(pk=instance_id)
        except selected_model.DoesNotExist:
            instance = None

    # Build a cancel URL that preserves current filters/sort but drops the edit ID
    cancel_url = None
    if 'id' in request.GET:
        params = request.GET.copy()
        params.pop('id', None)
        cancel_url = reverse('manage_sections')
        if params:
            cancel_url = f"{cancel_url}?{params.urlencode()}"
    
    subsection_field_names = set()

    # Create form
    form = FormClass(request.POST or None, instance=instance)
    # Auto-create a crispy helper if the form doesn't define one (marks it for layout generation later)
    if not hasattr(form, "helper") or form.helper is None:
        form.helper = FormHelper()
        form.helper.form_tag = False
        form._auto_helper = True
    else:
        form.helper.form_tag = False
        if not getattr(form.helper, "inputs", None):
            form.helper.add_input(Submit("submit", "حفظ", css_class="btn btn-primary rounded-pill"))

    user_scope = None
    if hasattr(request.user, 'profile') and getattr(request.user.profile, 'scope', None):
        user_scope = request.user.profile.scope
    elif hasattr(request.user, 'scope') and getattr(request.user, 'scope', None):
        user_scope = request.user.scope

    if is_scope_enabled() and user_scope and not request.user.is_superuser:
        scope_field = form.fields.get('scope')
        if scope_field:
            scope_field.initial = user_scope
            scope_field.disabled = True
            scope_field.widget = forms.HiddenInput()
            scope_field.required = False
    
    # Create filter and queryset
    queryset = selected_model.objects.all()
    filter_obj = None
    if FilterClass:
        filter_obj = FilterClass(request.GET or None, queryset=queryset)
        queryset = filter_obj.qs
    
    # Introspect table __init__ to see if it accepts model_name kwarg or **kwargs
    try:
        sig = inspect.signature(TableClass.__init__)
        params = sig.parameters
        accepts_model_name = (
            "model_name" in params
            or any(p.kind == p.VAR_KEYWORD for p in params.values())
        )
    except (TypeError, ValueError):
        accepts_model_name = False

    # Pass model_name to constructor if supported, otherwise inject it as an attribute
    translations = _get_request_translations(request)
    if accepts_model_name:
        table = TableClass(queryset, model_name=model_param, translations=translations, request=request)
    else:
        table = TableClass(queryset, translations=translations, request=request)
        if not hasattr(table, "model_name"):
            table.model_name = model_param
    RequestConfig(request, paginate={'per_page': 10}).configure(table)

    # Merge 'scope' into existing excludes without duplicates for scoped non-superusers
    if is_scope_enabled() and user_scope and not request.user.is_superuser:
        existing_exclude = getattr(table, "exclude", None) or ()
        merged = list(dict.fromkeys(list(existing_exclude) + ["scope"]))
        table.exclude = tuple(merged)
    
    # Handle Subsections (Child Models)
    subsection_forms = []
    subsection_selects = []
    for sub in selected_data.get('subsections', []):
        child_model_name = sub['model_name']
        related_field = sub['related_field']
        child_model = sub['model']

        if related_field not in form.fields:
            # Use the normal manager which applies scope filtering when enabled
            form.fields[related_field] = forms.ModelMultipleChoiceField(
                queryset=child_model.objects.all(),
                required=False,
                label=sub['verbose_name_plural'],
                widget=forms.CheckboxSelectMultiple(),
            )
        else:
            # Field exists - ensure it has the right queryset and widget
            form.fields[related_field].queryset = child_model.objects.all()
            form.fields[related_field].widget = forms.CheckboxSelectMultiple()
        
        # Sync widget choices with the field's queryset so CheckboxSelectMultiple renders correctly
        form.fields[related_field].widget.choices = form.fields[related_field].choices

        form.fields[related_field].modal_target = f"addSubsectionModal_{child_model_name}"

        if instance:
            try:
                rel_manager = getattr(instance, related_field, None)
                if rel_manager is not None:
                    form.fields[related_field].initial = list(
                        rel_manager.values_list('pk', flat=True)
                    )
            except Exception:
                pass

        # Determine which subsection items are "locked" (have dependencies elsewhere)
        locked_ids = []
        if instance:
            try:
                rel_manager = getattr(instance, related_field, None)
                if rel_manager is not None:
                    # Get the reverse accessor name so we can ignore the parent→child M2M itself
                    accessor = None
                    try:
                        field_obj = selected_model._meta.get_field(related_field)
                        accessor = field_obj.remote_field.get_accessor_name()
                    except Exception:
                        accessor = None

                    ignore = [accessor] if accessor else []
                    for child in rel_manager.all():
                        if has_related_records(child, ignore_relations=ignore):
                            locked_ids.append(str(child.pk))
            except Exception:
                locked_ids = []

        subsection_selects.append({
            'field': form[related_field],
            'locked_ids': locked_ids,
            'parent_model': model_param,
            'parent_id': instance.pk if instance else '',
            'parent_field': related_field,
            'child_model': child_model_name,
            'add_url': reverse('add_subsection'),
            'edit_url_template': reverse('edit_subsection', args=[0]).replace('/0/', '/{id}/'),
            'delete_url_template': reverse('delete_subsection', args=[0]).replace('/0/', '/{id}/'),
        })
        subsection_field_names.add(related_field)
        
        ChildForm = sub['form_class']
        child_form_instance = ChildForm()
        
        # Override form action to generic add_subsection view
        target_url = reverse('add_subsection')
        if not hasattr(child_form_instance, 'helper') or child_form_instance.helper is None:
             child_form_instance.helper = FormHelper()
             child_form_instance.helper.form_tag = True
        else:
             child_form_instance.helper.form_tag = True
        child_form_instance.helper.form_action = f"{target_url}?model={child_model_name}&parent={model_param}"
        if not getattr(child_form_instance.helper, "inputs", None):
             child_form_instance.helper.add_input(Submit("submit", "حفظ", css_class="btn btn-primary rounded-pill"))

        if is_scope_enabled() and user_scope and not request.user.is_superuser:
            child_scope_field = child_form_instance.fields.get('scope')
            if child_scope_field:
                child_scope_field.initial = user_scope
                child_scope_field.disabled = True
                child_scope_field.widget = forms.HiddenInput()
                child_scope_field.required = False
        
        subsection_forms.append({
            'name': child_model_name,
            'verbose_name': sub['verbose_name'],
            'form': child_form_instance
        })

    # Handle POST (after subsection fields are injected)
    if request.method == 'POST':
        if form.is_valid():
            saved_instance = form.save(commit=False)
            # Add created_by/updated_by if fields exist
            if hasattr(saved_instance, 'created_by') and not saved_instance.pk:
                saved_instance.created_by = request.user
            if hasattr(saved_instance, 'updated_by'):
                saved_instance.updated_by = request.user
            # Enforce scope for non-superusers with assigned scope
            if is_scope_enabled() and user_scope and not request.user.is_superuser and hasattr(saved_instance, 'scope'):
                saved_instance.scope = user_scope
            saved_instance.save()
            if hasattr(form, 'save_m2m'):
                form.save_m2m()
            # Manually set M2M subsection relations (with through_defaults for scoped through tables)
            for field_name in subsection_field_names:
                if field_name in form.cleaned_data:
                    try:
                        rel_manager = getattr(saved_instance, field_name)
                        through_defaults = _get_m2m_through_defaults(selected_model, field_name, request)
                        if through_defaults:
                            rel_manager.set(form.cleaned_data[field_name], through_defaults=through_defaults)
                        else:
                            rel_manager.set(form.cleaned_data[field_name])
                    except Exception:
                        pass
            return redirect('manage_sections')

    # For auto-generated helpers, build a custom 2-column layout with inline buttons
    if getattr(form, "_auto_helper", False):
        from crispy_forms.layout import Layout, Row, Column, Field, HTML, Div
        
        # Identify visible fields (excluding subsections which are handled separately)
        visible_fields = [
            f for f in form.fields 
            if f not in subsection_field_names 
            and not isinstance(form.fields[f].widget, forms.HiddenInput)
        ]
        
        layout_components = []
        
        # Add hidden fields first
        hidden_fields = [
            f for f in form.fields 
            if isinstance(form.fields[f].widget, forms.HiddenInput)
        ]
        for hf in hidden_fields:
            layout_components.append(Field(hf))
            
        # Helper to chunk fields
        def chunked(iterable, n):
            return [iterable[i:i + n] for i in range(0, len(iterable), n)]
            
        field_chunks = chunked(visible_fields, 2)
        total_chunks = len(field_chunks)
        
        for i, chunk in enumerate(field_chunks):
            is_last_chunk = (i == total_chunks - 1)
            
            if is_last_chunk:
                # Last chunk: Add fields + Buttons
                row_content = []
                for field_name in chunk:
                    row_content.append(Column(Field(field_name), css_class="col"))
                
                # Build Buttons HTML
                if cancel_url:
                    buttons_html = f"""
                    <div class="d-flex">
                        <button type="submit" class="btn btn-primary rounded-start-pill rounded-end-0">حفظ</button>
                        <a href="{cancel_url}" class="btn btn-outline-warning rounded-end-pill rounded-start-0">إلغاء</a>
                    </div>
                    """
                else:
                    buttons_html = '<button type="submit" class="btn btn-primary rounded-pill">حفظ</button>'
                
                row_content.append(
                    Column(
                        HTML(buttons_html), 
                        css_class="col-auto align-self-end mb-3"
                    )
                )
                layout_components.append(Row(*row_content))
            else:
                # Normal chunk: 2 columns
                row_content = [Column(Field(field_name), css_class="col-md-6") for field_name in chunk]
                layout_components.append(Row(*row_content))
                
        # If no visible fields but we have actions (rare edge case), just show buttons
        if not visible_fields:
            if cancel_url:
                buttons_html = f"""
                <div class="d-flex">
                    <button type="submit" class="btn btn-primary rounded-start-pill rounded-end-0">حفظ</button>
                    <a href="{cancel_url}" class="btn btn-outline-warning rounded-end-pill rounded-start-0">إلغاء</a>
                </div>
                """
            else:
                buttons_html = '<button type="submit" class="btn btn-primary rounded-pill">حفظ</button>'
            layout_components.append(Row(Column(HTML(buttons_html), css_class="col-auto")))

        form.helper.layout = Layout(*layout_components)

    # Build context
    context = {
        'active_model': model_param,
        'models': [
            {
                'name': sm['model_name'], 
                'ar_names': sm['verbose_name_plural'],
                'count': sm['model'].objects.count()
            } 
            for sm in section_models
        ],
        'form': form,
        'filter': filter_obj,
        'table': table,
        'id': instance_id,
        'form_has_submit': getattr(form, "_auto_helper", False),  # Flag to hide template buttons
        'show_cancel': 'id' in request.GET, # Kept for other uses if any
        'cancel_url': cancel_url,
        'ar_name': selected_data['verbose_name'],
        'ar_names': selected_data['verbose_name_plural'],
        'subsection_forms': subsection_forms, # subsection forms for modals (kept outside main form)
        'subsection_selects': subsection_selects,
        'has_subsections': len(subsection_selects) > 0,
    }
    
    return render(request, 'microsys/sections/manage_sections.html', context)

@login_required
def add_subsection(request):
    """
    Generic view to handle adding a new Subsection (child model) via modal.
    Expects ?model=child_model_name&parent=parent_model_name
    """
    child_model_name = request.GET.get('model')
    parent_model_name = request.GET.get('parent')
    parent_id = request.GET.get('parent_id')
    parent_field = request.GET.get('parent_field')
    
    if not child_model_name:
         messages.error(request, "معرف القسم الفرعي مفقود.")
         return redirect('manage_sections')

    # Resolve child model class
    model = resolve_model_by_name(child_model_name)
    if not model:
        messages.error(request, "القسم الفرعي غير موجود.")
        return redirect('manage_sections')
        
    # Resolve Form Class (consistent with discovery logic)
    form_class = resolve_form_class_for_model(model)
    
    if request.method == 'POST':
        form = form_class(request.POST)
        if form.is_valid():
            instance = form.save(commit=False)
            if hasattr(instance, 'created_by'):
                 instance.created_by = request.user
            # Ensure scope is set for scoped models
            if is_scope_enabled() and hasattr(instance, 'scope'):
                try:
                    user_scope = getattr(getattr(request.user, 'profile', None), 'scope', None)
                    if not user_scope and hasattr(request.user, 'scope'):
                        user_scope = request.user.scope
                    if user_scope:
                        if not request.user.is_superuser:
                            instance.scope = user_scope
                        elif not getattr(instance, 'scope', None):
                            instance.scope = user_scope
                except Exception:
                    pass
            instance.save()

            if parent_model_name and parent_id and parent_field:
                try:
                    parent_model = resolve_model_by_name(parent_model_name)
                    if parent_model:
                        parent_instance = parent_model.objects.get(pk=parent_id)
                        try:
                            rel_manager = getattr(parent_instance, parent_field)
                            through_defaults = _get_m2m_through_defaults(parent_model, parent_field, request)
                            if through_defaults:
                                rel_manager.add(instance, through_defaults=through_defaults)
                            else:
                                rel_manager.add(instance)
                        except Exception:
                            pass
                except Exception:
                    pass
            
            # AJAX Response
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({'success': True, 'id': instance.pk, 'name': str(instance)})
                
            messages.success(request, f"تم إضافة {model._meta.verbose_name}: {instance}")
        else:
            # Fallback: try creating from raw POST data if form validation fails (e.g. simple name-only models)
            instance, missing = _create_minimal_instance_from_post(model, request.POST, request)
            if instance:
                if parent_model_name and parent_id and parent_field:
                    try:
                        parent_model = resolve_model_by_name(parent_model_name)
                        if parent_model:
                            parent_instance = parent_model.objects.get(pk=parent_id)
                            try:
                                rel_manager = getattr(parent_instance, parent_field)
                                through_defaults = _get_m2m_through_defaults(parent_model, parent_field, request)
                                if through_defaults:
                                    rel_manager.add(instance, through_defaults=through_defaults)
                                else:
                                    rel_manager.add(instance)
                            except Exception:
                                pass
                    except Exception:
                        pass

                if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                    return JsonResponse({'success': True, 'id': instance.pk, 'name': str(instance)})
                messages.success(request, f"تم إضافة {model._meta.verbose_name}: {instance}")
            else:
                if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                     err = form.errors.as_text()
                     if missing:
                         err = f"Missing required fields: {', '.join(missing)}"
                     return JsonResponse({'success': False, 'error': err})
                messages.error(request, f"خطأ في إضافة {model._meta.verbose_name}.")
    
    # Redirect back to parent tab
    redirect_url = reverse('manage_sections')
    if parent_model_name:
        redirect_url += f"?model={parent_model_name}"
        
    return redirect(redirect_url)


@login_required
def edit_subsection(request, pk):
    """
    Edit a subsection (child model) by pk.
    Expects ?model=child_model_name&parent=parent_model_name
    """
    child_model_name = request.GET.get('model', 'subaffiliate')
    parent_model_name = request.GET.get('parent', 'affiliate')
    
    model = resolve_model_by_name(child_model_name)
    if not model:
        messages.error(request, "القسم الفرعي غير موجود.")
        return redirect('manage_sections')
    try:
        instance = model.objects.get(pk=pk)
    except model.DoesNotExist:
        messages.error(request, "القسم الفرعي غير موجود.")
        return redirect('manage_sections')
    
    # Resolve Form Class (consistent with discovery logic)
    form_class = resolve_form_class_for_model(model)
    
    if request.method == 'POST':
        form = form_class(request.POST, instance=instance)
        if form.is_valid():
            saved = form.save(commit=False)
            if hasattr(saved, 'updated_by'):
                saved.updated_by = request.user
            saved.save()
            
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({'success': True, 'id': saved.pk, 'name': str(saved)})
                
            messages.success(request, f"تم تعديل {model._meta.verbose_name}: {saved}")
        else:
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({'success': False, 'error': form.errors.as_text()})
            messages.error(request, f"خطأ في تعديل {model._meta.verbose_name}.")
    
    redirect_url = reverse('manage_sections')
    if parent_model_name:
        redirect_url += f"?model={parent_model_name}"
    return redirect(redirect_url)


@login_required
def delete_subsection(request, pk):
    """
    Delete a subsection (child model) by pk.
    Checks for related records before deletion.
    """    
    child_model_name = request.GET.get('model', 'subaffiliate')
    parent_model_name = request.GET.get('parent', 'affiliate')
    
    model = resolve_model_by_name(child_model_name)
    if not model:
        messages.error(request, "القسم الفرعي غير موجود.")
        return redirect('manage_sections')
    try:
        instance = model.objects.get(pk=pk)
    except model.DoesNotExist:
        messages.error(request, "القسم الفرعي غير موجود.")
        return redirect('manage_sections')
    
    if request.method == 'POST':
        # Check if locked (has related records)
        if has_related_records(instance, ignore_relations=['affiliates', 'affiliatedepartment_set']):
            messages.error(request, "لا يمكن حذف هذا العنصر لارتباطه بسجلات أخرى.")
        else:
            name = str(instance)
            instance.delete()
            messages.success(request, f"تم حذف {model._meta.verbose_name}: {name}")
    
    redirect_url = reverse('manage_sections')
    if parent_model_name:
        redirect_url += f"?model={parent_model_name}"
    return redirect(redirect_url)


@login_required
def delete_section(request):
    """
    Delete a section (main model) by pk via AJAX.
    Returns JSON response.
    """
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'طريقة غير مسموحة'}, status=405)
    
    try:
        data = json.loads(request.body)
        model_name = data.get('model')
        pk = data.get('pk')
    except (json.JSONDecodeError, ValueError):
        return JsonResponse({'success': False, 'error': 'بيانات غير صالحة'}, status=400)
    
    if not model_name or not pk:
        return JsonResponse({'success': False, 'error': 'معلومات ناقصة'}, status=400)
    
    model = resolve_model_by_name(model_name)
    if not model:
        return JsonResponse({'success': False, 'error': 'القسم غير موجود'}, status=404)
    
    try:
        instance = model.objects.get(pk=pk)
    except model.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'العنصر غير موجود'}, status=404)
    
    # Check if has related records (protect from deletion)
    # Use generic helper to find WHAT is related
    related_objects = collect_related_objects(instance)
    
    if related_objects:
        return JsonResponse({
            'success': False, 
            'error': 'لا يمكن حذف هذا العنصر لارتباطه بسجلات أخرى.',
            'related': related_objects # Structured dict of blocking items
        }, status=200)
    
    name = str(instance)
    try:
        instance.delete()
    except ProtectedError as e:
        # Fallback if collect_related_objects missed something
        return JsonResponse({
            'success': False, 
            'error': 'لا يمكن حذف هذا العنصر لارتباطه بسجلات محمية أخرى (لم يتم اكتشافها تلقائياً).',
            'details': str(e)
        }, status=200)
    except Exception as e:
        return JsonResponse({
            'success': False, 
            'error': f'حدث خطأ أثناء الحذف: {str(e)}'
        }, status=200)
    
    return JsonResponse({'success': True, 'message': f"تم حذف: {name}"})


@login_required
def get_section_details(request):
    """
    Get section details and related objects via AJAX (Smart View).
    Returns JSON with fields and related lists.
    """
    model_name = request.GET.get('model')
    pk = request.GET.get('pk')
    
    if not model_name or not pk:
        return JsonResponse({'success': False, 'error': 'معلومات ناقصة'}, status=400)
    
    model = resolve_model_by_name(model_name)
    if not model:
        return JsonResponse({'success': False, 'error': 'القسم غير موجود'}, status=404)
    
    try:
        instance = model.objects.get(pk=pk)
    except model.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'العنصر غير موجود'}, status=404)
    
    # 1. Collect Fields
    fields_data = {}
    exclude_fields = ['id', 'created_at', 'updated_at', 'scope', 'polymorphic_ctype', 'password']
    
    for field in model._meta.fields:
        if field.name not in exclude_fields:
            try:
                val = getattr(instance, field.name)
                # Handle choices
                if hasattr(instance, f"get_{field.name}_display"):
                     val = getattr(instance, f"get_{field.name}_display")()
                fields_data[field.verbose_name] = str(val) if val is not None else ""
            except:
                pass

    # 2. Collect Related Objects
    related_objects = collect_related_objects(instance)
    
    return JsonResponse({
        'success': True,
        'title': str(instance),
        'fields': fields_data,
        'related': related_objects
    })


# Options View
@login_required
def options_view(request):
    """
    View for system options, accessibility settings, and system info.
    Reads documented specs from README.md.
    """
    readme_path = os.path.join(settings.BASE_DIR, "README.md")
    readme_content = ""
    if os.path.exists(readme_path):
        try:
            with open(readme_path, "r", encoding="utf-8") as f:
                readme_content = f.read()
        except:
            pass

    # Helper to pull version strings from README using regex capture groups
    def extract_spec(pattern):
        match = re.search(pattern, readme_content)
        return match.group(1).strip() if match else "N/A"

    # API Health Check (Targeting project's own API via loopback)
    api_reachable = False
    api_error = ""
    try:
        # Hit the loopback address to verify the API is responding inside the container
        api_url = "http://127.0.0.1:8000/api/decrees/" 
        
        req = urllib.request.Request(api_url)
        req.add_header("X-API-KEY", getattr(settings, "X_API_KEY", ""))
        req.add_header("X-SECRET-KEY", getattr(settings, "X_SECRET_KEY", ""))
        
        with urllib.request.urlopen(req, timeout=3) as response:
            if response.status == 200:
                api_reachable = True
            else:
                api_error = f"Status: {response.status}"
    except Exception as e:
        api_reachable = False
        api_error = str(e)

    # System Stats
    try:
        # RAM
        mem = psutil.virtual_memory()
        ram_total_gb = mem.total / (1024 ** 3)
        ram_used_gb = mem.used / (1024 ** 3)
        ram_percent = mem.percent
        
        # Disk
        disk = psutil.disk_usage('/')
        disk_total_gb = disk.total / (1024 ** 3)
        disk_used_gb = disk.used / (1024 ** 3)
        disk_percent = disk.percent
    except Exception as e:
        ram_total_gb = ram_used_gb = ram_percent = 0
        disk_total_gb = disk_used_gb = disk_percent = 0

    context = {
        'current_time': timezone.now(),
        'os_info': f"{platform.system()} {platform.release()}",
        'python_version': sys.version.split()[0],
        'django_version': django.get_version(),
        'api_reachable': api_reachable,
        'api_error': api_error,
        'db_info': extract_spec(r'PostgreSQL ([\d.]+)'),
        'redis_info': extract_spec(r'Redis ([\d.]+)'),
        'celery_info': extract_spec(r'Celery ([\d.]+)'),
        'version': settings.VERSION,
        
        # System Stats
        'ram_total': f"{ram_total_gb:.1f}",
        'ram_used': f"{ram_used_gb:.1f}",
        'ram_percent': ram_percent,
        'disk_total': f"{disk_total_gb:.1f}",
        'disk_used': f"{disk_used_gb:.1f}",
        'disk_percent': disk_percent,
    }
    return render(request, 'microsys/includes/options.html', context)
@login_required
def reset_preferences(request):
    """
    Reset all user preferences to default.
    Clears Profile.preferences and session keys.
    """
    if request.method == "POST":
        try:
            # 1. Clear Profile preferences
            Profile = apps.get_model('microsys', 'Profile')
            profile, created = Profile.all_objects.get_or_create(user=request.user)
            profile.preferences = {}
            profile.save()
            
            # 2. Clear Session keys related to preferences
            session_keys_to_clear = ['django_language', 'sidebarCollapsed', 'enable_prefill']
            for key in session_keys_to_clear:
                if key in request.session:
                    del request.session[key]
            
            # Log action
            log_user_action(request, request.user, "RESET", "preferences")
            
            return JsonResponse({'success': True})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=500)
    
    return JsonResponse({'success': False}, status=400)
