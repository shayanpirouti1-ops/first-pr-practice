"""Tests for WebSocket manager"""
import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from app.websocket.manager import WebSocketManager, EventType
from app.websocket.quotes import QuoteHandler, Quote
from app.websocket.orders import OrderAndFillHandler, OrderNotification, FillNotification

class TestWebSocketManager:
    """Test cases for WebSocketManager"""
    
    @pytest.fixture
    def manager(self):
        return WebSocketManager(access_token="test_token", sandbox=True)
    
    def test_initialization(self, manager):
        """Test manager initialization"""
        assert manager.access_token == "test_token"
        assert manager.sandbox is True
        assert manager.running is False
        assert len(manager.callbacks) == 0
    
    def test_register_callback(self, manager):
        """Test registering callbacks"""
        async def callback(data):
            pass
        
        manager.on(EventType.QUOTE, callback)
        
        assert EventType.QUOTE in manager.callbacks
        assert callback in manager.callbacks[EventType.QUOTE]
    
    def test_unregister_callback(self, manager):
        """Test unregistering callbacks"""
        async def callback(data):
            pass
        
        manager.on(EventType.QUOTE, callback)
        manager.off(EventType.QUOTE, callback)
        
        assert len(manager.callbacks[EventType.QUOTE]) == 0
    
    @pytest.mark.asyncio
    async def test_emit_callback(self, manager):
        """Test emitting callbacks"""
        called = False
        call_data = None
        
        async def callback(data):
            nonlocal called, call_data
            called = True
            call_data = data
        
        manager.on(EventType.QUOTE, callback)
        await manager._emit(EventType.QUOTE, {"price": 100})
        
        assert called is True
        assert call_data["price"] == 100
    
    def test_get_subscriptions(self, manager):
        """Test getting subscriptions"""
        manager.subscriptions.add("quote:123")
        manager.subscriptions.add("order:456")
        
        subs = manager.get_subscriptions()
        assert len(subs) == 2
        assert "quote:123" in subs

class TestQuoteHandler:
    """Test cases for QuoteHandler"""
    
    @pytest.fixture
    def handler(self):
        return QuoteHandler()
    
    @pytest.mark.asyncio
    async def test_handle_quote(self, handler):
        """Test handling quote data"""
        data = {
            "contractId": 123,
            "symbol": "ES",
            "bid": 4500.0,
            "ask": 4500.25,
            "last": 4500.1,
            "bidSize": 100,
            "askSize": 100,
            "lastSize": 1,
            "volume": 1000,
            "high": 4501.0,
            "low": 4499.0,
            "open": 4499.5,
            "settlement": 4500.0
        }
        
        quote = await handler.handle_quote(data)
        
        assert quote is not None
        assert quote.symbol == "ES"
        assert quote.last == 4500.1
        assert 123 in handler.quotes
    
    @pytest.mark.asyncio
    async def test_price_change_callback(self, handler):
        """Test price change callback"""
        called = False
        event_data = None
        
        async def callback(event):
            nonlocal called, event_data
            called = True
            event_data = event
        
        handler.on_any_price_change(callback)
        
        # First quote
        data1 = {
            "contractId": 123,
            "symbol": "ES",
            "bid": 4500.0,
            "ask": 4500.25,
            "last": 4500.0,
            "bidSize": 100,
            "askSize": 100,
            "lastSize": 1,
            "volume": 1000,
            "high": 4501.0,
            "low": 4499.0,
            "open": 4499.5,
            "settlement": 4500.0
        }
        await handler.handle_quote(data1)
        
        # Second quote with price change
        data2 = data1.copy()
        data2["last"] = 4505.0
        await handler.handle_quote(data2)
        
        assert called is True
        assert event_data["new_price"] == 4505.0
        assert event_data["change"] == 5.0
    
    def test_get_quote(self, handler):
        """Test getting stored quote"""
        from datetime import datetime
        quote = Quote(
            contract_id=123,
            symbol="ES",
            bid=4500.0,
            ask=4500.25,
            last=4500.1,
            bid_size=100,
            ask_size=100,
            last_size=1,
            volume=1000,
            high=4501.0,
            low=4499.0,
            open_price=4499.5,
            settlement=4500.0,
            timestamp=datetime.utcnow()
        )
        handler.quotes[123] = quote
        
        retrieved = handler.get_quote(123)
        assert retrieved == quote

class TestOrderAndFillHandler:
    """Test cases for OrderAndFillHandler"""
    
    @pytest.fixture
    def handler(self):
        return OrderAndFillHandler()
    
    @pytest.mark.asyncio
    async def test_handle_order_update(self, handler):
        """Test handling order update"""
        data = {
            "orderId": 123,
            "accountId": 456,
            "symbol": "ES",
            "quantity": 2,
            "price": 4500.0,
            "status": "Working"
        }
        
        notification = await handler.handle_order_update(data)
        
        assert notification is not None
        assert notification.order_id == 123
        assert notification.status == "Working"
        assert 123 in handler.order_history
    
    @pytest.mark.asyncio
    async def test_handle_fill(self, handler):
        """Test handling fill"""
        data = {
            "orderId": 123,
            "accountId": 456,
            "symbol": "ES",
            "quantity": 2,
            "fillPrice": 4500.0,
            "fillQuantity": 2,
            "commission": 12.5
        }
        
        notification = await handler.handle_fill(data)
        
        assert notification is not None
        assert notification.fill_price == 4500.0
        assert notification.fill_quantity == 2
        assert len(handler.fill_history) == 1
    
    def test_get_order_status(self, handler):
        """Test getting order status"""
        from datetime import datetime
        notification = OrderNotification(
            order_id=123,
            account_id=456,
            symbol="ES",
            quantity=2,
            price=4500.0,
            status="Filled",
            timestamp=datetime.utcnow()
        )
        handler.order_history[123] = notification
        
        status = handler.get_order_status(123)
        assert status == "Filled"
