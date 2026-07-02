"""Tests for copy trading engine"""
import pytest
from datetime import datetime
from app.copytrader.engine import (
    CopyTradingEngine,
    CopyConfig,
    OrderType,
    PositionType,
    TraderStats
)

class TestCopyTradingEngine:
    """Test cases for CopyTradingEngine"""
    
    @pytest.fixture
    def engine(self):
        return CopyTradingEngine()
    
    def test_add_trader(self, engine):
        """Test adding a trader to copy"""
        config = CopyConfig(
            trader_id="trader1",
            copy_ratio=0.5,
            max_position_size=5000
        )
        result = engine.add_trader_to_copy(config)
        
        assert result is True
        assert "trader1" in engine.configs
        assert engine.configs["trader1"].copy_ratio == 0.5
    
    def test_add_duplicate_trader(self, engine):
        """Test adding duplicate trader"""
        config = CopyConfig(trader_id="trader1")
        engine.add_trader_to_copy(config)
        
        result = engine.add_trader_to_copy(config)
        assert result is False
    
    def test_invalid_copy_ratio(self, engine):
        """Test invalid copy ratio"""
        config = CopyConfig(
            trader_id="trader1",
            copy_ratio=1.5  # Invalid, should be 0.0-1.0
        )
        result = engine.add_trader_to_copy(config)
        
        assert result is False
    
    def test_remove_trader(self, engine):
        """Test removing trader"""
        config = CopyConfig(trader_id="trader1")
        engine.add_trader_to_copy(config)
        
        result = engine.remove_trader("trader1")
        assert result is True
        assert "trader1" not in engine.configs
    
    def test_calculate_copy_quantity(self, engine):
        """Test quantity calculation"""
        # Test 50% copy ratio
        quantity = engine.calculate_copy_quantity(10, 0.5)
        assert quantity == 5
        
        # Test 100% copy ratio
        quantity = engine.calculate_copy_quantity(10, 1.0)
        assert quantity == 10
        
        # Test minimum 1 contract
        quantity = engine.calculate_copy_quantity(1, 0.1)
        assert quantity >= 1
    
    def test_validate_copy_order_success(self, engine):
        """Test order validation - success case"""
        config = CopyConfig(
            trader_id="trader1",
            max_position_size=10000
        )
        engine.add_trader_to_copy(config)
        
        is_valid, error = engine.validate_copy_order(
            "trader1", "ES", 5, 10000
        )
        assert is_valid is True
        assert error == ""
    
    def test_validate_copy_order_trader_not_found(self, engine):
        """Test validation - trader not found"""
        is_valid, error = engine.validate_copy_order(
            "unknown_trader", "ES", 5, 10000
        )
        assert is_valid is False
        assert "not found" in error
    
    def test_validate_copy_order_exceeds_max_size(self, engine):
        """Test validation - exceeds max position size"""
        config = CopyConfig(
            trader_id="trader1",
            max_position_size=5000
        )
        engine.add_trader_to_copy(config)
        
        is_valid, error = engine.validate_copy_order(
            "trader1", "ES", 10000, 5000  # 10000 > 5000
        )
        assert is_valid is False
        assert "exceeds" in error
    
    def test_record_copy_order(self, engine):
        """Test recording a copy order"""
        config = CopyConfig(trader_id="trader1")
        engine.add_trader_to_copy(config)
        
        order = engine.record_copy_order(
            trader_order_id="ord_001",
            copy_order_id=123,
            trader_id="trader1",
            account_id=456,
            symbol="ES",
            original_quantity=10,
            copy_quantity=5,
            order_type=OrderType.MARKET,
            price=None,
            stop_price=None
        )
        
        assert order.copy_order_id == 123
        assert order.symbol == "ES"
        assert order.quantity == 5
        assert 123 in engine.order_map
    
    def test_update_order_status(self, engine):
        """Test updating order status"""
        config = CopyConfig(trader_id="trader1")
        engine.add_trader_to_copy(config)
        
        engine.record_copy_order(
            trader_order_id="ord_001",
            copy_order_id=123,
            trader_id="trader1",
            account_id=456,
            symbol="ES",
            original_quantity=10,
            copy_quantity=5,
            order_type=OrderType.MARKET
        )
        
        result = engine.update_order_status(123, "Filled")
        assert result is True
        assert engine.order_map[123].status == "Filled"
    
    def test_record_pnl(self, engine):
        """Test recording P&L"""
        config = CopyConfig(trader_id="trader1")
        engine.add_trader_to_copy(config)
        
        engine.record_copy_order(
            trader_order_id="ord_001",
            copy_order_id=123,
            trader_id="trader1",
            account_id=456,
            symbol="ES",
            original_quantity=10,
            copy_quantity=5,
            order_type=OrderType.MARKET
        )
        
        # Record profit
        result = engine.record_pnl(123, 250.0)
        assert result is True
        
        stats = engine.get_trader_stats("trader1")
        assert stats.total_pnl == 250.0
        assert stats.successful_copies == 1
    
    def test_get_active_copies(self, engine):
        """Test getting active copies"""
        config = CopyConfig(trader_id="trader1")
        engine.add_trader_to_copy(config)
        
        # Add working order
        engine.record_copy_order(
            trader_order_id="ord_001",
            copy_order_id=123,
            trader_id="trader1",
            account_id=456,
            symbol="ES",
            original_quantity=10,
            copy_quantity=5,
            order_type=OrderType.MARKET
        )
        
        # Add filled order
        engine.record_copy_order(
            trader_order_id="ord_002",
            copy_order_id=124,
            trader_id="trader1",
            account_id=456,
            symbol="NQ",
            original_quantity=10,
            copy_quantity=5,
            order_type=OrderType.MARKET,
            status="Filled"
        )
        
        active = engine.get_active_copies("trader1")
        assert len(active) == 1
        assert active[0].symbol == "ES"
