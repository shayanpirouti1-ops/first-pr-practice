"""Copy trading engine core logic"""
import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

logger = logging.getLogger(__name__)

class OrderType(str, Enum):
    """Order types"""
    MARKET = "Market"
    LIMIT = "Limit"
    STOP = "Stop"
    STOP_LIMIT = "StopLimit"

class PositionType(str, Enum):
    """Position types"""
    LONG = "long"
    SHORT = "short"

@dataclass
class CopyConfig:
    """Configuration for copying a trader"""
    trader_id: str
    copy_ratio: float = 1.0  # 0.0 to 1.0
    max_position_size: float = 10000.0
    enabled: bool = True
    created_at: datetime = field(default_factory=datetime.utcnow)

@dataclass
class CopyOrder:
    """Record of a copied order"""
    trader_order_id: str
    copy_order_id: int
    trader_id: str
    account_id: int
    symbol: str
    quantity: int
    original_quantity: int
    order_type: OrderType
    price: Optional[float]
    stop_price: Optional[float]
    status: str = "Pending"
    created_at: datetime = field(default_factory=datetime.utcnow)
    filled_at: Optional[datetime] = None
    pnl: Optional[float] = None

@dataclass
class TraderStats:
    """Statistics for a trader being copied"""
    trader_id: str
    total_copies: int = 0
    successful_copies: int = 0
    failed_copies: int = 0
    total_pnl: float = 0.0
    win_rate: float = 0.0
    last_copy_at: Optional[datetime] = None
    copy_ratio: float = 1.0

