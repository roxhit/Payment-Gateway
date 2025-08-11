import http.client
import json

conn = http.client.HTTPSConnection("payments.zoho.in")

payload = {
    "amount": "100.5",
    "currency": "INR",
    "meta_data": [{"key": "Key1", "value": "Value1"}],
    "description": "Payment for Order #12345",
    "invoice_number": "INV-12345",
}

headers = {
    "Authorization": "Zoho-oauthtoken 1003.a0c2534de0859237301608628217a8f5.c8eba581795098c7ed6e57969931aa61",
    "content-type": "application/json",
}

conn.request(
    "POST",
    "/api/v1/paymentsessions?account_id=60008335052",
    body=json.dumps(payload),
    headers=headers,
)

res = conn.getresponse()
data = res.read()

print(data.decode("utf-8"))
