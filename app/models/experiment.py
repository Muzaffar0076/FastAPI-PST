from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, JSON, ForeignKey
from sqlalchemy.orm import relationship
from app.db.database import Base
from datetime import datetime

class Experiment(Base):
    __tablename__ = 'experiments'
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True, nullable=False)
    description = Column(String)
    experiment_type = Column(String, default='promotion_comparison')
    status = Column(String, default='draft')
    control_config = Column(JSON)
    variant_config = Column(JSON)
    traffic_split = Column(Float, default=50.0)
    start_date = Column(DateTime, nullable=True)
    end_date = Column(DateTime, nullable=True)
    is_active = Column(Boolean, default=False)
    product_id = Column(Integer, ForeignKey('products.id'), nullable=True)
    product = relationship('Product', backref='experiments')
    results = Column(JSON, default={})
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class ExperimentResult(Base):
    __tablename__ = 'experiment_results'
    id = Column(Integer, primary_key=True, index=True)
    experiment_id = Column(Integer, ForeignKey('experiments.id'), nullable=False)
    experiment = relationship('Experiment', backref='result_records')
    variant = Column(String, nullable=False)
    product_id = Column(Integer)
    quantity = Column(Integer)
    original_price = Column(Float)
    final_price = Column(Float)
    discount_amount = Column(Float)
    extra_data = Column(JSON, default={})
    timestamp = Column(DateTime, default=datetime.utcnow)