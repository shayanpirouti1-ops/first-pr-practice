"""Risk management module"""
import logging
from typing import Dict, Any
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class RiskConfig:
    """Risk configuration"""
    max_position_size: float = 10000.0  # Max size per position
    max_account_exposure: float = 80.0  # Max % of account exposed
    max_daily_loss: float = 5.0  # Max daily loss in %
    stop_loss_percent: float = 2.0  # Default stop loss %
    take_profit_percent: float = 5.0  # Default take profit %

class RiskManager:
    """Manage risk for trading operations"""
    
    def __init__(self, config: RiskConfig):
        self.config = config
        self.daily_loss = 0.0
        self.current_exposure = 0.0
    
    def calculate_position_size(self, account_balance: float, risk_per_trade: float) -> float:
        """
        Calculate position size based on account and risk
        
        Args:
            account_balance: Total account balance
            risk_per_trade: Risk percentage per trade
        
        Returns:
            Position size
        """
        position_size = (account_balance * risk_per_trade) / 100
        
        # Cap at max position size
        position_size = min(position_size, self.config.max_position_size)
        
        logger.info(f"Calculated position size: {position_size} for balance: {account_balance}")
        return position_size
    
    def validate_position(self, current_exposure: float, new_position_size: float) -> bool:
        """
        Validate if new position respects risk limits
        
        Args:
            current_exposure: Current account exposure in %
            new_position_size: Size of new position in %
        
        Returns:
            True if position is valid
        """
        total_exposure = current_exposure + new_position_size
        
        if total_exposure > self.config.max_account_exposure:
            logger.warning(f"Total exposure {total_exposure}% exceeds limit {self.config.max_account_exposure}%")
            return False
        
        return True
    
    def calculate_stop_loss(self, entry_price: float, position_type: str = "long") -> float:
        """
        Calculate stop loss price
        
        Args:
            entry_price: Entry price
            position_type: 'long' or 'short'
        
        Returns:
            Stop loss price
        """
        stop_loss_amount = entry_price * (self.config.stop_loss_percent / 100)
        
        if position_type.lower() == "long":
            stop_price = entry_price - stop_loss_amount
        else:  # short
            stop_price = entry_price + stop_loss_amount
        
        logger.info(f"Calculated stop loss for {position_type} at {entry_price}: {stop_price}")
        return stop_price
    
    def calculate_take_profit(self, entry_price: float, position_type: str = "long") -> float:
        """
        Calculate take profit price
        
        Args:
            entry_price: Entry price
            position_type: 'long' or 'short'
        
        Returns:
            Take profit price
        """
        profit_amount = entry_price * (self.config.take_profit_percent / 100)
        
        if position_type.lower() == "long":
            tp_price = entry_price + profit_amount
        else:  # short
            tp_price = entry_price - profit_amount
        
        logger.info(f"Calculated take profit for {position_type} at {entry_price}: {tp_price}")
        return tp_price
    
    def check_daily_loss_limit(self, current_loss: float, account_balance: float) -> bool:
        """
        Check if daily loss limit is exceeded
        
        Args:
            current_loss: Current loss amount
            account_balance: Account balance
        
        Returns:
            True if within limit
        """
        loss_percent = (current_loss / account_balance) * 100
        
        if loss_percent > self.config.max_daily_loss:
            logger.warning(f"Daily loss {loss_percent}% exceeds limit {self.config.max_daily_loss}%")
            return False
        
        return True
    
    def reset_daily_stats(self):
        """Reset daily statistics"""
        self.daily_loss = 0.0
        logger.info("Daily statistics reset")
