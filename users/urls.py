# Imports of the required python modules and libraries
######################################################
from django.urls import path
from . import views
from django.contrib.auth import views as auth_views

urlpatterns = [
    path('login/', auth_views.LoginView.as_view(), name='login'),
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
    
    # Department Management URLs
    path("departments/manage/", views.manage_departments, name="manage_departments"),
    path("departments/form/", views.get_department_form, name="get_department_form"),
    path("departments/form/<int:pk>/", views.get_department_form, name="get_department_form"),
    path("departments/save/", views.save_department, name="save_department"),
    path("departments/save/<int:pk>/", views.save_department, name="save_department"),
    path("departments/delete/<int:pk>/", views.delete_department, name="delete_department"),
]
