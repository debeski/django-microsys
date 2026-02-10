# Imports of the required python modules and libraries
######################################################
from django.urls import path
from . import views, utils
from django.contrib.auth import views as auth_views

# app_name = 'microsys'

urlpatterns = [
    # Auth URLs (Django defaults - no prefix needed when mounted at root)
    path('accounts/login/', views.CustomLoginView.as_view(), name='login'),
    path('accounts/logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('accounts/profile/', views.user_profile, name='user_profile'),
    path('accounts/profile/edit/', views.edit_profile, name='edit_profile'),
    
    # System URLs (all prefixed with sys/)
    path('sys/', views.dashboard, name='sys_dashboard'),
    path('sys/users/', views.UserListView.as_view(), name='manage_users'),
    path('sys/users/create/', views.create_user, name='create_user'),
    path('sys/users/edit/<int:pk>/', views.edit_user, name='edit_user'),
    path('sys/users/delete/<int:pk>/', views.delete_user, name='delete_user'),
    path('sys/users/<int:pk>/', views.UserDetailView.as_view(), name='user_detail'),

    path('sys/logs/', views.UserActivityLogView.as_view(), name='user_activity_log'),
    path('sys/reset_password/<int:pk>/', views.reset_password, name='reset_password'),
    
    # Scope Management URLs
    path('sys/scopes/manage/', views.manage_scopes, name='manage_scopes'),
    path('sys/scopes/form/', views.get_scope_form, name='get_scope_form'),
    path('sys/scopes/form/<int:pk>/', views.get_scope_form, name='get_scope_form'),
    path('sys/scopes/save/', views.save_scope, name='save_scope'),
    path('sys/scopes/save/<int:pk>/', views.save_scope, name='save_scope'),
    path('sys/scopes/delete/<int:pk>/', views.delete_scope, name='delete_scope'),
    path('sys/scopes/toggle/', views.toggle_scopes, name='toggle_scopes'),

    # Sections Management URLs
    path('sys/options/', views.options_view, name='options_view'),
    path('sys/sections/', views.core_models_view, name='manage_sections'),
    path('sys/subsection/add/', views.add_subsection, name='add_subsection'),
    path('sys/subsection/edit/<int:pk>/', views.edit_subsection, name='edit_subsection'),
    path('sys/subsection/delete/<int:pk>/', views.delete_subsection, name='delete_subsection'),
    path('sys/section/delete/', views.delete_section, name='delete_section'),
    path('sys/section/subsections/', views.get_section_subsections, name='get_section_subsections'),

    # Sidebar Toggle URL
    path('sys/toggle-sidebar/', utils.toggle_sidebar, name='toggle_sidebar'),
]

