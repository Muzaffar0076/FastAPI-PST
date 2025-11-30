from datetime import datetime
from pydantic import BaseModel

class PromotionBase(BaseModel):
    name: str
    discount_type: str
    discount_value: float | None = None
    buy_quantity: int | None = None
    get_quantity: int | None = None
    min_quantity: int | None = None
    min_amount: float | None = None
    category_filter: str | None = None
    applies_to_category: bool = False
    priority: int = 0
    stacking_enabled: bool = False
    start_date: datetime
    end_date: datetime
    is_active: bool = True
    product_id: int | None = None

class PromotionCreate(PromotionBase):
    pass

class PromotionUpdate(BaseModel):
    name: str | None = None
    discount_type: str | None = None
    discount_value: float | None = None
    buy_quantity: int | None = None
    get_quantity: int | None = None
    min_quantity: int | None = None
    min_amount: float | None = None
    category_filter: str | None = None
    applies_to_category: bool | None = None
    priority: int | None = None
    stacking_enabled: bool | None = None
    start_date: datetime | None = None
    end_date: datetime | None = None
    is_active: bool | None = None
    product_id: int | None = None

class PromotionResponse(PromotionBase):
    id: int
    class Config:
        orm_mode = True
