from django.urls import path

from . import views

app_name = 'dashboard'

urlpatterns = [
    path('', views.redirect_to_dashboard, name='redirect'),
    path('owner/', views.owner_dashboard, name='owner'),
    path('tenant/', views.tenant_dashboard, name='tenant'),
    path('customer/', views.customer_dashboard, name='customer'),
]
