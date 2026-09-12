import requests
import json

url = "https://corona.quid.money/api/webhook/mcarbon"

headers = {
    "Content-Type": "application/json",
    "x-api-key": "d6b26788ee09533e44d21a54f29b9d7e"
}

payload = {
    "transactionId": "test_txn_001",
    "campaignId": "test_camp_001",
    "wabaId": "1701585614136150",
    "wabaMessageId": "",
    "wabaPhoneNumberId": "9293624535938609",
    "recipient": "919967943415",
    "eventType": "LEAD_GENERATION",
    "eventTime": "2026-08-09T12:00:00Z",
    "WabaTemplateId": "461034"
}

response = requests.post(url, headers=headers, data=json.dumps(payload))

print(f"Status Code: {response.status_code}")
print(f"Response Body: {response.text}")