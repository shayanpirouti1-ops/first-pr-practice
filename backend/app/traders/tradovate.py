"""Tradovate API integration module"""
import aiohttp
import asyncio
import json
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
import logging
from functools import wraps

logger = logging.getLogger(__name__)

class TradovateAuthError(Exception):
    """Raised when authentication fails"""
    pass

class TradovateAPIError(Exception):
    """Raised when API request fails"""
    pass

class TradovateClient:
    """Client for Tradovate API"""
    
    # API Endpoints
    PROD_URL = "https://api.tradovate.com"
    SANDBOX_URL = "https://sandbox.tradovate.com"
    
    def __init__(self, api_key: str, api_secret: str, sandbox: bool = False):
        """
        Initialize Tradovate client
        
        Args:
            api_key: API key from Tradovate
            api_secret: API secret from Tradovate
            sandbox: Use sandbox environment if True
        """
        self.api_key = api_key
        self.api_secret = api_secret
        self.sandbox = sandbox
        self.base_url = self.SANDBOX_URL if sandbox else self.PROD_URL
        self.session: Optional[aiohttp.ClientSession] = None
        self.access_token: Optional[str] = None
        self.token_expires_at: Optional[datetime] = None
        self.user_id: Optional[int] = None
    
    async def _ensure_session(self):
        """Ensure aiohttp session is created"""
        if self.session is None:
            self.session = aiohttp.ClientSession()
    
    async def _make_request(self, method: str, endpoint: str, data: Optional[Dict] = None, 
                          params: Optional[Dict] = None, authenticated: bool = True) -> Dict[str, Any]:
        """
        Make HTTP request to Tradovate API
        
        Args:
            method: HTTP method (GET, POST, etc.)
            endpoint: API endpoint path
            data: Request body data
            params: Query parameters
            authenticated: Whether request requires authentication
        
        Returns:
            Response data as dictionary
        
        Raises:
            TradovateAPIError: If request fails
        """
        await self._ensure_session()
        
        url = f"{self.base_url}{endpoint}"
        headers = {"Content-Type": "application/json"}
        
        # Add auth token if needed and available
        if authenticated and self.access_token:
            headers["Authorization"] = f"Bearer {self.access_token}"
        
        try:
            async with self.session.request(
                method, url, json=data, params=params, headers=headers, timeout=aiohttp.ClientTimeout(total=30)
            ) as response:
                response_data = await response.json()
                
                if response.status not in [200, 201]:
                    error_msg = response_data.get('errorText', f"HTTP {response.status}")
                    raise TradovateAPIError(f"API Error: {error_msg}")
                
                return response_data
        except aiohttp.ClientError as e:
            raise TradovateAPIError(f"Network error: {str(e)}")
        except json.JSONDecodeError as e:
            raise TradovateAPIError(f"Invalid JSON response: {str(e)}")
    
    async def authenticate(self) -> bool:
        """
        Authenticate with Tradovate API using API key and secret
        
        Returns:
            True if authentication successful
        
        Raises:
            TradovateAuthError: If authentication fails
        """
        try:
            response = await self._make_request(
                "POST",
                "/auth/login",
                data={
                    "apikey": self.api_key,
                    "apisecret": self.api_secret
                },
                authenticated=False
            )
            
            self.access_token = response.get('accessToken')
            self.user_id = response.get('userId')
            
            # Token expires in 1 hour by default, refresh at 55 minutes
            expires_in = response.get('expiresIn', 3600)
            self.token_expires_at = datetime.utcnow() + timedelta(seconds=expires_in - 300)
            
            logger.info(f"Authentication successful for user {self.user_id}")
            return True
        except TradovateAPIError as e:
            raise TradovateAuthError(f"Authentication failed: {str(e)}")
    
    async def _refresh_token_if_needed(self):
        """Refresh access token if it's about to expire"""
        if self.token_expires_at and datetime.utcnow() >= self.token_expires_at:
            await self.authenticate()
    
    async def get_accounts(self) -> List[Dict[str, Any]]:
        """
        Get all user accounts
        
        Returns:
            List of account dictionaries
        """
        await self._refresh_token_if_needed()
        
        response = await self._make_request("GET", "/account/accounts")
        return response.get('accounts', [])
    
    async def get_account(self, account_id: int) -> Dict[str, Any]:
        """
        Get specific account details
        
        Args:
            account_id: Account ID
        
        Returns:
            Account details
        """
        await self._refresh_token_if_needed()
        
        response = await self._make_request("GET", f"/account/accounts/{account_id}")
        return response
    
    async def get_positions(self, account_id: int) -> List[Dict[str, Any]]:
        """
        Get open positions for an account
        
        Args:
            account_id: Account ID
        
        Returns:
            List of position dictionaries
        """
        await self._refresh_token_if_needed()
        
        response = await self._make_request("GET", f"/account/accounts/{account_id}/positions")
        return response.get('positions', [])
    
    async def get_balance(self, account_id: int) -> Dict[str, Any]:
        """
        Get account balance and trading power
        
        Args:
            account_id: Account ID
        
        Returns:
            Balance information
        """
        await self._refresh_token_if_needed()
        
        account = await self.get_account(account_id)
        return {
            'balance': account.get('cash'),
            'buying_power': account.get('tradingPower'),
            'equity': account.get('equity'),
            'maintenance_excess': account.get('maintenanceExcess')
        }
    
    async def place_order(self, account_id: int, symbol: str, quantity: int, 
                         order_type: str, price: Optional[float] = None,
                         stop_price: Optional[float] = None,
                         time_in_force: str = "Day") -> Dict[str, Any]:
        """
        Place an order
        
        Args:
            account_id: Account ID
            symbol: Trading symbol (e.g., 'ES')
            quantity: Order quantity (positive for buy, negative for sell/short)
            order_type: 'Market', 'Limit', 'Stop', 'StopLimit'
            price: Limit price (required for Limit and StopLimit orders)
            stop_price: Stop price (required for Stop and StopLimit orders)
            time_in_force: 'Day', 'GTC', 'IOC', 'FOK'
        
        Returns:
            Order details including orderId
        
        Raises:
            TradovateAPIError: If order placement fails
        """
        await self._refresh_token_if_needed()
        
        order_data = {
            'accountId': account_id,
            'symbol': symbol,
            'orderQty': quantity,
            'orderType': order_type,
            'timeInForce': time_in_force
        }
        
        if price is not None:
            order_data['price'] = price
        if stop_price is not None:
            order_data['stopPrice'] = stop_price
        
        response = await self._make_request(
            "POST",
            "/order/placeorder",
            data=order_data
        )
        
        logger.info(f"Order placed: {symbol} {quantity} @ {order_type}")
        return response
    
    async def cancel_order(self, order_id: int) -> Dict[str, Any]:
        """
        Cancel an order
        
        Args:
            order_id: Order ID to cancel
        
        Returns:
            Cancelled order details
        """
        await self._refresh_token_if_needed()
        
        response = await self._make_request(
            "DELETE",
            f"/order/orders/{order_id}"
        )
        
        logger.info(f"Order {order_id} cancelled")
        return response
    
    async def modify_order(self, order_id: int, quantity: Optional[int] = None,
                          price: Optional[float] = None, 
                          stop_price: Optional[float] = None) -> Dict[str, Any]:
        """
        Modify an existing order
        
        Args:
            order_id: Order ID to modify
            quantity: New quantity
            price: New limit price
            stop_price: New stop price
        
        Returns:
            Modified order details
        """
        await self._refresh_token_if_needed()
        
        update_data = {}
        if quantity is not None:
            update_data['orderQty'] = quantity
        if price is not None:
            update_data['price'] = price
        if stop_price is not None:
            update_data['stopPrice'] = stop_price
        
        response = await self._make_request(
            "PATCH",
            f"/order/orders/{order_id}",
            data=update_data
        )
        
        logger.info(f"Order {order_id} modified")
        return response
    
    async def get_orders(self, account_id: int, status: str = "Working") -> List[Dict[str, Any]]:
        """
        Get orders for an account
        
        Args:
            account_id: Account ID
            status: Order status filter ('Working', 'Filled', 'Cancelled', 'All')
        
        Returns:
            List of orders
        """
        await self._refresh_token_if_needed()
        
        params = {'status': status}
        response = await self._make_request(
            "GET",
            f"/account/accounts/{account_id}/orders",
            params=params
        )
        return response.get('orders', [])
    
    async def get_order(self, order_id: int) -> Dict[str, Any]:
        """
        Get specific order details
        
        Args:
            order_id: Order ID
        
        Returns:
            Order details
        """
        await self._refresh_token_if_needed()
        
        response = await self._make_request("GET", f"/order/orders/{order_id}")
        return response
    
    async def get_fills(self, account_id: int, days: int = 1) -> List[Dict[str, Any]]:
        """
        Get filled orders (trades) for an account
        
        Args:
            account_id: Account ID
            days: Number of days to look back
        
        Returns:
            List of fills
        """
        await self._refresh_token_if_needed()
        
        params = {'accountId': account_id, 'days': days}
        response = await self._make_request(
            "GET",
            "/order/fills",
            params=params
        )
        return response.get('fills', [])
    
    async def get_contract(self, symbol: str) -> Dict[str, Any]:
        """
        Get contract details for a symbol
        
        Args:
            symbol: Trading symbol
        
        Returns:
            Contract details
        """
        await self._refresh_token_if_needed()
        
        response = await self._make_request("GET", f"/contract/contracts", params={'name': symbol})
        contracts = response.get('contracts', [])
        return contracts[0] if contracts else {}
    
    async def get_market_data(self, contract_id: int) -> Dict[str, Any]:
        """
        Get real-time market data for a contract
        
        Args:
            contract_id: Contract ID
        
        Returns:
            Market data (bid, ask, last, etc.)
        """
        await self._refresh_token_if_needed()
        
        response = await self._make_request("GET", f"/market/quotes/{contract_id}")
        return response
    
    async def close(self):
        """Close the aiohttp session"""
        if self.session:
            await self.session.close()
            self.session = None
    
    async def __aenter__(self):
        """Async context manager entry"""
        await self.authenticate()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        await self.close()
