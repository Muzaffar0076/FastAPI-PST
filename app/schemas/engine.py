from pydantic import BaseModel
from typing import Optional

class PriceRequest(BaseModel):
    product_id: int
    quantity: int = 1
    target_currency: Optional[str] = None  # Convert to this currency (ISO code)
    include_tax: Optional[bool] = None  # Override product tax_inclusive setting
    rounding_strategy: str = "half_up"  # half_up, half_down, up, down, nearest
