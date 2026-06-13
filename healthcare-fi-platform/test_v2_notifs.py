import requests
print("notifications config:")
res = requests.get("http://localhost:8000/api/v2/workspace/notifications/config")
print("status:", res.status_code)
print(res.text)
