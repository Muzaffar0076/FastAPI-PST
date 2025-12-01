from pydantic import BaseModel
from typing import Optional

class PriceRequest(BaseModel):
    product_id: int
    quantity: int = 1
    target_currency: Optional[str] = None
    include_tax: Optional[bool] = None
    rounding_strategy: str = 'half_up'