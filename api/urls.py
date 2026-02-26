from django.urls import path
from django.shortcuts import render
from .views import (
    UserRegistrationAPIView, UserLoginAPIView,
    LoanRequestAPIView, FinancialProfileAPIView,
    UserDashboardDataAPIView, LenderPreferenceAPIView,
    ESP32LoanRequestAPIView
)

def register_page(request):
    return render(request, 'api/register.html')

def login_page(request):
    return render(request, 'api/login.html')

def borrower_page(request):
    return render(request, 'api/borrower.html')

def lender_page(request):
    return render(request, 'api/lender.html')

def home_page(request):
    return render(request, 'api/home.html')

urlpatterns = [
    path('', login_page, name='home'),
    path('api/register/', UserRegistrationAPIView.as_view(), name='api-register'),
    path('api/login/', UserLoginAPIView.as_view(), name='api-login'),
    path('api/loan-request/', LoanRequestAPIView.as_view(), name='api-loan-request'),
    path('api/financial-profile/', FinancialProfileAPIView.as_view(), name='api-financial-profile'),
    path('api/lender-preferences/', LenderPreferenceAPIView.as_view(), name='api-lender-preferences'),
    path('api/dashboard-data/', UserDashboardDataAPIView.as_view(), name='api-dashboard-data'),
    path('api/esp32/loan-request/', ESP32LoanRequestAPIView.as_view(), name='api-esp32-loan-request'),
    path('register/', register_page, name='register-page'),
    path('login/', login_page, name='login-page'),
    path('borrower/', borrower_page, name='borrower-page'),
    path('lender/', lender_page, name='lender-page'),
    path('home/', home_page, name='home-page'),
]
