# Fundemental imports
######################################################
from django.utils import timezone
from django.contrib import messages
from django.contrib.auth import get_user_model, update_session_auth_hash
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.http import JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django_tables2 import RequestConfig, SingleTableView, SingleTableMixin
from django_filters.views import FilterView
from django.views.generic.detail import DetailView
from django.apps import apps
from django.utils.module_loading import import_string
from django.contrib.auth.views import LoginView
from django.conf import settings

# Project imports
#################

from .signals import get_client_ip
from .tables import UserTable
from .forms import CustomUserCreationForm, CustomUserChangeForm, ArabicPasswordChangeForm, ResetPasswordForm, UserProfileEditForm
from .filters import UserFilter

User = get_user_model() # Use custom user model

# Helper Function to log actions
def log_user_action(request, instance, action, model_name):
    UserActivityLog = apps.get_model('users', 'UserActivityLog')
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

# Custom Login View with Theme Injection
class CustomLoginView(LoginView):
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Inject theme configuration from settings
        context['theme'] = getattr(settings, 'MICRO_USERS_THEME', {})
        return context


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
    template_name = "users/manage_users.html"
    
    # Restrict access to only staff users
    def test_func(self):
        return self.request.user.is_staff


    
    def get_queryset(self):
        # Apply the filter and order by any logic you need
        qs = super().get_queryset().order_by('date_joined')
        # Exclude soft-deleted users
        qs = qs.filter(deleted_at__isnull=True)
        # Hide superuser entries from non-superusers
        if not self.request.user.is_superuser:
            qs = qs.exclude(is_superuser=True)
            # Restrict to same scope
            if self.request.user.scope:
                qs = qs.filter(scope=self.request.user.scope)
        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user_filter = self.get_filterset(self.filterset_class)

        # Apply the pagination
        RequestConfig(self.request, paginate={'per_page': 10}).configure(self.table_class(user_filter.qs))
        
        context["filter"] = user_filter
        context["users"] = user_filter.qs
        return context


# Function for creating a new User
@user_passes_test(is_staff)
def create_user(request):
    if request.method == "POST":
        form = CustomUserCreationForm(request.POST or None, user=request.user)
        if form.is_valid():
            user = form.save(commit=False)
            # Auto-assign scope for non-superusers
            if not request.user.is_superuser and request.user.scope:
                user.scope = request.user.scope
            user.save()
            user.user_permissions.set(form.cleaned_data["permissions"])
            return redirect("manage_users")
        else:
            return render(request, "users/user_form.html", {"form": form})
    else:
        form = CustomUserCreationForm(user=request.user)
    
    return render(request, "users/user_form.html", {"form": form})


# Function for editing an existing User
@user_passes_test(is_staff)
def edit_user(request, pk):
    user = get_object_or_404(User, pk=pk)
    
    # 🚫 Block staff users from editing superuser accounts
    if user.is_superuser and not request.user.is_superuser:
        messages.error(request, "ليس لديك صلاحية لتعديل هذا الحساب!")
        return redirect('manage_users')


    # Restrict to same scope
    if not request.user.is_superuser:
        if request.user.scope and user.scope != request.user.scope:
             messages.error(request, "ليس لديك صلاحية لتعديل هذا المستخدم!")
             return redirect('manage_users')

    form_reset = ResetPasswordForm(user, data=request.POST or None)

    if request.method == "POST":
        form = CustomUserChangeForm(request.POST, instance=user, user=request.user)
        if form.is_valid():
            user = form.save(commit=False)
            user.save()
            user.user_permissions.set(form.cleaned_data["permissions"])
            return redirect("manage_users")
        else:
            # Validation errors will be automatically handled by the form object
            return render(request, "users/user_form.html", {"form": form, "edit_mode": True, "form_reset": form_reset})

    else:
        form = CustomUserChangeForm(instance=user, user=request.user)

    return render(request, "users/user_form.html", {"form": form, "edit_mode": True, "form_reset": form_reset})


# Function for deleting a User
@user_passes_test(is_superuser)
def delete_user(request, pk):
    user = get_object_or_404(User, pk=pk)

    # Restrict to same scope
    if not request.user.is_superuser:
        if request.user.scope and user.scope != request.user.scope:
             messages.error(request, "ليس لديك صلاحية لحذف هذا المستخدم!")
             return redirect('manage_users')

    if request.method == "POST":
        # Soft delete the user
        user.is_active = False
        user.deleted_at = timezone.now()
        user.save()
        return redirect("manage_users")
    return redirect("manage_users")  # Redirect instead of rendering a separate page


# Class Function for the Log
class UserActivityLogView(LoginRequiredMixin, UserPassesTestMixin, SingleTableMixin, FilterView):
    model = apps.get_model('users', 'UserActivityLog')
    table_class = import_string('users.tables.UserActivityLogTable')
    filterset_class = import_string('users.filters.UserActivityLogFilter')
    template_name = "users/user_activity_log.html"

    def test_func(self):
        return self.request.user.is_staff  # Only staff can access logs
    
    def get_queryset(self):
        # Order by timestamp descending by default
        qs = super().get_queryset().order_by('-timestamp')
        if not self.request.user.is_superuser:
            qs = qs.exclude(user__is_superuser=True)
            if self.request.user.scope:
                qs = qs.filter(user__scope=self.request.user.scope)
        return qs

    def get_table(self, **kwargs):
        table = super().get_table(**kwargs)
        if self.request.user.scope:
            table.exclude = ('scope',)
        return table

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Handle the filter object
        context['filter'] = self.filterset
        return context


