"""Tests for database models and repositories"""
import pytest
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.database.models import (
    Base, User, Account, CopyTrader, Order, Fill, Position, OrderStatusEnum
)
from app.database.repositories import (
    UserRepository, AccountRepository, CopyTraderRepository, OrderRepository,
    FillRepository, PositionRepository
)

@pytest.fixture
def test_db():
    """Create test database"""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = TestingSessionLocal()
    yield db
    db.close()

class TestUserRepository:
    """Test user repository"""
    
    def test_create_user(self, test_db):
        """Test creating user"""
        user = UserRepository.create_user(
            test_db,
            username="testuser",
            email="test@example.com",
            api_key="key123",
            api_secret="secret123"
        )
        
        assert user.id is not None
        assert user.username == "testuser"
        assert user.email == "test@example.com"
    
    def test_get_user_by_username(self, test_db):
        """Test getting user by username"""
        UserRepository.create_user(
            test_db,
            username="testuser",
            email="test@example.com",
            api_key="key123",
            api_secret="secret123"
        )
        
        user = UserRepository.get_user_by_username(test_db, "testuser")
        assert user is not None
        assert user.username == "testuser"

class TestAccountRepository:
    """Test account repository"""
    
    def test_create_account(self, test_db):
        """Test creating account"""
        user = UserRepository.create_user(
            test_db,
            username="testuser",
            email="test@example.com",
            api_key="key123",
            api_secret="secret123"
        )
        
        account = AccountRepository.create_account(
            test_db,
            user_id=user.id,
            account_id=123456,
            account_name="Main Account"
        )
        
        assert account.id is not None
        assert account.account_id == 123456
        assert account.account_name == "Main Account"
    
    def test_update_account_balance(self, test_db):
        """Test updating account balance"""
        user = UserRepository.create_user(
            test_db,
            username="testuser",
            email="test@example.com",
            api_key="key123",
            api_secret="secret123"
        )
        
        account = AccountRepository.create_account(
            test_db,
            user_id=user.id,
            account_id=123456
        )
        
        updated = AccountRepository.update_account_balance(
            test_db,
            account_id=account.id,
            balance=100000.0,
            equity=100000.0,
            cash=50000.0
        )
        
        assert updated.balance == 100000.0
        assert updated.equity == 100000.0
        assert updated.cash == 50000.0

class TestCopyTraderRepository:
    """Test copy trader repository"""
    
    def test_create_copy_trader(self, test_db):
        """Test creating copy trader"""
        user = UserRepository.create_user(
            test_db,
            username="testuser",
            email="test@example.com",
            api_key="key123",
            api_secret="secret123"
        )
        
        trader = CopyTraderRepository.create_copy_trader(
            test_db,
            user_id=user.id,
            trader_id="trader1",
            copy_ratio=0.5
        )
        
        assert trader.id is not None
        assert trader.trader_id == "trader1"
        assert trader.copy_ratio == 0.5

class TestOrderRepository:
    """Test order repository"""
    
    def test_create_order(self, test_db):
        """Test creating order"""
        user = UserRepository.create_user(
            test_db,
            username="testuser",
            email="test@example.com",
            api_key="key123",
            api_secret="secret123"
        )
        
        account = AccountRepository.create_account(
            test_db,
            user_id=user.id,
            account_id=123456
        )
        
        order = OrderRepository.create_order(
            test_db,
            user_id=user.id,
            account_id=account.id,
            order_id=1001,
            symbol="ES",
            quantity=2,
            price=4500.0,
            order_type="Market"
        )
        
        assert order.id is not None
        assert order.symbol == "ES"
        assert order.quantity == 2
    
    def test_update_order_status(self, test_db):
        """Test updating order status"""
        user = UserRepository.create_user(
            test_db,
            username="testuser",
            email="test@example.com",
            api_key="key123",
            api_secret="secret123"
        )
        
        account = AccountRepository.create_account(
            test_db,
            user_id=user.id,
            account_id=123456
        )
        
        order = OrderRepository.create_order(
            test_db,
            user_id=user.id,
            account_id=account.id,
            order_id=1001,
            symbol="ES",
            quantity=2
        )
        
        updated = OrderRepository.update_order_status(
            test_db,
            order_id=order.order_id,
            status="Filled"
        )
        
        assert updated.status == OrderStatusEnum.FILLED

class TestPositionRepository:
    """Test position repository"""
    
    def test_create_position(self, test_db):
        """Test creating position"""
        user = UserRepository.create_user(
            test_db,
            username="testuser",
            email="test@example.com",
            api_key="key123",
            api_secret="secret123"
        )
        
        account = AccountRepository.create_account(
            test_db,
            user_id=user.id,
            account_id=123456
        )
        
        position = PositionRepository.create_position(
            test_db,
            account_id=account.id,
            symbol="ES",
            quantity=2,
            entry_price=4500.0
        )
        
        assert position.id is not None
        assert position.symbol == "ES"
        assert position.quantity == 2
        assert position.entry_price == 4500.0
