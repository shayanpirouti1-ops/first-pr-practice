"""Copy trading signal handler"""
import logging
from typing import Optional, Dict, Any
from datetime import datetime
from app.copytrader.engine import CopyTradingEngine, OrderType, PositionType
from app.traders.tradovate import TradovateClient, TradovateAPIError
from app.risk.manager import RiskManager

logger = logging.getLogger(__name__)

class TraderSignal:
    """Signal from a trader to copy"""
    
    def __init__(self, trader_id: str, symbol: str, quantity: int,
                 order_type: str, price: Optional[float] = None,
                 stop_price: Optional[float] = None,
                 trader_order_id: Optional[str] = None):
        self.trader_id = trader_id
        self.symbol = symbol
        self.quantity = quantity
        self.order_type = order_type
        self.price = price
        self.stop_price = stop_price
        self.trader_order_id = trader_order_id or f"{trader_id}_{symbol}_{datetime.utcnow().timestamp()}"
        self.timestamp = datetime.utcnow()

class CopyTradingSignalHandler:
    """Handle signals from traders and execute copy trades"""
    
    def __init__(self, engine: CopyTradingEngine, client: TradovateClient,
                 risk_manager: RiskManager, account_id: int):
        self.engine = engine
        self.client = client
        self.risk_manager = risk_manager
        self.account_id = account_id
        self.signal_history = []
    
    async def handle_signal(self, signal: TraderSignal) -> Dict[str, Any]:
        """
        Handle a trading signal from a trader
        
        Args:
            signal: Trading signal to copy
        
        Returns:
            Result dictionary with status
        """
        result = {
            "success": False,
            "trader_id": signal.trader_id,
            "symbol": signal.symbol,
            "error": None,
            "copy_order_id": None
        }
        
        try:
            # Get trader configuration
            config = self.engine.configs.get(signal.trader_id)
            if not config:
                result["error"] = f"Trader {signal.trader_id} not found"
                logger.warning(result["error"])
                return result
            
            # Calculate copy quantity
            copy_quantity = self.engine.calculate_copy_quantity(
                signal.quantity,
                config.copy_ratio
            )
            
            # Validate order
            is_valid, error_msg = self.engine.validate_copy_order(
                signal.trader_id,
                signal.symbol,
                copy_quantity,
                config.max_position_size
            )
            
            if not is_valid:
                result["error"] = error_msg
                logger.warning(f"Order validation failed: {error_msg}")
                return result
            
            # Risk check
            if not await self._risk_check(signal.symbol, copy_quantity, signal.order_type):
                result["error"] = "Risk check failed"
                logger.warning("Risk check failed for order")
                return result
            
            # Place order on exchange
            try:
                exchange_order = await self.client.place_order(
                    account_id=self.account_id,
                    symbol=signal.symbol,
                    quantity=copy_quantity,
                    order_type=signal.order_type,
                    price=signal.price,
                    stop_price=signal.stop_price
                )
            except TradovateAPIError as e:
                result["error"] = f"Order placement failed: {str(e)}"
                logger.error(result["error"])
                return result
            
            # Record the copy
            copy_order_id = exchange_order.get('orderId')
            self.engine.record_copy_order(
                trader_order_id=signal.trader_order_id,
                copy_order_id=copy_order_id,
                trader_id=signal.trader_id,
                account_id=self.account_id,
                symbol=signal.symbol,
                original_quantity=signal.quantity,
                copy_quantity=copy_quantity,
                order_type=OrderType(signal.order_type),
                price=signal.price,
                stop_price=signal.stop_price
            )
            
            # Update stats
            stats = self.engine.stats.get(signal.trader_id)
            if stats:
                stats.total_copies += 1
            
            result["success"] = True
            result["copy_order_id"] = copy_order_id
            result["copy_quantity"] = copy_quantity
            result["ratio"] = config.copy_ratio
            
            logger.info(f"Successfully copied order from {signal.trader_id}: {signal.symbol} x{copy_quantity}")
            self.signal_history.append(result)
            
            return result
        
        except Exception as e:
            result["error"] = f"Unexpected error: {str(e)}"
            logger.error(result["error"], exc_info=True)
            return result
    
    async def _risk_check(self, symbol: str, quantity: int, order_type: str) -> bool:
        """
        Perform risk checks before placing order
        
        Args:
            symbol: Trading symbol
            quantity: Order quantity
            order_type: Order type
        
        Returns:
            True if risk check passes
        """
        try:
            # Get account balance
            balance = await self.client.get_balance(self.account_id)
            current_equity = balance.get('equity', 0)
            
            # Calculate exposure
            # Simplified: assume each contract = $1000 notional value
            position_notional = quantity * 1000
            exposure_percent = (position_notional / current_equity * 100) if current_equity > 0 else 100
            
            # Check against risk limits
            if exposure_percent > self.risk_manager.config.max_account_exposure:
                logger.warning(f"Exposure {exposure_percent}% exceeds limit {self.risk_manager.config.max_account_exposure}%")
                return False
            
            if quantity > self.risk_manager.config.max_position_size:
                logger.warning(f"Quantity {quantity} exceeds max position {self.risk_manager.config.max_position_size}")
                return False
            
            return True
        
        except Exception as e:
            logger.error(f"Risk check error: {str(e)}")
            return False
    
    async def handle_order_fill(self, copy_order_id: int, fill_price: float,
                               fill_quantity: int, fill_time: Optional[datetime] = None) -> bool:
        """
        Handle order fill notification
        
        Args:
            copy_order_id: Our copy order ID
            fill_price: Fill price
            fill_quantity: Filled quantity
            fill_time: Time of fill
        
        Returns:
            True if handled
        """
        try:
            # Update order status
            self.engine.update_order_status(copy_order_id, "Filled", fill_time)
            logger.info(f"Order {copy_order_id} filled at {fill_price}")
            return True
        except Exception as e:
            logger.error(f"Error handling fill: {str(e)}")
            return False
    
    async def handle_order_cancellation(self, copy_order_id: int) -> bool:
        """
        Handle order cancellation
        
        Args:
            copy_order_id: Our copy order ID
        
        Returns:
            True if handled
        """
        try:
            self.engine.update_order_status(copy_order_id, "Cancelled")
            logger.info(f"Order {copy_order_id} cancelled")
            return True
        except Exception as e:
            logger.error(f"Error handling cancellation: {str(e)}")
            return False
    
    def get_signal_history(self, trader_id: Optional[str] = None, limit: int = 50) -> list:
        """
        Get signal history
        
        Args:
            trader_id: Filter by trader ID
            limit: Maximum results
        
        Returns:
            List of signals
        """
        history = self.signal_history
        if trader_id:
            history = [s for s in history if s.get('trader_id') == trader_id]
        return history[-limit:]
