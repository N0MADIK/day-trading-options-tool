"""Base integration class for external services"""
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from datetime import datetime
import aiohttp
import asyncio
from app.domain.errors import ExternalServiceError, UnauthorizedError


class BaseIntegration(ABC):
    """Abstract base class for external service integrations"""
    
    def __init__(self):
        self.session: Optional[aiohttp.ClientSession] = None
        self._retry_count = 3
        self._retry_delay = 1
    
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    @abstractmethod
    async def validate_credentials(self, credentials: Dict[str, str]) -> bool:
        """Validate user credentials for the service"""
        pass
    
    @abstractmethod
    async def test_connection(self, credentials: Dict[str, str]) -> Dict[str, Any]:
        """Test the connection to the service"""
        pass
    
    @abstractmethod
    async def get_accounts(self, credentials: Dict[str, str]) -> Dict[str, Any]:
        """Get user accounts from the service"""
        pass
    
    async def _make_request(
        self,
        method: str,
        url: str,
        headers: Optional[Dict[str, str]] = None,
        params: Optional[Dict[str, Any]] = None,
        data: Optional[Dict[str, Any]] = None,
        json_data: Optional[Dict[str, Any]] = None,
        retry_count: Optional[int] = None
    ) -> Dict[str, Any]:
        """Make HTTP request with retry logic"""
        retry_count = retry_count or self._retry_count
        
        for attempt in range(retry_count):
            try:
                if not self.session:
                    self.session = aiohttp.ClientSession()
                
                async with self.session.request(
                    method,
                    url,
                    headers=headers,
                    params=params,
                    data=data,
                    json=json_data
                ) as response:
                    response_data = await response.json() if response.content_type == 'application/json' else await response.text()
                    
                    if response.status == 401:
                        raise UnauthorizedError("Invalid credentials or authentication expired")
                    
                    if response.status >= 400:
                        error_msg = response_data.get('error', response_data) if isinstance(response_data, dict) else str(response_data)
                        raise ExternalServiceError(f"Request failed: {error_msg}")
                    
                    return response_data
                    
            except (aiohttp.ClientError, asyncio.TimeoutError) as e:
                if attempt == retry_count - 1:
                    raise ExternalServiceError(f"Failed to connect to service: {str(e)}")
                await asyncio.sleep(self._retry_delay * (attempt + 1))
    
    def _build_headers(self, auth_token: Optional[str] = None, api_key: Optional[str] = None) -> Dict[str, str]:
        """Build common headers for API requests"""
        headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }
        
        if auth_token:
            headers['Authorization'] = f'Bearer {auth_token}'
        
        if api_key:
            headers['API-Key'] = api_key
            
        return headers
