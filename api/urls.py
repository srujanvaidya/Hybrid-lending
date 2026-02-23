from django.urls import path
from .views import (
    UserRegistrationAPIView, UserLoginAPIView, register_page, login_page, 
    LoanRequestAPIView, borrower_page, FinancialProfileAPIView
)

urlpatterns = [
    path('', login_page, name='home'),
    path('api/register/', UserRegistrationAPIView.as_view(), name='api-register'),
    path('api/login/', UserLoginAPIView.as_view(), name='api-login'),
    path('api/loan-request/', LoanRequestAPIView.as_view(), name='api-loan-request'),
    path('api/financial-profile/', FinancialProfileAPIView.as_view(), name='api-financial-profile'),
    path('register/', register_page, name='register-page'),
    path('login/', login_page, name='login-page'),
    path('borrower/', borrower_page, name='borrower-page'),
]
