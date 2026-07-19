from django.urls import path

from . import views

app_name = 'products'

urlpatterns = [
    path('', views.product_list, name='list'),
    path('manage/', views.product_manage_list, name='manage_list'),
    path('create/', views.product_create, name='create'),
    path('<int:pk>/', views.product_detail, name='detail'),
    path('edit/<int:pk>/', views.product_update, name='update'),
    path('delete/<int:pk>/', views.product_delete, name='delete'),
]
