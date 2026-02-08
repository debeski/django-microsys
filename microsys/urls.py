# Imports of the required python modules and libraries
######################################################
from django.urls import path
from . import views, utils
from django.contrib.auth import views as auth_views

urlpatterns = [
    path('', views.index, name='index'), # Dashboard/Index
    path('login/', views.CustomLoginView.as_view(), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path("users/", views.UserListView.as_view(), name="manage_users"),
    path('users/create/', views.create_user, name='create_user'),
    path('users/edit/<int:pk>/', views.edit_user, name='edit_user'),
    path('users/delete/<int:pk>/', views.delete_user, name='delete_user'),
    path("profile", views.user_profile, name="user_profile"),
    path('profile/edit/', views.edit_profile, name='edit_profile'),
    path("logs/", views.UserActivityLogView.as_view(), name="user_activity_log"),
    path('reset_password/<int:pk>/', views.reset_password, name="reset_password"),
    path("users/<int:pk>/", views.UserDetailView.as_view(), name="user_detail"),
    
    # Scope Management URLs
    path("scopes/manage/", views.manage_scopes, name="manage_scopes"),
    path("scopes/form/", views.get_scope_form, name="get_scope_form"),
    path("scopes/form/<int:pk>/", views.get_scope_form, name="get_scope_form"),
    path("scopes/save/", views.save_scope, name="save_scope"),
    path("scopes/save/<int:pk>/", views.save_scope, name="save_scope"),
    path("scopes/delete/<int:pk>/", views.delete_scope, name="delete_scope"),
    path('scopes/toggle/', views.toggle_scopes, name='toggle_scopes'),

    # Sections Management URLs
    path('options/', views.options_view, name='options_view'),
    path('sections/', views.core_models_view, name='manage_sections'),
    path('subsection/add/', views.add_subsection, name='add_subsection'),
    path('subsection/edit/<int:pk>/', views.edit_subsection, name='edit_subsection'),
    path('subsection/delete/<int:pk>/', views.delete_subsection, name='delete_subsection'),

    # Sidebar Toggle URL
    path("toggle-sidebar/", utils.toggle_sidebar, name="toggle_sidebar"),
]
