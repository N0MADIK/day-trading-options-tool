import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch

from app.main import app
from app.schemas.personal_finance import (
    InstitutionCreateRequest, InstitutionUpdateRequest,
    ConnectionCreateRequest, ConnectionUpdateRequest,
    AccountCreateRequest, AccountUpdateRequest,
    SecurityCreateRequest, SecurityUpdateRequest,
    HoldingCreateRequest, HoldingUpdateRequest,
    TransactionCreateRequest, TransactionUpdateRequest,
    SyncJobCreateRequest, SyncJobUpdateRequest,
    FileImportRequest, SourceType, ConnectionStatus,
    AccountType, AccountSubtype, SecurityType,
    TransactionType, SyncMode, SyncStatus
)
from app.domain.errors import NotFoundError, ConflictError, ValidationError


class TestPersonalFinanceAPI:
    """Test personal finance API endpoints"""
    
    @pytest.fixture
    def client(self):
        """Create test client"""
        return TestClient(app)
    
    def test_create_institution_success(self, client):
        """Test creating an institution successfully"""
        response = client.post("/api/v1/personal-finance/institutions/", json={
            "name": "Test Bank",
            "brand_key": "TESTBANK",
            "source_type": "AGGREGATOR",
            "logo_url": "https://example.com/logo.png"
        })
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "institution_id" in data
        assert data["institution"]["name"] == "Test Bank"
        assert data["institution"]["brand_key"] == "TESTBANK"
    
    def test_create_institution_validation_error(self, client):
        """Test creating an institution with validation error"""
        response = client.post("/api/v1/personal-finance/institutions/", json={
            "name": "",  # Invalid: empty name
            "brand_key": "TESTBANK",
            "source_type": "AGGREGATOR"
        })
        
        assert response.status_code == 400
        data = response.json()
        assert "detail" in data
        assert "validation error" in data["detail"].lower()
    
    def test_create_institution_duplicate_error(self, client):
        """Test creating an institution with duplicate brand key"""
        # First create an institution
        client.post("/api/v1/personal-finance/institutions/", json={
            "name": "Test Bank",
            "brand_key": "TESTBANK",
            "source_type": "AGGREGATOR"
        })
        
        # Try to create the same institution again
        response = client.post("/api/v1/personal-finance/institutions/", json={
            "name": "Another Bank",
            "brand_key": "TESTBANK",  # Same brand key
            "source_type": "AGGREGATOR"
        })
        
        assert response.status_code == 409
        data = response.json()
        assert "already exists" in data["detail"].lower()
    
    def test_list_institutions_success(self, client):
        """Test listing institutions successfully"""
        response = client.get("/api/v1/personal-finance/institutions/")
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "institutions" in data
        assert isinstance(data["institutions"], list)
    
    def test_list_institutions_with_filters(self, client):
        """Test listing institutions with filters"""
        response = client.get("/api/v1/personal-finance/institutions/?source_type=SNAPTRADE&limit=10")
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "institutions" in data
        assert isinstance(data["institutions"], list)
    
    def test_get_institution_by_id_success(self, client):
        """Test getting an institution by ID successfully"""
        # First create an institution
        create_response = client.post("/api/v1/personal-finance/institutions/", json={
            "name": "Test Bank",
            "brand_key": "TESTBANK",
            "source_type": "AGGREGATOR"
        })
        institution_id = create_response.json()["institution_id"]
        
        # Get the institution
        response = client.get(f"/api/v1/personal-finance/institutions/{institution_id}")
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "institution" in data
        assert data["institution"]["id"] == institution_id
    
    def test_get_institution_by_id_not_found(self, client):
        """Test getting a non-existent institution"""
        response = client.get("/api/v1/personal-finance/institutions/999")
        
        assert response.status_code == 404
        data = response.json()
        assert "detail" in data
        assert "not found" in data["detail"].lower()
    
    def test_update_institution_success(self, client):
        """Test updating an institution successfully"""
        # First create an institution
        create_response = client.post("/api/v1/personal-finance/institutions/", json={
            "name": "Test Bank",
            "brand_key": "TESTBANK",
            "source_type": "AGGREGATOR"
        })
        institution_id = create_response.json()["institution_id"]
        
        # Update the institution
        response = client.put(f"/api/v1/personal-finance/institutions/{institution_id}", json={
            "name": "Updated Bank Name"
        })
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "institution" in data
        assert data["institution"]["name"] == "Updated Bank Name"
    
    def test_update_institution_not_found(self, client):
        """Test updating a non-existent institution"""
        response = client.put("/api/v1/personal-finance/institutions/999", json={
            "name": "Updated Bank Name"
        })
        
        assert response.status_code == 404
        data = response.json()
        assert "detail" in data
        assert "not found" in data["detail"].lower()
    
    def test_delete_institution_success(self, client):
        """Test deleting an institution successfully"""
        # First create an institution
        create_response = client.post("/api/v1/personal-finance/institutions/", json={
            "name": "Test Bank",
            "brand_key": "TESTBANK",
            "source_type": "AGGREGATOR"
        })
        institution_id = create_response.json()["institution_id"]
        
        # Delete the institution
        response = client.delete(f"/api/v1/personal-finance/institutions/{institution_id}")
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "deleted successfully" in data["message"].lower()
    
    def test_delete_institution_not_found(self, client):
        """Test deleting a non-existent institution"""
        response = client.delete("/api/v1/personal-finance/institutions/999")
        
        assert response.status_code == 404
        data = response.json()
        assert "detail" in data
        assert "not found" in data["detail"].lower()
    
    def test_search_institutions_success(self, client):
        """Test searching institutions successfully"""
        response = client.get("/api/v1/personal-finance/institutions/search?q=Test")
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "institutions" in data
        assert isinstance(data["institutions"], list)
    
    def test_search_institutions_invalid_query(self, client):
        """Test searching institutions with invalid query"""
        response = client.get("/api/v1/personal-finance/institutions/search?q=A")
        
        assert response.status_code == 400
        data = response.json()
        assert "detail" in data
        assert "at least 2 characters" in data["detail"].lower()
    
    def test_create_connection_success(self, client):
        """Test creating a connection successfully"""
        # First create an institution
        institution_response = client.post("/api/v1/personal-finance/institutions/", json={
            "name": "Test Bank",
            "brand_key": "TESTBANK",
            "source_type": "AGGREGATOR"
        })
        institution_id = institution_response.json()["institution_id"]
        
        # Create a connection
        response = client.post("/api/v1/personal-finance/connections/", json={
            "user_id": "user123",
            "institution_id": institution_id,
            "source_type": "SNAPTRADE",
            "auth_data": {"api_key": "test_key"},
            "status": "ACTIVE"
        })
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "connection_id" in data
        assert data["connection"]["user_id"] == "user123"
        assert data["connection"]["institution_id"] == institution_id
    
    def test_create_connection_institution_not_found(self, client):
        """Test creating a connection with non-existent institution"""
        response = client.post("/api/v1/personal-finance/connections/", json={
            "user_id": "user123",
            "institution_id": 999,
            "source_type": "SNAPTRADE",
            "auth_data": {"api_key": "test_key"}
        })
        
        assert response.status_code == 404
        data = response.json()
        assert "detail" in data
        assert "not found" in data["detail"].lower()
    
    def test_list_connections_success(self, client):
        """Test listing connections successfully"""
        response = client.get("/api/v1/personal-finance/connections/")
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "connections" in data
        assert isinstance(data["connections"], list)
    
    def test_list_connections_with_filters(self, client):
        """Test listing connections with filters"""
        response = client.get("/api/v1/personal-finance/connections/?user_id=user123&status=ACTIVE&limit=10")
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "connections" in data
        assert isinstance(data["connections"], list)
    
    def test_get_connection_by_id_success(self, client):
        """Test getting a connection by ID successfully"""
        # First create a connection
        create_response = client.post("/api/v1/personal-finance/connections/", json={
            "user_id": "user123",
            "institution_id": 1,
            "source_type": "SNAPTRADE",
            "auth_data": {"api_key": "test_key"}
        })
        connection_id = create_response.json()["connection_id"]
        
        # Get the connection
        response = client.get(f"/api/v1/personal-finance/connections/{connection_id}")
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "connection" in data
        assert data["connection"]["id"] == connection_id
    
    def test_get_connection_by_id_not_found(self, client):
        """Test getting a non-existent connection"""
        response = client.get("/api/v1/personal-finance/connections/999")
        
        assert response.status_code == 404
        data = response.json()
        assert "detail" in data
        assert "not found" in data["detail"].lower()
    
    def test_update_connection_success(self, client):
        """Test updating a connection successfully"""
        # First create a connection
        create_response = client.post("/api/v1/personal-finance/connections/", json={
            "user_id": "user123",
            "institution_id": 1,
            "source_type": "SNAPTRADE",
            "auth_data": {"api_key": "test_key"}
        })
        connection_id = create_response.json()["connection_id"]
        
        # Update the connection
        response = client.put(f"/api/v1/personal-finance/connections/{connection_id}", json={
            "status": "NEEDS_REAUTH"
        })
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "connection" in data
        assert data["connection"]["status"] == "NEEDS_REAUTH"
    
    def test_update_connection_not_found(self, client):
        """Test updating a non-existent connection"""
        response = client.put("/api/v1/personal-finance/connections/999", json={
            "status": "NEEDS_REAUTH"
        })
        
        assert response.status_code == 404
        data = response.json()
        assert "detail" in data
        assert "not found" in data["detail"].lower()
    
    def test_delete_connection_success(self, client):
        """Test deleting a connection successfully"""
        # First create a connection
        create_response = client.post("/api/v1/personal-finance/connections/", json={
            "user_id": "user123",
            "institution_id": 1,
            "source_type": "SNAPTRADE",
            "auth_data": {"api_key": "test_key"}
        })
        connection_id = create_response.json()["connection_id"]
        
        # Delete the connection
        response = client.delete(f"/api/v1/personal-finance/connections/{connection_id}")
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "deleted successfully" in data["message"].lower()
    
    def test_delete_connection_not_found(self, client):
        """Test deleting a non-existent connection"""
        response = client.delete("/api/v1/personal-finance/connections/999")
        
        assert response.status_code == 404
        data = response.json()
        assert "detail" in data
        assert "not found" in data["detail"].lower()
    
    def test_test_connection_success(self, client):
        """Test connection testing successfully"""
        # First create a connection
        create_response = client.post("/api/v1/personal-finance/connections/", json={
            "user_id": "user123",
            "institution_id": 1,
            "source_type": "SNAPTRADE",
            "auth_data": {"api_key": "test_key"}
        })
        connection_id = create_response.json()["connection_id"]
        
        # Test the connection
        response = client.post(f"/api/v1/personal-finance/connections/{connection_id}/test")
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "test_result" in data
    
    def test_test_connection_not_found(self, client):
        """Test connection testing when connection not found"""
        response = client.post("/api/v1/personal-finance/connections/999/test")
        
        assert response.status_code == 404
        data = response.json()
        assert "detail" in data
        assert "not found" in data["detail"].lower()
    
    def test_trigger_sync_success(self, client):
        """Test triggering sync successfully"""
        # First create a connection
        create_response = client.post("/api/v1/personal-finance/connections/", json={
            "user_id": "user123",
            "institution_id": 1,
            "source_type": "SNAPTRADE",
            "auth_data": {"api_key": "test_key"}
        })
        connection_id = create_response.json()["connection_id"]
        
        # Trigger sync
        response = client.post(f"/api/v1/personal-finance/connections/{connection_id}/sync")
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "sync_result" in data
    
    def test_trigger_sync_not_found(self, client):
        """Test triggering sync when connection not found"""
        response = client.post("/api/v1/personal-finance/connections/999/sync")
        
        assert response.status_code == 404
        data = response.json()
        assert "detail" in data
        assert "not found" in data["detail"].lower()
    
    def test_get_connections_needing_reauth(self, client):
        """Test getting connections needing re-authentication"""
        response = client.get("/api/v1/personal-finance/connections/needing-reauth")
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "connections" in data
        assert isinstance(data["connections"], list)
    
    def test_create_account_success(self, client):
        """Test creating an account successfully"""
        # First create a connection
        connection_response = client.post("/api/v1/personal-finance/connections/", json={
            "user_id": "user123",
            "institution_id": 1,
            "source_type": "SNAPTRADE",
            "auth_data": {"api_key": "test_key"}
        })
        connection_id = connection_response.json()["connection_id"]
        
        # Create an account
        response = client.post("/api/v1/personal-finance/accounts/", json={
            "connection_id": connection_id,
            "external_account_id": "ACC123456",
            "name": "Primary Checking",
            "account_type": "CASH",
            "account_subtype": "CHECKING",
            "currency": "USD"
        })
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "account_id" in data
        assert data["account"]["name"] == "Primary Checking"
    
    def test_create_account_connection_not_found(self, client):
        """Test creating an account with non-existent connection"""
        response = client.post("/api/v1/personal-finance/accounts/", json={
            "connection_id": 999,
            "external_account_id": "ACC123456",
            "name": "Primary Checking",
            "account_type": "CASH",
            "currency": "USD"
        })
        
        assert response.status_code == 404
        data = response.json()
        assert "detail" in data
        assert "not found" in data["detail"].lower()
    
    def test_list_accounts_success(self, client):
        """Test listing accounts successfully"""
        response = client.get("/api/v1/personal-finance/accounts/")
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "accounts" in data
        assert isinstance(data["accounts"], list)
    
    def test_list_accounts_with_filters(self, client):
        """Test listing accounts with filters"""
        response = client.get("/api/v1/personal-finance/accounts/?account_type=CASH&is_closed=false&limit=10")
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "accounts" in data
        assert isinstance(data["accounts"], list)
    
    def test_get_account_by_id_success(self, client):
        """Test getting an account by ID successfully"""
        # First create an account
        create_response = client.post("/api/v1/personal-finance/accounts/", json={
            "connection_id": 1,
            "external_account_id": "ACC123456",
            "name": "Primary Checking",
            "account_type": "CASH",
            "account_subtype": "CHECKING",
            "currency": "USD"
        })
        account_id = create_response.json()["account_id"]
        
        # Get the account
        response = client.get(f"/api/v1/personal-finance/accounts/{account_id}")
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "account" in data
        assert data["account"]["id"] == account_id
    
    def test_get_account_by_id_not_found(self, client):
        """Test getting a non-existent account"""
        response = client.get("/api/v1/personal-finance/accounts/999")
        
        assert response.status_code == 404
        data = response.json()
        assert "detail" in data
        assert "not found" in data["detail"].lower()
    
    def test_update_account_success(self, client):
        """Test updating an account successfully"""
        # First create an account
        create_response = client.post("/api/v1/personal-finance/accounts/", json={
            "connection_id": 1,
            "external_account_id": "ACC123456",
            "name": "Primary Checking",
            "account_type": "CASH",
            "account_subtype": "CHECKING",
            "currency": "USD"
        })
        account_id = create_response.json()["account_id"]
        
        # Update the account
        response = client.put(f"/api/v1/personal-finance/accounts/{account_id}", json={
            "name": "Updated Checking Account"
        })
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "account" in data
        assert data["account"]["name"] == "Updated Checking Account"
    
    def test_update_account_not_found(self, client):
        """Test updating a non-existent account"""
        response = client.put("/api/v1/personal-finance/accounts/999", json={
            "name": "Updated Checking Account"
        })
        
        assert response.status_code == 404
        data = response.json()
        assert "detail" in data
        assert "not found" in data["detail"].lower()
    
    def test_delete_account_success(self, client):
        """Test deleting an account successfully"""
        # First create an account
        create_response = client.post("/api/v1/personal-finance/accounts/", json={
            "connection_id": 1,
            "external_account_id": "ACC123456",
            "name": "Primary Checking",
            "account_type": "CASH",
            "account_subtype": "CHECKING",
            "currency": "USD"
        })
        account_id = create_response.json()["account_id"]
        
        # Delete the account
        response = client.delete(f"/api/v1/personal-finance/accounts/{account_id}")
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "deleted successfully" in data["message"].lower()
    
    def test_delete_account_not_found(self, client):
        """Test deleting a non-existent account"""
        response = client.delete("/api/v1/personal-finance/accounts/999")
        
        assert response.status_code == 404
        data = response.json()
        assert "detail" in data
        assert "not found" in data["detail"].lower()
    
    def test_search_accounts_success(self, client):
        """Test searching accounts successfully"""
        response = client.get("/api/v1/personal-finance/accounts/search?q=Checking")
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "accounts" in data
        assert isinstance(data["accounts"], list)
    
    def test_search_accounts_invalid_query(self, client):
        """Test searching accounts with invalid query"""
        response = client.get("/api/v1/personal-finance/accounts/search?q=A")
        
        assert response.status_code == 400
        data = response.json()
        assert "detail" in data
        assert "at least 2 characters" in data["detail"].lower()
    
    def test_create_security_success(self, client):
        """Test creating a security successfully"""
        response = client.post("/api/v1/personal-finance/securities/", json={
            "symbol": "AAPL",
            "name": "Apple Inc.",
            "security_type": "EQUITY",
            "cusip": "037833100"
        })
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "security_id" in data
        assert data["security"]["symbol"] == "AAPL"
    
    def test_create_security_validation_error(self, client):
        """Test creating a security with validation error"""
        response = client.post("/api/v1/personal-finance/securities/", json={
            "symbol": "",  # Invalid: empty symbol
            "name": "Apple Inc.",
            "security_type": "EQUITY"
        })
        
        assert response.status_code == 400
        data = response.json()
        assert "detail" in data
        assert "validation error" in data["detail"].lower()
    
    def test_get_security_by_id_success(self, client):
        """Test getting a security by ID successfully"""
        # First create a security
        create_response = client.post("/api/v1/personal-finance/securities/", json={
            "symbol": "AAPL",
            "name": "Apple Inc.",
            "security_type": "EQUITY",
            "cusip": "037833100"
        })
        security_id = create_response.json()["security_id"]
        
        # Get the security
        response = client.get(f"/api/v1/personal-finance/securities/{security_id}")
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "security" in data
        assert data["security"]["id"] == security_id
    
    def test_get_security_by_id_not_found(self, client):
        """Test getting a non-existent security"""
        response = client.get("/api/v1/personal-finance/securities/999")
        
        assert response.status_code == 404
        data = response.json()
        assert "detail" in data
        assert "not found" in data["detail"].lower()
    
    def test_get_security_by_symbol_success(self, client):
        """Test getting a security by symbol successfully"""
        # First create a security
        create_response = client.post("/api/v1/personal-finance/securities/", json={
            "symbol": "AAPL",
            "name": "Apple Inc.",
            "security_type": "EQUITY",
            "cusip": "037833100"
        })
        
        # Get the security by symbol
        response = client.get("/api/v1/personal-finance/securities/symbol/AAPL")
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "security" in data
        assert data["security"]["symbol"] == "AAPL"
    
    def test_get_security_by_symbol_not_found(self, client):
        """Test getting a security by symbol when not found"""
        response = client.get("/api/v1/personal-finance/securities/symbol/UNKNOWN")
        
        assert response.status_code == 404
        data = response.json()
        assert "detail" in data
        assert "not found" in data["detail"].lower()
    
    def test_update_security_success(self, client):
        """Test updating a security successfully"""
        # First create a security
        create_response = client.post("/api/v1/personal-finance/securities/", json={
            "symbol": "AAPL",
            "name": "Apple Inc.",
            "security_type": "EQUITY",
            "cusip": "037833100"
        })
        security_id = create_response.json()["security_id"]
        
        # Update the security
        response = client.put(f"/api/v1/personal-finance/securities/{security_id}", json={
            "name": "Updated Apple Inc."
        })
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "security" in data
        assert data["security"]["name"] == "Updated Apple Inc."
    
    def test_update_security_not_found(self, client):
        """Test updating a non-existent security"""
        response = client.put("/api/v1/personal-finance/securities/999", json={
            "name": "Updated Apple Inc."
        })
        
        assert response.status_code == 404
        data = response.json()
        assert "detail" in data
        assert "not found" in data["detail"].lower()
    
    def test_delete_security_success(self, client):
        """Test deleting a security successfully"""
        # First create a security
        create_response = client.post("/api/v1/personal-finance/securities/", json={
            "symbol": "AAPL",
            "name": "Apple Inc.",
            "security_type": "EQUITY",
            "cusip": "037833100"
        })
        security_id = create_response.json()["security_id"]
        
        # Delete the security
        response = client.delete(f"/api/v1/personal-finance/securities/{security_id}")
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "deleted successfully" in data["message"].lower()
    
    def test_delete_security_not_found(self, client):
        """Test deleting a non-existent security"""
        response = client.delete("/api/v1/personal-finance/securities/999")
        
        assert response.status_code == 404
        data = response.json()
        assert "detail" in data
        assert "not found" in data["detail"].lower()
    
    def test_search_securities_success(self, client):
        """Test searching securities successfully"""
        response = client.get("/api/v1/personal-finance/securities/search?q=Apple")
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "securities" in data
        assert isinstance(data["securities"], list)
    
    def test_search_securities_invalid_query(self, client):
        """Test searching securities with invalid query"""
        response = client.get("/api/v1/personal-finance/securities/search?q=")
        
        assert response.status_code == 400
        data = response.json()
        assert "detail" in data
        assert "at least 1 character" in data["detail"].lower()
    
    def test_get_popular_securities_success(self, client):
        """Test getting popular securities"""
        response = client.get("/api/v1/personal-finance/securities/popular?limit=10")
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "securities" in data
        assert isinstance(data["securities"], list)
    
    def test_upload_file_csv_success(self, client):
        """Test uploading and importing a CSV file"""
        csv_content = "symbol,date,type,amount\nAAPL,2023-01-01,BUY,100\nMSFT,2023-01-02,SELL,50"
        files = {"file": ("test.csv", csv_content, "text/csv")}
        
        response = client.post(
            "/api/v1/personal-finance/import/upload",
            files=files,
            params={"file_type": "csv"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "import_result" in data
    
    def test_upload_file_ofx_success(self, client):
        """Test uploading and importing an OFX file"""
        ofx_content = """
        OFXHEADER:100
        BANKID:123456789
        ACCOUNTTYPE:CHECKING
        DTSTART:20230101
        DTPOSTED:20230101
        TRNTAMT:100.00
        TRNAMT:100.00
        FITID:DEPOSIT
        MEMO:Test deposit
        """
        files = {"file": ("test.ofx", ofx_content, "application/x-ofx")}
        
        response = client.post(
            "/api/v1/personal-finance/import/upload",
            files=files,
            params={"file_type": "ofx"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "import_result" in data
    
    def test_upload_file_invalid_type(self, client):
        """Test uploading file with invalid type"""
        files = {"file": ("test.txt", "test content", "text/plain")}
        
        response = client.post(
            "/api/v1/personal-finance/import/upload",
            files=files,
            params={"file_type": "invalid"}
        )
        
        assert response.status_code == 400
        data = response.json()
        assert "detail" in data
        assert "regex" in data["detail"].lower()
    
    def test_get_portfolio_performance_success(self, client):
        """Test getting portfolio performance metrics"""
        response = client.get("/api/v1/person-finance/analytics/portfolio-performance")
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "performance" in data
    
    def test_get_account_performance_success(self, client):
        """Test getting account performance metrics"""
        # First create an account
        create_response = client.post("/api/v1/person-finance/accounts/", json={
            "connection_id": 1,
            "external_account_id": "ACC123456",
            "name": "Primary Checking",
            "account_type": "CASH",
            "account_subtype": "CHECKING",
            "currency": "USD"
        })
        account_id = create_response.json()["account_id"]
        
        response = client.get(f"/api/v1/person-finance/analytics/account-performance/{account_id}")
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "performance" in data
    
    def test_get_asset_allocation_success(self, client):
        """Test getting asset allocation breakdown"""
        response = client.get("/api/v1/personal-finance/analytics/asset-allocation")
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "asset_allocation" in data
    
    def test_get_income_expense_analysis_success(self, client):
        """Test getting income and expense analysis"""
        response = client.get("/api/v1/person-finance/analytics/income-expense-analysis")
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "income_expense_analysis" in data
    
    def test_sync_all_connections_success(self, client):
        """Test syncing all connections"""
        response = client.post("/api/v1/personal-finance/sync-all")
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "sync_results" in data
        assert isinstance(data["sync_results"], list)
    
    def test_refresh_all_tokens_success(self, client):
        """Test refreshing all authentication tokens"""
        response = client.post("/api/v1/person-finance/refresh-all-tokens")
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "refresh_results" in data
        assert isinstance(data["refresh_results"], list)
    
    def test_get_sync_status_success(self, client):
        """Test getting sync status for a connection"""
        # First create a connection
        create_response = client.post("/api/v1/person-finance/connections/", json={
            "user_id": "user123",
            "institution_id": 1,
            "source_type": "SNAPTRADE",
            "auth_data": {"api_key": "test_key"}
        })
        connection_id = create_response.json()["connection_id"]
        
        response = client.get(f"/api/v1/person-finance/sync-status/{connection_id}")
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "connection_status" in data
