import pytest
from app.risk.manager import RiskManager, RiskConfig

@pytest.fixture
def risk_config():
    return RiskConfig(
        max_position_size=10000,
        max_account_exposure=80,
        max_daily_loss=5,
        stop_loss_percent=2,
        take_profit_percent=5
    )

@pytest.fixture
def risk_manager(risk_config):
    return RiskManager(risk_config)

def test_calculate_position_size(risk_manager):
    """Test position size calculation"""
    account_balance = 100000
    risk_per_trade = 2
    
    position_size = risk_manager.calculate_position_size(account_balance, risk_per_trade)
    expected = 2000
    
    assert position_size == expected

def test_calculate_position_size_exceeds_max(risk_manager):
    """Test that position size doesn't exceed max"""
    account_balance = 1000000
    risk_per_trade = 5
    
    position_size = risk_manager.calculate_position_size(account_balance, risk_per_trade)
    
    assert position_size <= risk_manager.config.max_position_size

def test_validate_position_within_limits(risk_manager):
    """Test position validation within limits"""
    current_exposure = 50
    new_position_size = 20
    
    is_valid = risk_manager.validate_position(current_exposure, new_position_size)
    
    assert is_valid is True

def test_validate_position_exceeds_limit(risk_manager):
    """Test position validation exceeding limits"""
    current_exposure = 70
    new_position_size = 20
    
    is_valid = risk_manager.validate_position(current_exposure, new_position_size)
    
    assert is_valid is False

def test_calculate_stop_loss_long(risk_manager):
    """Test stop loss calculation for long position"""
    entry_price = 100
    stop_loss = risk_manager.calculate_stop_loss(entry_price, 'long')
    expected = 100 * (1 - 0.02)
    
    assert stop_loss == expected

def test_calculate_stop_loss_short(risk_manager):
    """Test stop loss calculation for short position"""
    entry_price = 100
    stop_loss = risk_manager.calculate_stop_loss(entry_price, 'short')
    expected = 100 * (1 + 0.02)
    
    assert stop_loss == expected

def test_calculate_take_profit_long(risk_manager):
    """Test take profit calculation for long position"""
    entry_price = 100
    take_profit = risk_manager.calculate_take_profit(entry_price, 'long')
    expected = 100 * (1 + 0.05)
    
    assert take_profit == expected

def test_calculate_take_profit_short(risk_manager):
    """Test take profit calculation for short position"""
    entry_price = 100
    take_profit = risk_manager.calculate_take_profit(entry_price, 'short')
    expected = 100 * (1 - 0.05)
    
    assert take_profit == expected
