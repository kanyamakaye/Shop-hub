from django.urls import path

from . import views

app_name = 'notifications'

urlpatterns = [
    path('', views.notification_list, name='list'),
    path('read/<int:pk>/', views.notification_read, name='read'),
    path('delete/<int:pk>/', views.notification_delete, name='delete'),
]
