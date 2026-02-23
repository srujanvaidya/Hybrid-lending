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
print("Connected:", w3.is_connected())

MINIMAL_ERC20_ABI = [
    {
        "constant": True,
        "inputs": [{"name": "account", "type": "address"}],
        "name": "balanceOf",
        "outputs": [{"name": "", "type": "uint256"}],
        "type": "function"
    }
]

contract = w3.eth.contract(address=Web3.to_checksum_address(settings.TOKEN_CONTRACT_ADDRESS), abi=MINIMAL_ERC20_ABI)

lenders = User.objects.filter(role='Lender')
for lender in lenders:
    if lender.wallet_address:
        w_addr = Web3.to_checksum_address(lender.wallet_address)
        bal = contract.functions.balanceOf(w_addr).call()
        print(f"{lender.email} ({w_addr}): {bal / 10**18} HLT")
