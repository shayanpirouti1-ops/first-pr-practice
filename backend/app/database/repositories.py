"""Database repositories for data access"""
from typing import List, Optional
from sqlalchemy.orm import Session
from app.database.models import (
    User, Account, CopyTrader, Order, Fill, Position, CopyOrder, AccountStats, OrderStatusEnum
)
from datetime import datetime, timedelta

class UserRepository:
    """User data access"""
    
    @staticmethod
    def create_user(db: Session, username: str, email: str, api_key: str, 
                   api_secret: str, sandbox_mode: bool = True) -> User:
        """Create new user"""
        user = User(
            username=username,
            email=email,
            api_key=api_key,
            api_secret=api_secret,
            sandbox_mode=sandbox_mode
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        return user
    
    @staticmethod
    def get_user_by_username(db: Session, username: str) -> Optional[User]:
        """Get user by username"""
        return db.query(User).filter(User.username == username).first()
    
    @staticmethod
    def get_user_by_id(db: Session, user_id: int) -> Optional[User]:
        """Get user by ID"""
        return db.query(User).filter(User.id == user_id).first()

class AccountRepository:
    """Account data access"""
    
    @staticmethod
    def create_account(db: Session, user_id: int, account_id: int, 
                      account_name: str = None) -> Account:
        """Create new account"""
        account = Account(
            user_id=user_id,
            account_id=account_id,
            account_name=account_name
        )
        db.add(account)
        db.commit()
        db.refresh(account)
        return account
    
    @staticmethod
    def get_account_by_id(db: Session, account_id: int) -> Optional[Account]:
        """Get account by ID"""
        return db.query(Account).filter(Account.id == account_id).first()
    
    @staticmethod
    def get_accounts_by_user(db: Session, user_id: int) -> List[Account]:
        """Get all accounts for user"""
        return db.query(Account).filter(Account.user_id == user_id).all()
    
    @staticmethod
    def update_account_balance(db: Session, account_id: int, balance: float, 
                              equity: float, cash: float) -> Optional[Account]:
        """Update account balance"""
        account = db.query(Account).filter(Account.id == account_id).first()
        if account:
            account.balance = balance
            account.equity = equity
            account.cash = cash
            account.updated_at = datetime.utcnow()
            db.commit()
            db.refresh(account)
        return account

class CopyTraderRepository:
    """Copy trader data access"""
    
    @staticmethod
    def create_copy_trader(db: Session, user_id: int, trader_id: str,
                          copy_ratio: float = 1.0, max_position_size: float = 10000.0) -> CopyTrader:
        """Create new copy trader"""
        trader = CopyTrader(
            user_id=user_id,
            trader_id=trader_id,
            copy_ratio=copy_ratio,
            max_position_size=max_position_size
        )
        db.add(trader)
        db.commit()
        db.refresh(trader)
        return trader
    
    @staticmethod
    def get_copy_trader(db: Session, trader_id: int) -> Optional[CopyTrader]:
        """Get copy trader by ID"""
        return db.query(CopyTrader).filter(CopyTrader.id == trader_id).first()
    
    @staticmethod
    def get_copy_traders_by_user(db: Session, user_id: int) -> List[CopyTrader]:
        """Get all copy traders for user"""
        return db.query(CopyTrader).filter(CopyTrader.user_id == user_id).all()
    
    @staticmethod
    def update_trader_stats(db: Session, trader_id: int, total_copies: int = None,
                           successful_copies: int = None, total_pnl: float = None) -> Optional[CopyTrader]:
        """Update trader statistics"""
        trader = db.query(CopyTrader).filter(CopyTrader.id == trader_id).first()
        if trader:
            if total_copies is not None:
                trader.total_copies = total_copies
            if successful_copies is not None:
                trader.successful_copies = successful_copies
                if trader.total_copies > 0:
                    trader.win_rate = (successful_copies / trader.total_copies) * 100
            if total_pnl is not None:
                trader.total_pnl = total_pnl
            trader.updated_at = datetime.utcnow()
            db.commit()
            db.refresh(trader)
        return trader

class OrderRepository:
    """Order data access"""
    
    @staticmethod
    def create_order(db: Session, user_id: int, account_id: int, order_id: int,
                    symbol: str, quantity: int, price: float = None,
                    order_type: str = "Market") -> Order:
        """Create new order"""
        order = Order(
            user_id=user_id,
            account_id=account_id,
            order_id=order_id,
            symbol=symbol,
            quantity=quantity,
            price=price,
            order_type=order_type
        )
        db.add(order)
        db.commit()
        db.refresh(order)
        return order
    
    @staticmethod
    def get_order(db: Session, order_id: int) -> Optional[Order]:
        """Get order by ID"""
        return db.query(Order).filter(Order.order_id == order_id).first()
    
    @staticmethod
    def get_orders_by_account(db: Session, account_id: int, 
                             status: str = None, limit: int = 100) -> List[Order]:
        """Get orders for account"""
        query = db.query(Order).filter(Order.account_id == account_id)
        if status:
            query = query.filter(Order.status == status)
        return query.order_by(Order.created_at.desc()).limit(limit).all()
    
    @staticmethod
    def update_order_status(db: Session, order_id: int, status: str,
                           filled_at: datetime = None) -> Optional[Order]:
        """Update order status"""
        order = db.query(Order).filter(Order.order_id == order_id).first()
        if order:
            order.status = status
            if filled_at:
                order.filled_at = filled_at
            order.updated_at = datetime.utcnow()
            db.commit()
            db.refresh(order)
        return order

class FillRepository:
    """Fill data access"""
    
    @staticmethod
    def create_fill(db: Session, account_id: int, order_id: int, symbol: str,
                   quantity: int, fill_price: float, commission: float = 0.0) -> Fill:
        """Create new fill"""
        fill = Fill(
            account_id=account_id,
            order_id=order_id,
            symbol=symbol,
            quantity=quantity,
            fill_price=fill_price,
            commission=commission
        )
        db.add(fill)
        db.commit()
        db.refresh(fill)
        return fill
    
    @staticmethod
    def get_fills_by_account(db: Session, account_id: int, 
                            days: int = 1, limit: int = 100) -> List[Fill]:
        """Get fills for account in last N days"""
        since = datetime.utcnow() - timedelta(days=days)
        return db.query(Fill).filter(
            Fill.account_id == account_id,
            Fill.created_at >= since
        ).order_by(Fill.created_at.desc()).limit(limit).all()

class PositionRepository:
    """Position data access"""
    
    @staticmethod
    def create_position(db: Session, account_id: int, symbol: str,
                       quantity: int, entry_price: float) -> Position:
        """Create new position"""
        position = Position(
            account_id=account_id,
            symbol=symbol,
            quantity=quantity,
            entry_price=entry_price
        )
        db.add(position)
        db.commit()
        db.refresh(position)
        return position
    
    @staticmethod
    def get_position(db: Session, account_id: int, symbol: str) -> Optional[Position]:
        """Get position for symbol"""
        return db.query(Position).filter(
            Position.account_id == account_id,
            Position.symbol == symbol
        ).first()
    
    @staticmethod
    def get_positions_by_account(db: Session, account_id: int) -> List[Position]:
        """Get all positions for account"""
        return db.query(Position).filter(Position.account_id == account_id).all()
    
    @staticmethod
    def update_position(db: Session, position_id: int, current_price: float,
                       unrealized_pnl: float) -> Optional[Position]:
        """Update position"""
        position = db.query(Position).filter(Position.id == position_id).first()
        if position:
            position.current_price = current_price
            position.unrealized_pnl = unrealized_pnl
            position.updated_at = datetime.utcnow()
            db.commit()
            db.refresh(position)
        return position

class AccountStatsRepository:
    """Account stats data access"""
    
    @staticmethod
    def create_daily_stats(db: Session, account_id: int, date: datetime) -> AccountStats:
        """Create daily stats record"""
        stats = AccountStats(
            account_id=account_id,
            date=date
        )
        db.add(stats)
        db.commit()
        db.refresh(stats)
        return stats
    
    @staticmethod
    def get_stats_by_date(db: Session, account_id: int, date: datetime) -> Optional[AccountStats]:
        """Get stats for specific date"""
        return db.query(AccountStats).filter(
            AccountStats.account_id == account_id,
            AccountStats.date == date.date()
        ).first()
    
    @staticmethod
    def update_daily_stats(db: Session, account_id: int, date: datetime,
                          daily_pnl: float, daily_trades: int, daily_wins: int,
                          daily_losses: int) -> Optional[AccountStats]:
        """Update daily stats"""
        stats = AccountStatsRepository.get_stats_by_date(db, account_id, date)
        if not stats:
            stats = AccountStatsRepository.create_daily_stats(db, account_id, date)
        
        stats.daily_pnl = daily_pnl
        stats.daily_trades = daily_trades
        stats.daily_wins = daily_wins
        stats.daily_losses = daily_losses
        if daily_trades > 0:
            stats.win_rate = (daily_wins / daily_trades) * 100
        db.commit()
        db.refresh(stats)
        return stats
