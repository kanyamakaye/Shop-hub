from django.urls import path

from . import views

app_name = 'tenants'

urlpatterns = [
    path('', views.tenant_list, name='list'),
    path('create/', views.tenant_create, name='create'),
    path('<int:pk>/', views.tenant_detail, name='detail'),
    path('<int:pk>/edit/', views.tenant_update, name='update'),
    path('<int:pk>/delete/', views.tenant_delete, name='delete'),
]
