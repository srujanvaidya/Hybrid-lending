from rest_framework import status, permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.authtoken.models import Token
from django.shortcuts import render
from django.contrib.auth import login, authenticate
from .models import BorrowerFinancialProfile, LoanRequest, LenderPreference, CredXWallet
from .serializers import (
    UserRegistrationSerializer,
    LoginSerializer,
    LoanRequestSerializer,
    BorrowerFinancialProfileSerializer,
    LenderPreferenceSerializer
)
from django.conf import settings
from web3 import Web3

MINIMAL_ERC20_ABI = [
    {
        "constant": True,
        "inputs": [{"name": "_owner", "type": "address"}],
        "name": "balanceOf",
        "outputs": [{"name": "balance", "type": "uint256"}],
        "type": "function"
    },
    {
        "constant": False,
        "inputs": [
            {"name": "_to", "type": "address"},
            {"name": "_value", "type": "uint256"}
        ],
        "name": "transfer",
        "outputs": [{"name": "", "type": "bool"}],
        "type": "function"
    }
]

class UserRegistrationAPIView(APIView):
    def post(self, request, *args, **kwargs):
        serializer = UserRegistrationSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            token, created = Token.objects.get_or_create(user=user)
            return Response({'token': token.key, 'message': 'Registration successful'}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class UserLoginAPIView(APIView):
    def post(self, request, *args, **kwargs):
        serializer = LoginSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            user = serializer.validated_data['user']
            login(request, user)
            token, created = Token.objects.get_or_create(user=user)
            return Response({'token': token.key, 'message': 'Login successful'}, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

def register_page(request):
    return render(request, 'api/register.html')

def login_page(request):
    return render(request, 'api/login.html')

def borrower_page(request):
    return render(request, 'api/borrower.html')

class LoanRequestAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, *args, **kwargs):
        if request.user.role != 'Borrower':
            return Response({'detail': 'Only borrowers can request loans.'}, status=status.HTTP_403_FORBIDDEN)

        serializer = LoanRequestSerializer(data=request.data)
        if serializer.is_valid():
            loan = serializer.save(user=request.user)
            
            # Check CredX balance and fund Borrower
            try:
                w3 = Web3(Web3.HTTPProvider(settings.WEB3_PROVIDER_URI))
                from web3.middleware import ExtraDataToPOAMiddleware
                w3.middleware_onion.inject(ExtraDataToPOAMiddleware, layer=0)
                
                if w3.is_connected() and settings.TOKEN_CONTRACT_ADDRESS:
                    contract = w3.eth.contract(address=Web3.to_checksum_address(settings.TOKEN_CONTRACT_ADDRESS), abi=MINIMAL_ERC20_ABI)
                    credx = CredXWallet.get_solo()
                    credx_addr = Web3.to_checksum_address(credx.address)
                    borrower_addr = Web3.to_checksum_address(request.user.wallet_address)
                    
                    credx_balance = contract.functions.balanceOf(credx_addr).call()
                    loan_amount_wei = int(loan.amount * 10**18)
                    
                    if credx_balance >= loan_amount_wei:
                        # Gas Station Logic: Ensure CredX Wallet has MATIC to pay gas fees
                        owner_addr = Web3.to_checksum_address(settings.OWNER_ADDRESS)
                        native_balance = w3.eth.get_balance(credx_addr)
                        if native_balance < int(2 * 10**15): # < 0.002 MATIC
                            print("CredX Wallet needs gas. Funding from Owner wallet...")
                            gas_tx = {
                                'to': credx_addr,
                                'value': int(5 * 10**15), # 0.005 MATIC
                                'gas': 21000,
                                'gasPrice': w3.eth.gas_price,
                                'nonce': w3.eth.get_transaction_count(owner_addr),
                                'chainId': w3.eth.chain_id
                            }
                            signed_gas_tx = w3.eth.account.sign_transaction(gas_tx, private_key=settings.OWNER_PRIVATE_KEY)
                            gas_tx_hash = w3.eth.send_raw_transaction(signed_gas_tx.raw_transaction)
                            print(f"Sent gas prep: {gas_tx_hash.hex()}")
                            w3.eth.wait_for_transaction_receipt(gas_tx_hash, timeout=120)
                            print("Gas funded.")
                            
                        # Approve and Transfer
                        nonce = w3.eth.get_transaction_count(credx_addr)
                        tx = contract.functions.transfer(
                            borrower_addr,
                            loan_amount_wei
                        ).build_transaction({
                            'from': credx_addr,
                            'nonce': nonce,
                        })
                        signed_tx = w3.eth.account.sign_transaction(tx, private_key=credx.private_key)
                        tx_hash = w3.eth.send_raw_transaction(signed_tx.raw_transaction)
                        print(f"CredX funded Borrower {loan.amount} USDC: {tx_hash.hex()}")
                        
                        loan.status = 'Approved'
                        loan.save()
                        return Response(LoanRequestSerializer(loan).data, status=status.HTTP_201_CREATED)
                    else:
                        print("Insufficient funds in CredX Wallet to fund the loan.")
                        loan.delete()
                        return Response({'detail': 'The CredX Platform Wallet currently lacks sufficient token liquidity to fund this loan amount. Please try a smaller amount.'}, status=status.HTTP_400_BAD_REQUEST)
                        
            except Exception as e:
                loan.delete()
                print(f"Failed to process loan funding: {e}")
                return Response({'detail': 'A blockchain error occurred while attempting to fund the loan. Please try again.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class FinancialProfileAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, *args, **kwargs):
        try:
            profile = request.user.financial_profile
            serializer = BorrowerFinancialProfileSerializer(profile)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except BorrowerFinancialProfile.DoesNotExist:
            return Response({'detail': 'Financial profile not found.'}, status=status.HTTP_404_NOT_FOUND)

    def post(self, request, *args, **kwargs):
        try:
            profile = request.user.financial_profile
            serializer = BorrowerFinancialProfileSerializer(profile, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data, status=status.HTTP_200_OK)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except BorrowerFinancialProfile.DoesNotExist:
            serializer = BorrowerFinancialProfileSerializer(data=request.data)
            if serializer.is_valid():
                serializer.save(user=request.user)
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class UserDashboardDataAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, *args, **kwargs):
        user = request.user
        
        # 1. Fetch Token Balance via Web3
        token_balance = "0.00"
        try:
            w3 = Web3(Web3.HTTPProvider(settings.WEB3_PROVIDER_URI))
            from web3.middleware import ExtraDataToPOAMiddleware
            w3.middleware_onion.inject(ExtraDataToPOAMiddleware, layer=0)
            
            if w3.is_connected() and settings.TOKEN_CONTRACT_ADDRESS and user.wallet_address:
                contract = w3.eth.contract(
                    address=Web3.to_checksum_address(settings.TOKEN_CONTRACT_ADDRESS), 
                    abi=MINIMAL_ERC20_ABI
                )
                raw_balance = contract.functions.balanceOf(Web3.to_checksum_address(user.wallet_address)).call()
                # Assuming 18 decimals
                token_balance = f"{(raw_balance / 10**18):.2f}"
        except Exception as e:
            print(f"Web3 Balance Error: {e}")
            token_balance = "Error"

        # 2. Calculate Credit Score
        # Hardcoded to 0 as requested for simplified testing
        credit_score = 0

        # 3. Transaction / Activity History
        if user.role == 'Borrower':
            recent_loans = LoanRequest.objects.filter(user=user).order_by('-created_at')[:5]
            activity_history = LoanRequestSerializer(recent_loans, many=True).data
        else:
            activity_history = []
            if hasattr(user, 'lender_preference'):
                pref = user.lender_preference
                activity_history.append({
                    "created_at": pref.updated_at.isoformat(),
                    "purpose": f"Capital Deployment ({pref.risk_appetite} Risk)",
                    "amount": str(pref.total_lending_amount),
                    "tenure": pref.time_period_months,
                    "status": "Deployed"
                })

        # 4. User details
        user_data = {
            "name": f"{user.first_name} {user.last_name}".strip() or user.email,
            "email": user.email,
            "role": user.role,
            "wallet_address": user.wallet_address,
        }
        
        response_data = {
            "user": user_data,
            "balance": token_balance,
            "credit_score": credit_score,
            "recent_activity": activity_history
        }
        
        if user.role == 'Lender':
            if hasattr(user, 'lender_preference'):
                pref = user.lender_preference
                response_data['lender_stats'] = {
                    "total_lending_amount": str(pref.total_lending_amount),
                    "deployed_at": pref.updated_at.isoformat()
                }
            else:
                response_data['lender_stats'] = None

        return Response(response_data, status=status.HTTP_200_OK)

class LenderPreferenceAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, *args, **kwargs):
        try:
            preference = request.user.lender_preference
            serializer = LenderPreferenceSerializer(preference)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except LenderPreference.DoesNotExist:
            return Response({'detail': 'Lender preferences not found.'}, status=status.HTTP_404_NOT_FOUND)

    def post(self, request, *args, **kwargs):
        # Only allow Lenders
        if request.user.role != 'Lender':
            return Response({'detail': 'Only lenders can set preferences.'}, status=status.HTTP_403_FORBIDDEN)

        try:
            preference = request.user.lender_preference
            serializer = LenderPreferenceSerializer(preference, data=request.data, partial=True)
            if serializer.is_valid():
                preference = serializer.save()
                self._fund_credx(request.user, preference.total_lending_amount)
                return Response(serializer.data, status=status.HTTP_200_OK)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except LenderPreference.DoesNotExist:
            serializer = LenderPreferenceSerializer(data=request.data)
            if serializer.is_valid():
                preference = serializer.save(user=request.user)
                self._fund_credx(request.user, preference.total_lending_amount)
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def _fund_credx(self, user, amount):
        try:
            w3 = Web3(Web3.HTTPProvider(settings.WEB3_PROVIDER_URI))
            from web3.middleware import ExtraDataToPOAMiddleware
            w3.middleware_onion.inject(ExtraDataToPOAMiddleware, layer=0)
            
            if w3.is_connected() and settings.TOKEN_CONTRACT_ADDRESS:
                contract = w3.eth.contract(address=Web3.to_checksum_address(settings.TOKEN_CONTRACT_ADDRESS), abi=MINIMAL_ERC20_ABI)
                
                credx = CredXWallet.get_solo()
                lender_addr = Web3.to_checksum_address(user.wallet_address)
                credx_addr = Web3.to_checksum_address(credx.address)
                amount_to_send = int(amount * 10**18)
                
                # Gas Station Logic: Ensure Lender has MATIC to pay gas fees
                owner_addr = Web3.to_checksum_address(settings.OWNER_ADDRESS)
                native_balance = w3.eth.get_balance(lender_addr)
                if native_balance < int(2 * 10**15): # < 0.002 MATIC
                    print("Lender needs gas. Funding from Owner wallet...")
                    gas_tx = {
                        'to': lender_addr,
                        'value': int(5 * 10**15), # 0.005 MATIC
                        'gas': 21000,
                        'gasPrice': w3.eth.gas_price,
                        'nonce': w3.eth.get_transaction_count(owner_addr),
                        'chainId': w3.eth.chain_id
                    }
                    signed_gas_tx = w3.eth.account.sign_transaction(gas_tx, private_key=settings.OWNER_PRIVATE_KEY)
                    gas_tx_hash = w3.eth.send_raw_transaction(signed_gas_tx.raw_transaction)
                    print(f"Sent gas prep: {gas_tx_hash.hex()}")
                    w3.eth.wait_for_transaction_receipt(gas_tx_hash, timeout=120)
                    print("Gas funded.")
                
                nonce = w3.eth.get_transaction_count(lender_addr)
                tx = contract.functions.transfer(
                    credx_addr,
                    amount_to_send
                ).build_transaction({
                    'from': lender_addr,
                    'nonce': nonce,
                })
                signed_tx = w3.eth.account.sign_transaction(tx, private_key=user.private_key)
                tx_hash = w3.eth.send_raw_transaction(signed_tx.raw_transaction)
                print(f"Lender funded CredX: {tx_hash.hex()}")
        except Exception as e:
            print(f"Failed to fund CredX from Lender: {e}")
