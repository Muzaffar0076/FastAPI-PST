from sqlalchemy import Column, Integer, String, Numeric
from app.db.database import Base

class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)
    sku = Column(String, unique=True, nullable=False)
    title = Column(String, nullable=False)
    base_price = Column(Numeric(10, 2), nullable=False)
    category = Column(String, nullable=True)
    stock = Column(Integer, default=0)
