import os
import django
from web3 import Web3

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()
from django.conf import settings

w3 = Web3(Web3.HTTPProvider(settings.WEB3_PROVIDER_URI))
from web3.middleware import ExtraDataToPOAMiddleware
w3.middleware_onion.inject(ExtraDataToPOAMiddleware, layer=0)

try:
    print("Is connected:", w3.is_connected())
    if w3.is_connected():
        print("Owner Address:", settings.OWNER_ADDRESS)
        owner_addr = Web3.to_checksum_address(settings.OWNER_ADDRESS)
        balance = w3.eth.get_balance(owner_addr)
        print("Owner Native Balance:", balance)
        
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
        contract = w3.eth.contract(address=Web3.to_checksum_address(settings.TOKEN_CONTRACT_ADDRESS), abi=MINIMAL_ERC20_ABI)
        nonce = w3.eth.get_transaction_count(owner_addr)
        
        print(f"Nonce: {nonce}")
        tx = contract.functions.mint(owner_addr, 100).build_transaction({
            'from': owner_addr,
            'nonce': nonce,
        })
        print(f"Built tx: {tx}")
        signed_tx = w3.eth.account.sign_transaction(tx, private_key=settings.OWNER_PRIVATE_KEY)
        tx_hash = w3.eth.send_raw_transaction(signed_tx.rawTransaction)
        print("Test mint TX Hash (sent to self):", tx_hash.hex())
except Exception as e:
    import traceback
    traceback.print_exc()
