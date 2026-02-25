from rest_framework import serializers
from django.contrib.auth import authenticate
from .models import User, LoanRequest, BorrowerFinancialProfile, LenderPreference
from eth_account import Account
import secrets
from web3 import Web3
from django.conf import settings

MINIMAL_ERC20_ABI = [
    {
        "constant": False,
        "inputs": [
            {"name": "to", "type": "address"},
            {"name": "amount", "type": "uint256"}
        ],
        "name": "mint",
        "outputs": [],
        "type": "function"
    }
]

class UserRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ('id', 'first_name', 'last_name', 'email', 'password', 'mobile_no', 'kyc_pdf', 'role', 'wallet_address')
        read_only_fields = ('wallet_address',)

    def create(self, validated_data):
        # Generate Wallet
        priv = secrets.token_hex(32)
        private_key = "0x" + priv
        acct = Account.from_key(private_key)

        role = validated_data.get('role', 'Borrower')
        user = User.objects.create_user(
            email=validated_data['email'],
            password=validated_data['password'],
            first_name=validated_data.get('first_name', ''),
            last_name=validated_data.get('last_name', ''),
            mobile_no=validated_data.get('mobile_no', ''),
            kyc_pdf=validated_data.get('kyc_pdf', None),
            wallet_address=acct.address,
            private_key=private_key,
            role=role
        )

        # Web3 Minting Logic
        if role == 'Lender':
            try:
                w3 = Web3(Web3.HTTPProvider(settings.WEB3_PROVIDER_URI))
                from web3.middleware import ExtraDataToPOAMiddleware
                w3.middleware_onion.inject(ExtraDataToPOAMiddleware, layer=0)
                
                if w3.is_connected() and settings.OWNER_PRIVATE_KEY and settings.TOKEN_CONTRACT_ADDRESS:
                    contract = w3.eth.contract(address=Web3.to_checksum_address(settings.TOKEN_CONTRACT_ADDRESS), abi=MINIMAL_ERC20_ABI)
                    owner_addr = Web3.to_checksum_address(settings.OWNER_ADDRESS)
                    nonce = w3.eth.get_transaction_count(owner_addr)
                    amount_to_mint = int(5000 * 10**18)
                    
                    tx = contract.functions.mint(
                        Web3.to_checksum_address(acct.address),
                        amount_to_mint
                    ).build_transaction({
                        'from': owner_addr,
                        'nonce': nonce,
                    })
                    
                    signed_tx = w3.eth.account.sign_transaction(tx, private_key=settings.OWNER_PRIVATE_KEY)
                    tx_hash = w3.eth.send_raw_transaction(signed_tx.raw_transaction)
                    # Log or print success dynamically
                    print(f"Minted 5000 tokens to {acct.address}. TX Hash: {tx_hash.hex()}")
            except Exception as e:
                print(f"Web3 Minting Error: {e}")

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
    monthly_emi = serializers.SerializerMethodField()

    class Meta:
        model = LoanRequest
        fields = ('id', 'amount', 'tenure', 'purpose', 'credit_check_consent', 'auto_debit_consent', 'status', 'created_at', 'monthly_emi')
        read_only_fields = ('status', 'created_at', 'monthly_emi')

    def get_monthly_emi(self, obj):
        try:
            P = float(obj.amount)
            n = int(obj.tenure)
            if P > 0 and n > 0:
                r = 0.16 / 12  # 16% Annual Rate
                emi = (P * r * (1 + r)**n) / ((1 + r)**n - 1)
                return round(emi, 2)
        except (TypeError, ValueError):
            pass
        return 0.00

    def validate(self, attrs):
        if not attrs.get('credit_check_consent') or not attrs.get('auto_debit_consent'):
            raise serializers.ValidationError("Both consents must be agreed to.")
        return attrs

class BorrowerFinancialProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = BorrowerFinancialProfile
        fields = ('id', 'yearly_income', 'occupation', 'employer', 'existing_loan_emis', 'gst_no', 'created_at', 'updated_at')
        read_only_fields = ('created_at', 'updated_at')

class LenderPreferenceSerializer(serializers.ModelSerializer):
    class Meta:
        model = LenderPreference
        fields = (
            'id', 'risk_appetite', 'total_lending_amount', 
            'time_period_months', 'auto_reinvest', 'withdrawal_preference',
            'created_at', 'updated_at'
        )
        read_only_fields = ('created_at', 'updated_at')

class ESP32LoanRequestSerializer(serializers.Serializer):
    amount = serializers.DecimalField(max_digits=12, decimal_places=2)
    tenure = serializers.IntegerField(help_text="Tenure in months")

    def validate_amount(self, value):
        if value <= 0:
            raise serializers.ValidationError("Amount must be greater than zero.")
        return value

    def validate_tenure(self, value):
        if value <= 0:
            raise serializers.ValidationError("Tenure must be greater than zero.")
        return value
