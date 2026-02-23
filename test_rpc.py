import requests

rpcs = [
    "https://rpc.ankr.com/polygon",
    "https://polygon-bor-rpc.publicnode.com",
    "https://1rpc.io/matic"
]

payload = {"jsonrpc":"2.0","method":"eth_blockNumber","params":[],"id":1}

for rpc in rpcs:
    try:
        res = requests.post(rpc, json=payload, timeout=5)
        print(f"{rpc}: {res.status_code} - {res.text}")
    except Exception as e:
        print(f"{rpc}: ERROR - {e}")
