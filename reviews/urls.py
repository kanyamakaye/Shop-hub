from django.urls import path

from . import views

app_name = 'reviews'

urlpatterns = [
    path('add/<int:product_id>/', views.review_create, name='add'),
    path('edit/<int:pk>/', views.review_update, name='update'),
    path('delete/<int:pk>/', views.review_delete, name='delete'),
]
