
import pytest
from fastapi.testclient import TestClient
from app.main import app
import uuid

client = TestClient(app)

def test_register_and_login_flow():
    """
    Test the full authentication flow:
    1. Register a new user
    2. Login to get token
    3. Access protected endpoint
    """
    # Use a unique email to avoid conflicts with existing data
    unique_id = str(uuid.uuid4())[:8]
    email = f"test_{unique_id}@example.com"
    password = "SafePassword123!"
    full_name = "Test User"
    
    # 1. Register
    response = client.post("/api/v1/auth/register", json={
        "email": email,
        "password": password,
        "full_name": full_name
    })
    if response.status_code != 201:
        print(f"Registration failed: {response.status_code} {response.text}")
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == email
    
    # 2. Login
    login_response = client.post("/api/v1/auth/login", data={
        "username": email,
        "password": password
    })
    assert login_response.status_code == 200
    token_data = login_response.json()
    assert "access_token" in token_data
    assert token_data["token_type"] == "bearer"
    
    token = token_data["access_token"]
    
    # 3. Access Protected Endpoint (/me)
    me_response = client.get("/api/v1/auth/me", headers={
        "Authorization": f"Bearer {token}"
    })
    assert me_response.status_code == 200
    user_data = me_response.json()
    assert user_data["email"] == email
    assert user_data["full_name"] == full_name

def test_login_invalid_credentials():
    response = client.post("/api/v1/auth/login", data={
        "username": "wrong@example.com",
        "password": "wrongpassword"
    })
    assert response.status_code == 401
