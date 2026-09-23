from django.urls import path
from . import views

urlpatterns = [
    path('signup/', views.signup_view, name='signup'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('profile/', views.profile_view, name='profile'),
    path('setup-2fa/', views.setup_2fa_view, name='setup_2fa'),
    path('verify-2fa/', views.verify_2fa_view, name='verify_2fa'),
]