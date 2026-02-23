import os
import django
from web3 import Web3

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()
from django.conf import settings
from api.models import User

w3 = Web3(Web3.HTTPProvider(settings.WEB3_PROVIDER_URI))
from web3.middleware import ExtraDataToPOAMiddleware
w3.middleware_onion.inject(ExtraDataToPOAMiddleware, layer=0)
print(f"Connected: {w3.is_connected()}")

lender = User.objects.filter(role='Lender').first()
if lender:
    owner_addr = Web3.to_checksum_address(settings.OWNER_ADDRESS)
    lender_addr = Web3.to_checksum_address(lender.wallet_address)
    
    native_balance = w3.eth.get_balance(lender_addr)
    print(f"Lender {lender.email} balance: {native_balance} Wei")
    
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
        receipt = w3.eth.wait_for_transaction_receipt(gas_tx_hash, timeout=120)
        print("Gas funded.")
else:
    print("No lenders found.")
