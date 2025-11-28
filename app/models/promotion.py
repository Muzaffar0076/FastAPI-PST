from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, ForeignKey
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
    start_date = Column(DateTime, nullable=False)
    end_date = Column(DateTime, nullable=False)
    is_active = Column(Boolean, default=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)

    product = relationship("Product")
