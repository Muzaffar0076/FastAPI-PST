from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, ForeignKey, Numeric
from sqlalchemy.orm import relationship
from app.db.database import Base

class Promotion(Base):
    __tablename__ = "promotions"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    discount_type = Column(String, nullable=False)
    discount_value = Column(Float, nullable=True)
    buy_quantity = Column(Integer, nullable=True)
    get_quantity = Column(Integer, nullable=True)
    min_quantity = Column(Integer, nullable=True)
    min_amount = Column(Float, nullable=True)
    category_filter = Column(String, nullable=True)
    applies_to_category = Column(Boolean, default=False, nullable=False)
    priority = Column(Integer, default=0, nullable=False)
    stacking_enabled = Column(Boolean, default=False, nullable=False)
    start_date = Column(DateTime, nullable=False)
    end_date = Column(DateTime, nullable=False)
    is_active = Column(Boolean, default=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=True)

    product = relationship("Product")
