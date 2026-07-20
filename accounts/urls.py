from django.urls import path

from . import views

app_name = 'accounts'

urlpatterns = [
    path('login/', views.login_view, name='login'),
    path('verify-otp/', views.verify_otp_view, name='verify_otp'),
    path('verify-otp/resend/', views.resend_otp_view, name='resend_otp'),
    path('logout/', views.logout_view, name='logout'),
    path('register/', views.register, name='register'),

    path('password-reset/', views.StyledPasswordResetView.as_view(), name='forgot_password'),
    path('password-reset/done/', views.StyledPasswordResetDoneView.as_view(), name='password_reset_done'),
    path('password-reset/confirm/<uidb64>/<token>/', views.StyledPasswordResetConfirmView.as_view(), name='password_reset_confirm'),
    path('password-reset/complete/', views.StyledPasswordResetCompleteView.as_view(), name='password_reset_complete'),

    path('password-change/', views.StyledPasswordChangeView.as_view(), name='change_password'),
    path('password-change/done/', views.StyledPasswordChangeDoneView.as_view(), name='change_password_done'),

    path('profile/', views.user_profile, name='profile'),

    path('users/', views.user_list, name='user_list'),
    path('users/create/', views.user_create, name='user_create'),
    path('users/<int:pk>/edit/', views.user_update, name='user_update'),
    path('users/<int:pk>/delete/', views.user_delete, name='user_delete'),
]
