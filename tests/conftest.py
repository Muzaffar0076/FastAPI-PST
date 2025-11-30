import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient
from app.db.database import Base, get_db
from app.main import app
from decimal import Decimal

# Create test database
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_promotions.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="function")
def db_session():
    """Create a fresh database for each test"""
    from app.core.cache import CacheService
    # Clear cache before each test
    CacheService.clear_all()

    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)
        # Clear cache after each test
        CacheService.clear_all()


@pytest.fixture(scope="function")
def client(db_session):
    """Create a test client with database dependency override"""
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def sample_product_data():
    """Sample product data for testing"""
    return {
        "sku": "TEST-001",
        "title": "Test Product",
        "base_price": 1000.00,
        "currency": "INR",
        "tax_rate": 18.0,
        "tax_inclusive": False,
        "max_discount_cap": 300.00,
        "category": "electronics",
        "stock": 100
    }


@pytest.fixture
def sample_promotion_data():
    """Sample promotion data for testing"""
    from datetime import datetime, timedelta

    return {
        "name": "Test Promotion",
        "discount_type": "percentage",
        "discount_value": 10.0,
        "priority": 1,
        "stacking_enabled": False,
        "start_date": datetime.utcnow().isoformat(),
        "end_date": (datetime.utcnow() + timedelta(days=7)).isoformat(),
        "is_active": True,
        "product_id": 1
    }
