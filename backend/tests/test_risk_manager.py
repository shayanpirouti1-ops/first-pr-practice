"""Tests for risk manager"""
import pytest
from app.risk.manager import RiskManager, RiskConfig

class TestRiskManager:
    """Test cases for RiskManager"""
    
    @pytest.fixture
    def manager(self):
        config = RiskConfig(
            max_position_size=10000,
            max_account_exposure=80,
            max_daily_loss=5,
            stop_loss_percent=2,
            take_profit_percent=5
        )
        return RiskManager(config)
    
    def test_calculate_position_size(self, manager):
        """Test position size calculation"""
        position_size = manager.calculate_position_size(100000, 2)
        
        # 2% of 100000 = 2000
        assert position_size == 2000
    
    def test_calculate_position_size_capped(self, manager):
        """Test position size capped at max"""
        position_size = manager.calculate_position_size(1000000, 10)
        
        # Would be 100000, but capped at 10000
        assert position_size == 10000
    
    def test_validate_position_success(self, manager):
        """Test position validation - success"""
        is_valid = manager.validate_position(50, 20)
        
        # 50 + 20 = 70, which is < 80
        assert is_valid is True
    
    def test_validate_position_exceeds_limit(self, manager):
        """Test position validation - exceeds limit"""
        is_valid = manager.validate_position(60, 30)
        
        # 60 + 30 = 90, which is > 80
        assert is_valid is False
    
    def test_calculate_stop_loss_long(self, manager):
        """Test stop loss calculation for long position"""
        stop_loss = manager.calculate_stop_loss(1000, "long")
        
        # 2% stop loss = 1000 - 20 = 980
        assert stop_loss == 980
    
    def test_calculate_stop_loss_short(self, manager):
        """Test stop loss calculation for short position"""
        stop_loss = manager.calculate_stop_loss(1000, "short")
        
        # 2% stop loss = 1000 + 20 = 1020
        assert stop_loss == 1020
    
    def test_calculate_take_profit_long(self, manager):
        """Test take profit calculation for long position"""
        take_profit = manager.calculate_take_profit(1000, "long")
        
        # 5% take profit = 1000 + 50 = 1050
        assert take_profit == 1050
    
    def test_calculate_take_profit_short(self, manager):
        """Test take profit calculation for short position"""
        take_profit = manager.calculate_take_profit(1000, "short")
        
        # 5% take profit = 1000 - 50 = 950
        assert take_profit == 950
    
    def test_check_daily_loss_limit_within(self, manager):
        """Test daily loss limit - within limit"""
        is_within = manager.check_daily_loss_limit(4000, 100000)
        
        # 4000/100000 = 4%, which is < 5%
        assert is_within is True
    
    def test_check_daily_loss_limit_exceeded(self, manager):
        """Test daily loss limit - exceeded"""
        is_within = manager.check_daily_loss_limit(6000, 100000)
        
        # 6000/100000 = 6%, which is > 5%
        assert is_within is False
    
    def test_reset_daily_stats(self, manager):
        """Test resetting daily stats"""
        manager.daily_loss = 5000
        manager.reset_daily_stats()
        
        assert manager.daily_loss == 0.0
