from django.urls import path
from .views import UserRegistrationAPIView, UserLoginAPIView, register_page, login_page

urlpatterns = [
    path('', login_page, name='home'),
    path('api/register/', UserRegistrationAPIView.as_view(), name='api-register'),
    path('api/login/', UserLoginAPIView.as_view(), name='api-login'),
    path('register/', register_page, name='register-page'),
    path('login/', login_page, name='login-page'),
]
