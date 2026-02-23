import requests

rpcs = {
    "Polygon Amoy": "https://rpc-amoy.polygon.technology/",
    "Ethereum Sepolia": "https://ethereum-sepolia-rpc.publicnode.com",
    "Polygon zkEVM Testnet": "https://rpc.public.zkevm-test.net",
    "Binance Smart Chain Testnet": "https://data-seed-prebsc-1-s1.binance.org:8545/",
    "Ethereum Mainnet": "https://ethereum-rpc.publicnode.com"
}
addr = "0x48B0DB4e87D280AFB3fDC572f61A641E7261D74D"
payload = {"jsonrpc":"2.0", "method":"eth_getCode", "params":[addr, "latest"], "id":1}

for name, rpc in rpcs.items():
    try:
        res = requests.post(rpc, json=payload, timeout=5)
        code = res.json().get('result', '0x')
        if code != '0x':
            print(f"FOUND ON {name}: {rpc}")
        else:
            print(f"Not on {name}")
    except Exception as e:
        print(f"Error checking {name}")
