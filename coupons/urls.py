from django.urls import path

from . import views

app_name = 'coupons'

urlpatterns = [
    path('', views.coupon_list, name='list'),
    path('create/', views.coupon_create, name='create'),
    path('edit/<int:pk>/', views.coupon_update, name='update'),
    path('delete/<int:pk>/', views.coupon_delete, name='delete'),
]
