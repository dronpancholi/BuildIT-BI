import requests

print("Testing Registration...")
res = requests.post("http://localhost:8000/api/v1/auth/register", json={
    "email": "test@example.com",
    "password": "Password123",
    "full_name": "Test User",
    "role": "cfo"
})
print("Reg status:", res.status_code)
print("Reg text:", res.text)

print("Testing Login...")
res = requests.post("http://localhost:8000/api/v1/auth/login", data={
    "username": "test@example.com",
    "password": "Password123"
}, headers={"Content-Type": "application/x-www-form-urlencoded"})
print("Login status:", res.status_code)
print("Login text:", res.text)
