from pydantic import BaseModel
from datetime import datetime
from typing import Optional, Dict, Any

class ExperimentBase(BaseModel):
    name: str
    description: Optional[str] = None
    experiment_type: str = 'promotion_comparison'
    control_config: Dict[str, Any]
    variant_config: Dict[str, Any]
    traffic_split: float = 50.0
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    is_active: bool = False
    product_id: Optional[int] = None

class ExperimentCreate(ExperimentBase):
    pass

class ExperimentUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None
    control_config: Optional[Dict[str, Any]] = None
    variant_config: Optional[Dict[str, Any]] = None
    traffic_split: Optional[float] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    is_active: Optional[bool] = None
    product_id: Optional[int] = None

class ExperimentResponse(ExperimentBase):
    id: int
    status: str
    results: Dict[str, Any]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class ExperimentResultCreate(BaseModel):
    experiment_id: int
    variant: str
    product_id: int
    quantity: int
    original_price: float
    final_price: float
    discount_amount: float
    extra_data: Optional[Dict[str, Any]] = None

class ExperimentResultResponse(BaseModel):
    id: int
    experiment_id: int
    variant: str
    product_id: int
    quantity: int
    original_price: float
    final_price: float
    discount_amount: float
    extra_data: Dict[str, Any]
    timestamp: datetime

    class Config:
        from_attributes = True