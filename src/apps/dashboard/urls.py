"""URL configuration for dashboard app."""

from django.urls import path

from . import views

app_name = 'dashboard'

urlpatterns = [
    path('ajax/', views.dashboard_ajax, name='ajax'),
    path('analytics/', views.analytics_view, name='analytics'),
]
