import urllib.request
import json

url = "https://grill-set-ron-reload.trycloudflare.com/whatsapp"
payload = {
  "object": "whatsapp_business_account",
  "entry": [
    {
      "id": "1234567890",
      "changes": [
        {
          "value": {
            "messaging_product": "whatsapp",
            "metadata": {
              "display_phone_number": "15556367230",
              "phone_number_id": "1234567890"
            },
            "contacts": [
              {
                "profile": {
                  "name": "Test User"
                },
                "wa_id": "123456789"
              }
            ],
            "messages": [
              {
                "from": "123456789",
                "id": "wamid.HBgL",
                "timestamp": "1699999999",
                "text": {
                  "body": "Hello from python script!"
                },
                "type": "text"
              }
            ]
          },
          "field": "messages"
        }
      ]
    }
  ]
}

req = urllib.request.Request(url, data=json.dumps(payload).encode('utf-8'), headers={'Content-Type': 'application/json'})
try:
    with urllib.request.urlopen(req) as response:
        print("Success:", response.read().decode('utf-8'))
except urllib.error.HTTPError as e:
    print("HTTPError:", e.code, e.read().decode('utf-8'))
