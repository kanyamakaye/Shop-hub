from django.urls import path

from . import views

app_name = 'categories'

urlpatterns = [
    path('', views.category_list, name='list'),
    path('create/', views.category_create, name='create'),
    path('edit/<int:pk>/', views.category_update, name='update'),
    path('delete/<int:pk>/', views.category_delete, name='delete'),
]