class CopyTradingEngine:
    """Main copy trading engine"""
    
    def __init__(self):
        self.configs: Dict[str, CopyConfig] = {}
        self.active_copies: Dict[str, List[CopyOrder]] = {}  # trader_id -> list of orders
        self.stats: Dict[str, TraderStats] = {}  # trader_id -> stats
        self.order_map: Dict[int, CopyOrder] = {}  # copy_order_id -> CopyOrder
    
    def add_trader_to_copy(self, config: CopyConfig) -> bool:
        """
        Add a trader to copy
        
        Args:
            config: Trader configuration
        
        Returns:
            True if added successfully
        """
        if config.trader_id in self.configs:
            logger.warning(f"Trader {config.trader_id} already being copied")
            return False
        
        if not (0.0 <= config.copy_ratio <= 1.0):
            logger.error(f"Invalid copy ratio: {config.copy_ratio}")
            return False
        
        self.configs[config.trader_id] = config
        self.active_copies[config.trader_id] = []
        self.stats[config.trader_id] = TraderStats(
            trader_id=config.trader_id,
            copy_ratio=config.copy_ratio
        )
        
        logger.info(f"Started copying trader {config.trader_id} with ratio {config.copy_ratio}")
        return True
    
    def remove_trader(self, trader_id: str) -> bool:
        """
        Stop copying a trader
        
        Args:
            trader_id: Trader ID
        
        Returns:
            True if removed successfully
        """
        if trader_id not in self.configs:
            return False
        
        del self.configs[trader_id]
        del self.active_copies[trader_id]
        
        logger.info(f"Stopped copying trader {trader_id}")
        return True
    
    def calculate_copy_quantity(self, original_quantity: int, copy_ratio: float) -> int:
        """
        Calculate quantity for copied order
        
        Args:
            original_quantity: Original order quantity
            copy_ratio: Copy ratio (0.0 to 1.0)
        
        Returns:
            Calculated quantity
        """
        copied_qty = int(original_quantity * copy_ratio)
        return max(1, copied_qty)  # Minimum 1 contract
    
    def validate_copy_order(self, trader_id: str, symbol: str, quantity: int, 
                           max_position_size: float) -> tuple[bool, str]:
        """
        Validate if order can be copied
        
        Args:
            trader_id: Trader ID
            symbol: Trading symbol
            quantity: Quantity to copy
            max_position_size: Max position size
        
        Returns:
            (is_valid, error_message)
        """
        config = self.configs.get(trader_id)
        if not config:
            return False, f"Trader {trader_id} not found"
        
        if not config.enabled:
            return False, f"Copying of {trader_id} is disabled"
        
        # Check position size limit
        if quantity > config.max_position_size:
            return False, f"Quantity {quantity} exceeds max position size {config.max_position_size}"
        
        # Check if same symbol already has open position
        existing_orders = [o for o in self.active_copies.get(trader_id, [])
                          if o.symbol == symbol and o.status == "Working"]
        if existing_orders:
            return False, f"Already have open order for {symbol} from {trader_id}"
        
        return True, ""
    
    def record_copy_order(self, trader_order_id: str, copy_order_id: int,
                         trader_id: str, account_id: int, symbol: str,
                         original_quantity: int, copy_quantity: int,
                         order_type: OrderType, price: Optional[float] = None,
                         stop_price: Optional[float] = None) -> CopyOrder:
        """
        Record a copied order
        
        Args:
            trader_order_id: Original trader's order ID
            copy_order_id: Order ID from exchange
            trader_id: Trader ID
            account_id: Our account ID
            symbol: Trading symbol
            original_quantity: Original quantity
            copy_quantity: Quantity we're copying
            order_type: Order type
            price: Limit price if applicable
            stop_price: Stop price if applicable
        
        Returns:
            CopyOrder record
        """
        copy_order = CopyOrder(
            trader_order_id=trader_order_id,
            copy_order_id=copy_order_id,
            trader_id=trader_id,
            account_id=account_id,
            symbol=symbol,
            quantity=copy_quantity,
            original_quantity=original_quantity,
            order_type=order_type,
            price=price,
            stop_price=stop_price
        )
        
        if trader_id not in self.active_copies:
            self.active_copies[trader_id] = []
        
        self.active_copies[trader_id].append(copy_order)
        self.order_map[copy_order_id] = copy_order
        
        logger.info(f"Recorded copy order {copy_order_id} for trader {trader_id}: {symbol} x{copy_quantity}")
        return copy_order
    
    def update_order_status(self, copy_order_id: int, status: str,
                           filled_at: Optional[datetime] = None) -> bool:
        """
        Update order status
        
        Args:
            copy_order_id: Copy order ID
            status: New status
            filled_at: Timestamp when filled
        
        Returns:
            True if updated
        """
        order = self.order_map.get(copy_order_id)
        if not order:
            return False
        
        order.status = status
        if filled_at:
            order.filled_at = filled_at
        
        logger.info(f"Order {copy_order_id} status updated to {status}")
        return True
    
    def record_pnl(self, copy_order_id: int, pnl: float) -> bool:
        """
        Record P&L for filled order
        
        Args:
            copy_order_id: Copy order ID
            pnl: Profit/Loss amount
        
        Returns:
            True if recorded
        """
        order = self.order_map.get(copy_order_id)
        if not order:
            return False
        
        order.pnl = pnl
        trader_id = order.trader_id
        stats = self.stats.get(trader_id)
        
        if stats:
            stats.total_pnl += pnl
            stats.successful_copies += 1 if pnl > 0 else 0
            stats.win_rate = stats.successful_copies / max(1, stats.total_copies) * 100
            stats.last_copy_at = datetime.utcnow()
        
        logger.info(f"P&L recorded for order {copy_order_id}: {pnl}")
        return True
    
    def get_active_copies(self, trader_id: str) -> List[CopyOrder]:
        """
        Get active copies for a trader
        
        Args:
            trader_id: Trader ID
        
        Returns:
            List of active orders
        """
        return [o for o in self.active_copies.get(trader_id, [])
                if o.status in ["Working", "Pending"]]
    
    def get_trader_stats(self, trader_id: str) -> Optional[TraderStats]:
        """
        Get statistics for a trader
        
        Args:
            trader_id: Trader ID
        
        Returns:
            Trader statistics
        """
        return self.stats.get(trader_id)
    
    def get_all_stats(self) -> Dict[str, TraderStats]:
        """
        Get statistics for all traders
        
        Returns:
            Dictionary of trader stats
        """
        return self.stats.copy()
