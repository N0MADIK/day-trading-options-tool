
import sys
sys.path.append('.')
from fastapi.testclient import TestClient
from app.main import app
import uuid

client = TestClient(app)

unique_id = str(uuid.uuid4())[:8]
email = f"test_{unique_id}@example.com"
password = "SafePassword123!"
full_name = "Test User"

response = client.post("/api/v1/auth/register", json={
    "email": email,
    "password": password,
    "full_name": full_name
})

with open("debug_auth.txt", "w") as f:
    f.write(f"Status: {response.status_code}\n")
    f.write(f"Body: {response.text}\n")
