from django.urls import path

from .views import dashboard_home, dashboard_secondary

app_name = 'dashboard'

urlpatterns = [
    path('', dashboard_home, name='dashboard_home'),
    path('secondary/', dashboard_secondary, name='dashboard_secondary'),
]
