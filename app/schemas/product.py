from pydantic import BaseModel
from datetime import date

class ProductCreate(BaseModel):
    name: str
    description: str | None = None
    purchase_price: float
    sale_price: float
    quantity: int
    expiration_date: date | None = None
    rupture_threshold: int = 5
    supplier_id: int


class ProductResponse(BaseModel):
    id: int
    name: str
    quantity: int
    sale_price: float

    class Config:
        from_attributes = True
