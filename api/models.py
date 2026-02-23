from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager

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
    username = None
    email = models.EmailField('email address', unique=True)
    mobile_no = models.CharField(max_length=15, blank=True, null=True)
    kyc_pdf = models.FileField(upload_to='kyc_pdfs/', blank=True, null=True)
    wallet_address = models.CharField(max_length=42, blank=True, null=True)
    private_key = models.CharField(max_length=66, blank=True, null=True)

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
    status = models.CharField(max_length=20, default='Pending')
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
