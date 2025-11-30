from pydantic import BaseModel
from decimal import Decimal

class ProductBase(BaseModel):
    sku: str
    title: str
    base_price: Decimal
    currency: str = "INR"  # ISO currency code
    tax_rate: Decimal = Decimal("0.0")  # Tax rate as percentage
    tax_inclusive: bool = False  # True if price includes tax
    max_discount_cap: Decimal | None = None  # Maximum discount amount allowed (None = no cap)
    category: str | None = None
    stock: int = 0


class ProductCreate(ProductBase):
    pass


class ProductUpdate(BaseModel):
    sku: str | None = None
    title: str | None = None
    base_price: Decimal | None = None
    currency: str | None = None
    tax_rate: Decimal | None = None
    tax_inclusive: bool | None = None
    max_discount_cap: Decimal | None = None
    category: str | None = None
    stock: int | None = None


class ProductResponse(ProductBase):
    id: int

    class Config:
        orm_mode = True
