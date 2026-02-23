from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager
from eth_account import Account
import secrets

class CustomUserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('The Email field must be set')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        return self.create_user(email, password, **extra_fields)

class User(AbstractUser):
    ROLE_CHOICES = (
        ('Borrower', 'Borrower'),
        ('Lender', 'Lender')
    )
    username = None
    email = models.EmailField('email address', unique=True)
    mobile_no = models.CharField(max_length=15, blank=True, null=True)
    kyc_pdf = models.FileField(upload_to='kyc_pdfs/', blank=True, null=True)
    wallet_address = models.CharField(max_length=42, blank=True, null=True)
    private_key = models.CharField(max_length=66, blank=True, null=True)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='Borrower')

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    objects = CustomUserManager()

    def __str__(self):
        return self.email

class LoanRequest(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='loan_requests')
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    tenure = models.IntegerField(help_text="Tenure in months")
    purpose = models.CharField(max_length=255)
    credit_check_consent = models.BooleanField(default=False)
    auto_debit_consent = models.BooleanField(default=False)
    status = models.CharField(max_length=20, default='Approved')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.email} - {self.amount} - {self.status}"

class BorrowerFinancialProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='financial_profile')
    yearly_income = models.DecimalField(max_digits=15, decimal_places=2)
    occupation = models.CharField(max_length=100)
    employer = models.CharField(max_length=255)
    existing_loan_emis = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    gst_no = models.CharField(max_length=20, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.email} - Financial Profile"

class LenderPreference(models.Model):
    RISK_CHOICES = (
        ('Low', 'Low Risk'),
        ('Medium', 'Medium Risk'),
        ('High', 'High Risk'),
    )
    WITHDRAWAL_CHOICES = (
        ('Monthly Interest', 'Monthly Interest'),
        ('End of Term', 'End of Term'),
        ('Manual', 'Manual'),
    )
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='lender_preference')
    risk_appetite = models.CharField(max_length=20, choices=RISK_CHOICES, default='Medium')
    total_lending_amount = models.DecimalField(max_digits=15, decimal_places=2, help_text="Amount in USDC")
    time_period_months = models.IntegerField(help_text="Lock-in period in months")
    auto_reinvest = models.BooleanField(default=False)
    withdrawal_preference = models.CharField(max_length=30, choices=WITHDRAWAL_CHOICES, default='Monthly Interest')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.email} - Lender Preferences"

class CredXWallet(models.Model):
    address = models.CharField(max_length=42, unique=True)
    private_key = models.CharField(max_length=66)

    @classmethod
    def get_solo(cls):
        obj = cls.objects.first()
        if not obj:
            priv = secrets.token_hex(32)
            private_key = "0x" + priv
            acct = Account.from_key(private_key)
            obj = cls.objects.create(address=acct.address, private_key=private_key)
        return obj

    def __str__(self):
        return f"CredX Platform Wallet ({self.address})"
