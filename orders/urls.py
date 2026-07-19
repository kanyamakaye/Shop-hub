from django.urls import path

from . import views

app_name = 'orders'

urlpatterns = [
    path('', views.order_list, name='list'),
    path('<int:pk>/', views.order_detail, name='detail'),
    path('<int:pk>/return/request/', views.request_return, name='request_return'),
    path('<int:pk>/return/process/', views.process_return, name='process_return'),
    path('checkout/', views.checkout, name='checkout'),
]
