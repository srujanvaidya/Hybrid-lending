import requests

rpc = "https://polygon-bor-rpc.publicnode.com"
addr = "0x48B0DB4e87D280AFB3fDC572f61A641E7261D74D"
payload = {
    "jsonrpc":"2.0",
    "method":"eth_getCode",
    "params":[addr, "latest"],
    "id":1
}
res = requests.post(rpc, json=payload)
print(res.json())
