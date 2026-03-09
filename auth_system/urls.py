"""
URL маршруты для auth_system.
"""
from django.urls import path
from . import views

urlpatterns = [
    path('', views.auth_api_index),
    path('register/', views.register),
    path('login/', views.login),
    path('logout/', views.logout),
    path('refresh/', views.refresh_token),
    path('profile/', views.ProfileView.as_view()),
    path('delete-account/', views.delete_account),

    path('admin/resources/', views.resource_list_create),
    path('admin/resources/<int:pk>/', views.resource_detail),
    path('admin/actions/', views.action_list_create),
    path('admin/actions/<int:pk>/', views.action_detail),
    path('admin/permissions/', views.permission_list_create),
    path('admin/permissions/<int:pk>/', views.permission_detail),
    path('admin/roles/', views.role_list_create),
    path('admin/roles/<int:pk>/', views.role_detail),
    path('admin/assign-role/', views.assign_role),
    path('admin/revoke-role/<int:user_id>/<int:role_id>/', views.revoke_role),
]
