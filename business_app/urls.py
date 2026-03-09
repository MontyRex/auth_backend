"""
URL маршруты для mock бизнес-объектов.
"""
from django.urls import path
from . import views

urlpatterns = [
    path('', views.business_api_index),
    path('documents/', views.document_list),
    path('documents/create/', views.document_create),
    path('reports/', views.report_list),
    path('reports/<int:pk>/', views.report_detail),
    path('settings/', views.settings_view),
]
