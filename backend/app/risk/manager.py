"""Risk management module"""
from dataclasses import dataclass
from typing import Optional

@dataclass
class RiskConfig:
    """Risk management configuration"""
    max_position_size: float  # Max size per trade
    max_account_exposure: float  # Max % of account exposed
    max_daily_loss: float  # Max daily loss in %
    stop_loss_percent: float  # Default stop loss %
    take_profit_percent: float  # Default take profit %

class RiskManager:
    """Manages risk for trading operations"""
    
    def __init__(self, config: RiskConfig):
        self.config = config
    
    def calculate_position_size(self, account_balance: float, risk_per_trade: float) -> float:
        """
        Calculate position size based on account balance and risk per trade
        
        Args:
            account_balance: Current account balance
            risk_per_trade: Risk per trade in %
        
        Returns:
            Position size
        """
        position_size = (account_balance * risk_per_trade) / 100
        return min(position_size, self.config.max_position_size)
    
    def validate_position(self, current_exposure: float, new_position_size: float) -> bool:
        """
        Validate if a new position respects risk limits
        
        Args:
            current_exposure: Current account exposure in %
            new_position_size: Size of new position
        
        Returns:
            True if position is within limits
        """
        total_exposure = current_exposure + new_position_size
        return total_exposure <= self.config.max_account_exposure
    
    def calculate_stop_loss(self, entry_price: float, position_type: str) -> float:
        """
        Calculate stop loss price
        
        Args:
            entry_price: Entry price of the position
            position_type: 'long' or 'short'
        
        Returns:
            Stop loss price
        """
        if position_type == 'long':
            return entry_price * (1 - self.config.stop_loss_percent / 100)
        else:  # short
            return entry_price * (1 + self.config.stop_loss_percent / 100)
    
    def calculate_take_profit(self, entry_price: float, position_type: str) -> float:
        """
        Calculate take profit price
        
        Args:
            entry_price: Entry price of the position
            position_type: 'long' or 'short'
        
        Returns:
            Take profit price
        """
        if position_type == 'long':
            return entry_price * (1 + self.config.take_profit_percent / 100)
        else:  # short
            return entry_price * (1 - self.config.take_profit_percent / 100)
