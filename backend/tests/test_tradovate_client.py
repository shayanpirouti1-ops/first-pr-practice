"""Tests for Tradovate API client"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import json
from datetime import datetime, timedelta

from app.traders.tradovate import (
    TradovateClient, 
    TradovateAuthError, 
    TradovateAPIError
)


class TestTradovateClient:
    """Test cases for TradovateClient"""
    
    @pytest.fixture
    def client(self):
        return TradovateClient(
            api_key="test_key",
            api_secret="test_secret",
            sandbox=True
        )
    
    @pytest.mark.asyncio
    async def test_initialization(self, client):
        """Test client initialization"""
        assert client.api_key == "test_key"
        assert client.api_secret == "test_secret"
        assert client.sandbox is True
        assert client.access_token is None
    
    @pytest.mark.asyncio
    async def test_authenticate_success(self, client):
        """Test successful authentication"""
        with patch.object(client, '_make_request') as mock_request:
            mock_request.return_value = {
                'accessToken': 'test_token_123',
                'userId': 12345,
                'expiresIn': 3600
            }
            
            result = await client.authenticate()
            
            assert result is True
            assert client.access_token == 'test_token_123'
            assert client.user_id == 12345
    
    @pytest.mark.asyncio
    async def test_authenticate_failure(self, client):
        """Test authentication failure"""
        with patch.object(client, '_make_request') as mock_request:
            mock_request.side_effect = TradovateAPIError("Invalid credentials")
            
            with pytest.raises(TradovateAuthError):
                await client.authenticate()
    
    @pytest.mark.asyncio
    async def test_get_accounts(self, client):
        """Test getting accounts"""
        client.access_token = "test_token"
        
        with patch.object(client, '_make_request') as mock_request:
            mock_request.return_value = {
                'accounts': [
                    {'id': 1, 'name': 'Account 1'},
                    {'id': 2, 'name': 'Account 2'}
                ]
            }
            
            accounts = await client.get_accounts()
            
            assert len(accounts) == 2
            assert accounts[0]['id'] == 1
            assert accounts[1]['id'] == 2
    
    @pytest.mark.asyncio
    async def test_get_positions(self, client):
        """Test getting open positions"""
        client.access_token = "test_token"
        
        with patch.object(client, '_make_request') as mock_request:
            mock_request.return_value = {
                'positions': [
                    {
                        'id': 1,
                        'symbol': 'ES',
                        'quantity': 2,
                        'entryPrice': 4500.0
                    }
                ]
            }
            
            positions = await client.get_positions(account_id=123)
            
            assert len(positions) == 1
            assert positions[0]['symbol'] == 'ES'
            assert positions[0]['quantity'] == 2
    
    @pytest.mark.asyncio
    async def test_get_balance(self, client):
        """Test getting account balance"""
        client.access_token = "test_token"
        
        with patch.object(client, 'get_account') as mock_get_account:
            mock_get_account.return_value = {
                'cash': 50000.0,
                'tradingPower': 200000.0,
                'equity': 250000.0,
                'maintenanceExcess': 125000.0
            }
            
            balance = await client.get_balance(account_id=123)
            
            assert balance['balance'] == 50000.0
            assert balance['buying_power'] == 200000.0
            assert balance['equity'] == 250000.0
    
    @pytest.mark.asyncio
    async def test_place_market_order(self, client):
        """Test placing a market order"""
        client.access_token = "test_token"
        
        with patch.object(client, '_make_request') as mock_request:
            mock_request.return_value = {
                'orderId': 456,
                'symbol': 'ES',
                'quantity': 2,
                'status': 'Pending'
            }
            
            order = await client.place_order(
                account_id=123,
                symbol='ES',
                quantity=2,
                order_type='Market'
            )
            
            assert order['orderId'] == 456
            assert order['symbol'] == 'ES'
            assert order['quantity'] == 2
    
    @pytest.mark.asyncio
    async def test_place_limit_order(self, client):
        """Test placing a limit order"""
        client.access_token = "test_token"
        
        with patch.object(client, '_make_request') as mock_request:
            mock_request.return_value = {
                'orderId': 457,
                'symbol': 'ES',
                'quantity': 1,
                'price': 4500.0,
                'status': 'Working'
            }
            
            order = await client.place_order(
                account_id=123,
                symbol='ES',
                quantity=1,
                order_type='Limit',
                price=4500.0
            )
            
            assert order['orderId'] == 457
            assert order['price'] == 4500.0
    
    @pytest.mark.asyncio
    async def test_place_stop_limit_order(self, client):
        """Test placing a stop-limit order"""
        client.access_token = "test_token"
        
        with patch.object(client, '_make_request') as mock_request:
            mock_request.return_value = {
                'orderId': 458,
                'symbol': 'ES',
                'quantity': 1,
                'stopPrice': 4490.0,
                'price': 4485.0,
                'status': 'Working'
            }
            
            order = await client.place_order(
                account_id=123,
                symbol='ES',
                quantity=1,
                order_type='StopLimit',
                price=4485.0,
                stop_price=4490.0
            )
            
            assert order['orderId'] == 458
            assert order['stopPrice'] == 4490.0
    
    @pytest.mark.asyncio
    async def test_cancel_order(self, client):
        """Test cancelling an order"""
        client.access_token = "test_token"
        
        with patch.object(client, '_make_request') as mock_request:
            mock_request.return_value = {
                'orderId': 456,
                'status': 'Cancelled'
            }
            
            result = await client.cancel_order(order_id=456)
            
            assert result['orderId'] == 456
            assert result['status'] == 'Cancelled'
    
    @pytest.mark.asyncio
    async def test_modify_order(self, client):
        """Test modifying an order"""
        client.access_token = "test_token"
        
        with patch.object(client, '_make_request') as mock_request:
            mock_request.return_value = {
                'orderId': 456,
                'quantity': 3,
                'price': 4505.0
            }
            
            result = await client.modify_order(
                order_id=456,
                quantity=3,
                price=4505.0
            )
            
            assert result['orderId'] == 456
            assert result['quantity'] == 3
            assert result['price'] == 4505.0
    
    @pytest.mark.asyncio
    async def test_get_orders(self, client):
        """Test getting orders"""
        client.access_token = "test_token"
        
        with patch.object(client, '_make_request') as mock_request:
            mock_request.return_value = {
                'orders': [
                    {'orderId': 1, 'status': 'Working'},
                    {'orderId': 2, 'status': 'Working'}
                ]
            }
            
            orders = await client.get_orders(account_id=123, status='Working')
            
            assert len(orders) == 2
    
    @pytest.mark.asyncio
    async def test_get_fills(self, client):
        """Test getting filled orders"""
        client.access_token = "test_token"
        
        with patch.object(client, '_make_request') as mock_request:
            mock_request.return_value = {
                'fills': [
                    {
                        'orderId': 1,
                        'symbol': 'ES',
                        'quantity': 2,
                        'fillPrice': 4500.0
                    }
                ]
            }
            
            fills = await client.get_fills(account_id=123, days=1)
            
            assert len(fills) == 1
            assert fills[0]['fillPrice'] == 4500.0
    
    @pytest.mark.asyncio
    async def test_context_manager(self, client):
        """Test using client as async context manager"""
        with patch.object(client, 'authenticate'):
            with patch.object(client, 'close'):
                async with client as ctx_client:
                    assert ctx_client == client
