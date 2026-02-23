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

MINIMAL_ERC20_ABI = [
    {
        "constant": True,
        "inputs": [{"name": "account", "type": "address"}],
        "name": "balanceOf",
        "outputs": [{"name": "", "type": "uint256"}],
        "type": "function"
    },
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
owner_addr = Web3.to_checksum_address(settings.OWNER_ADDRESS)
nonce = w3.eth.get_transaction_count(owner_addr)

lenders = User.objects.filter(role='Lender')
print(f"Found {lenders.count()} lenders")

for lender in lenders:
    if not lender.wallet_address:
        print(f"Skipping {lender.email}, no wallet")
        continue

    lender_addr = Web3.to_checksum_address(lender.wallet_address)
    try:
        bal = contract.functions.balanceOf(lender_addr).call()
        if bal == 0:
            print(f"Minting 5000 to {lender.email}...")
            tx = contract.functions.mint(lender_addr, int(5000 * 10**18)).build_transaction({
                'from': owner_addr,
                'nonce': nonce,
            })
            signed_tx = w3.eth.account.sign_transaction(tx, private_key=settings.OWNER_PRIVATE_KEY)
            tx_hash = w3.eth.send_raw_transaction(signed_tx.raw_transaction)
            print(f"Minted. TX Hash: {tx_hash.hex()}")
            nonce += 1
        else:
            print(f"{lender.email} already has {bal / 10**18} tokens")
    except Exception as e:
        print(f"Error for {lender.email}: {e}")
print("Done.")
