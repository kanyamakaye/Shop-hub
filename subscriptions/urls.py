from django.urls import path

from . import views

app_name = 'subscriptions'

urlpatterns = [
    path('', views.plan_list, name='list'),
    path('create/', views.plan_create, name='create'),
    path('<int:pk>/edit/', views.plan_update, name='update'),
    path('<int:pk>/delete/', views.plan_delete, name='delete'),
]