class UserDetailView(LoginRequiredMixin, UserPassesTestMixin, DetailView):
    model = User
    template_name = "users/user_detail.html"

    def test_func(self):
        # only staff can view user detail page
        return self.request.user.is_staff

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # self.object is the User instance
        UserActivityLog = apps.get_model('users', 'UserActivityLog')
        logs_qs = UserActivityLog.objects.filter(user=self.object).order_by('-timestamp')
        
        # Create table manually
        UserActivityLogTableNoUser = import_string('users.tables.UserActivityLogTableNoUser')
        table = UserActivityLogTableNoUser(logs_qs)
        RequestConfig(self.request, paginate={'per_page': 10}).configure(table)
        
        context['table'] = table
        return context


# Function that resets a user password
@user_passes_test(is_staff)
def reset_password(request, pk):
    user = get_object_or_404(User, id=pk)

    # 🚫 Block staff users from resetting superuser passwords
    if user.is_superuser and not request.user.is_superuser:
        messages.error(request, "ليس لديك صلاحية لتعديل هذا الحساب!")
        return redirect('manage_users')

    # Restrict to same scope
    if not request.user.is_superuser:
        if request.user.scope and user.scope != request.user.scope:
             messages.error(request, "ليس لديك صلاحية لتعديل هذا المستخدم!")
             return redirect('manage_users')

    if request.method == "POST":
        form = ResetPasswordForm(user=user, data=request.POST)  # ✅ Correct usage with SetPasswordForm
        if form.is_valid():
            form.save()
            log_user_action(request, user, "RESET", "رمز سري")
            return redirect("manage_users")
        else:
            print("Form errors:", form.errors)
            return redirect("edit_user", pk=pk)
    
    return redirect("manage_users")  # Fallback redirect


# Function for the user profile
@login_required
def user_profile(request):
    user = request.user
    password_form = ArabicPasswordChangeForm(user)
    if request.method == 'POST':
        password_form = ArabicPasswordChangeForm(user, request.POST)
        if password_form.is_valid():
            password_form.save()
            log_user_action(request, user, "UPDATE", "رمز سري")
            update_session_auth_hash(request, password_form.user)  # Prevent user from being logged out
            messages.success(request, 'تم تغيير كلمة المرور بنجاح!')
            return redirect('user_profile')
        else:
            # Log form errors
            messages.error(request, "هناك خطأ في البيانات المدخلة")
            print(password_form.errors)  # You can log or print errors here for debugging

    return render(request, 'users/profile/profile.html', {
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
            log_user_action(request, user, "UPDATE", "بيانات شخصية")
            messages.success(request, 'تم حفظ التغييرات بنجاح')
            return redirect('user_profile')
        else:
            messages.error(request, 'حدث خطأ أثناء حفظ التغييرات')
    else:
        form = UserProfileEditForm(instance=request.user)
    return render(request, 'users/profile/profile_edit.html', {'form': form})

# Scope Management Views
# ###########################
from django.template.loader import render_to_string

@login_required # staff check handled in template or can be added here
@user_passes_test(is_staff)
def manage_scopes(request):
    """
    Returns the initial modal content with the table.
    """
    if request.user.scope:
        return JsonResponse({'error': 'Permission denied.'}, status=403)

    Scope = apps.get_model('users', 'Scope')
    ScopeTable = import_string('users.tables.ScopeTable')
    table = ScopeTable(Scope.objects.all())
    RequestConfig(request, paginate={'per_page': 5}).configure(table)
    
    context = {'table': table}
    html = render_to_string('users/partials/scope_manager.html', context, request=request)
    return JsonResponse({'html': html})

@login_required
@user_passes_test(is_staff)
def get_scope_form(request, pk=None):
    """
    Returns the Add/Edit form partial.
    """
    if request.user.scope:
        return JsonResponse({'error': 'Permission denied.'}, status=403)

    ScopeForm = import_string('users.forms.ScopeForm')
    Scope = apps.get_model('users', 'Scope')

    if pk:
        scope = get_object_or_404(Scope, pk=pk)
        form = ScopeForm(instance=scope)
    else:
        form = ScopeForm()
        
    html = render_to_string('users/partials/scope_form.html', {'form': form, 'scope_id': pk}, request=request)
    return JsonResponse({'html': html})

@login_required
@user_passes_test(is_staff)
def save_scope(request, pk=None):
    """
    Handles form submission. Returns updated table on success, or form with errors on failure.
    """
    if request.user.scope:
        return JsonResponse({'error': 'Permission denied.'}, status=403)
    
    ScopeForm = import_string('users.forms.ScopeForm')
    Scope = apps.get_model('users', 'Scope')
    ScopeTable = import_string('users.tables.ScopeTable')

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
            html = render_to_string('users/partials/scope_manager.html', {'table': table}, request=request)
            return JsonResponse({'success': True, 'html': html})
        else:
            # Return form with errors
            html = render_to_string('users/partials/scope_form.html', {'form': form, 'scope_id': pk}, request=request)
            return JsonResponse({'success': False, 'html': html})
    
    return JsonResponse({'success': False, 'error': 'Invalid method'})

@login_required
@user_passes_test(is_staff)
def delete_scope(request, pk):
    return JsonResponse({'success': False, 'error': 'تم تعطيل حذف النطاقات لأسباب أمنية.'})
