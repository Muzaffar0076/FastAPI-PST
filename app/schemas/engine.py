from pydantic import BaseModel

class PriceRequest(BaseModel):
    product_id: int
    quantity: int = 1
