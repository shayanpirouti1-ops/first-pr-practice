"""Tradovate trading manager with connection pooling"""
import logging
from typing import Optional, Dict, List, Any
from .tradovate import TradovateClient, TradovateAuthError, TradovateAPIError

logger = logging.getLogger(__name__)

class TradovateManager:
    """Manager for Tradovate client connections"""
    
    def __init__(self, api_key: str, api_secret: str, sandbox: bool = False):
        self.api_key = api_key
        self.api_secret = api_secret
        self.sandbox = sandbox
        self.client: Optional[TradovateClient] = None
    
    async def initialize(self) -> bool:
        """
        Initialize and authenticate the client
        
        Returns:
            True if initialization successful
        """
        try:
            self.client = TradovateClient(self.api_key, self.api_secret, self.sandbox)
            await self.client.authenticate()
            logger.info("Tradovate manager initialized")
            return True
        except TradovateAuthError as e:
            logger.error(f"Failed to initialize Tradovate: {str(e)}")
            return False
    
    async def get_client(self) -> TradovateClient:
        """
        Get authenticated client
        
        Returns:
            TradovateClient instance
        
        Raises:
            RuntimeError: If client not initialized
        """
        if not self.client:
            raise RuntimeError("Tradovate manager not initialized")
        return self.client
    
    async def close(self):
        """Close client connection"""
        if self.client:
            await self.client.close()
            self.client = None
    
    async def __aenter__(self):
        await self.initialize()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()
