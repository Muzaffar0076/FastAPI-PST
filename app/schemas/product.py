from pydantic import BaseModel
from decimal import Decimal

class ProductBase(BaseModel):
    sku: str
    title: str
    base_price: Decimal
    category: str | None = None
    stock: int = 0


class ProductCreate(ProductBase):
    pass


class ProductResponse(ProductBase):
    id: int

    class Config:
        orm_mode = True
