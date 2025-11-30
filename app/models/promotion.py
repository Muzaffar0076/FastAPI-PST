from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, ForeignKey, Numeric
from sqlalchemy.orm import relationship
from app.db.database import Base

class Promotion(Base):
    __tablename__ = "promotions"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    discount_type = Column(String, nullable=False)  # percentage | flat | bogo
    discount_value = Column(Float, nullable=False)  # % or fixed amount
    buy_quantity = Column(Integer, nullable=True)   # for BOGO
    get_quantity = Column(Integer, nullable=True)   # for BOGO
    min_quantity = Column(Integer, nullable=True)
    priority = Column(Integer, default=0, nullable=False)  # Lower number = higher priority (0 is highest)
    stacking_enabled = Column(Boolean, default=False, nullable=False)  # Can stack with other promotions
    start_date = Column(DateTime, nullable=False)
    end_date = Column(DateTime, nullable=False)
    is_active = Column(Boolean, default=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)

    product = relationship("Product")
