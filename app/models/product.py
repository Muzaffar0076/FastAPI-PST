from sqlalchemy import Column, Integer, String, Numeric, Boolean
from app.db.database import Base

class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)
    sku = Column(String, unique=True, nullable=False)
    title = Column(String, nullable=False)
    base_price = Column(Numeric(10, 2), nullable=False)
    currency = Column(String, default="INR", nullable=False)  # ISO currency code
    tax_rate = Column(Numeric(5, 2), default=0.0, nullable=False)  # Tax rate as percentage
    tax_inclusive = Column(Boolean, default=False, nullable=False)  # True if price includes tax
    max_discount_cap = Column(Numeric(10, 2), nullable=True)  # Maximum discount amount allowed (None = no cap)
    category = Column(String, nullable=True)
    stock = Column(Integer, default=0)
