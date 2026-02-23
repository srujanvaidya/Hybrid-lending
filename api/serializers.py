from rest_framework import serializers
from django.contrib.auth import authenticate
from .models import User, LoanRequest, BorrowerFinancialProfile
from eth_account import Account
import secrets

class UserRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ('id', 'first_name', 'last_name', 'email', 'password', 'mobile_no', 'kyc_pdf', 'wallet_address')
        read_only_fields = ('wallet_address',)

    def create(self, validated_data):
        # Generate Wallet
        priv = secrets.token_hex(32)
        private_key = "0x" + priv
        acct = Account.from_key(private_key)

        user = User.objects.create_user(
            email=validated_data['email'],
            password=validated_data['password'],
            first_name=validated_data.get('first_name', ''),
            last_name=validated_data.get('last_name', ''),
            mobile_no=validated_data.get('mobile_no', ''),
            kyc_pdf=validated_data.get('kyc_pdf', None),
            wallet_address=acct.address,
            private_key=private_key
        )
        return user

class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        email = attrs.get('email')
        password = attrs.get('password')

        if email and password:
            user = authenticate(request=self.context.get('request'), username=email, password=password)
            if not user:
                raise serializers.ValidationError('Invalid credentials.')
        else:
            raise serializers.ValidationError('Must include "email" and "password".')

        attrs['user'] = user
        return attrs

class LoanRequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = LoanRequest
        fields = ('id', 'amount', 'tenure', 'purpose', 'credit_check_consent', 'auto_debit_consent', 'status', 'created_at')
        read_only_fields = ('status', 'created_at')

    def validate(self, attrs):
        if not attrs.get('credit_check_consent') or not attrs.get('auto_debit_consent'):
            raise serializers.ValidationError("Both consents must be agreed to.")
        return attrs

class BorrowerFinancialProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = BorrowerFinancialProfile
        fields = ('id', 'yearly_income', 'occupation', 'employer', 'existing_loan_emis', 'gst_no', 'created_at', 'updated_at')
        read_only_fields = ('created_at', 'updated_at')
