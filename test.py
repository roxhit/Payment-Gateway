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
    "Authorization": "Zoho-oauthtoken 1000.2283d543281d6545522f1fee9827dfb7.6f9e98b57cbbdaaecb959f41f5d7db31",
    "content-type": "application/json",
}

conn.request(
    "POST",
    "/api/v1/paymentsessions?account_id=60044853379",
    body=json.dumps(payload),
    headers=headers,
)

res = conn.getresponse()
data = res.read()

print(data.decode("utf-8"))
