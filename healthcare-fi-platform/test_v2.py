import requests
print("workspace layout:")
print(requests.get("http://localhost:8000/api/v2/workspace").text)
print("briefings:")
print(requests.get("http://localhost:8000/api/v2/workspace/briefings").text)
