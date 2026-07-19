from django.urls import path

from . import views

app_name = 'wishlist'

urlpatterns = [
    path('', views.wishlist, name='list'),
    path('overview/', views.wishlist_overview, name='overview'),
    path('add/<int:product_id>/', views.wishlist_add, name='add'),
    path('remove/<int:pk>/', views.wishlist_remove, name='remove'),
]
