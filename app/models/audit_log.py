from sqlalchemy import Column, Integer, String, Float, DateTime, JSON, ForeignKey
from sqlalchemy.orm import relationship
from app.db.database import Base
from datetime import datetime

class PriceAuditLog(Base):
    __tablename__ = 'price_audit_logs'
    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey('products.id'), nullable=False)
    quantity = Column(Integer, nullable=False)
    original_price = Column(Float, nullable=False)
    final_price = Column(Float, nullable=False)
    discount_amount = Column(Float, nullable=False)
    applied_promotions = Column(JSON, default=[])
    currency = Column(String, nullable=False)
    tax_amount = Column(Float, nullable=False)
    tax_rate = Column(Float, nullable=False)
    user_id = Column(String, nullable=True)
    ip_address = Column(String, nullable=True)
    user_agent = Column(String, nullable=True)
    request_id = Column(String, nullable=True)
    extra_data = Column(JSON, default={})
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    product = relationship('Product')