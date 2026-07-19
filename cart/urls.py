from django.urls import path

from . import views

app_name = 'cart'

urlpatterns = [
    path('', views.cart_list, name='list'),
    path('overview/', views.cart_overview, name='overview'),
    path('add/<int:product_id>/', views.add_to_cart, name='add'),
    path('update/<int:pk>/', views.update_cart, name='update'),
    path('delete/<int:pk>/', views.remove_cart, name='remove'),
]
