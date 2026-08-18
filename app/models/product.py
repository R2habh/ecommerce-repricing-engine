from pydantic import BaseModel


class Product(BaseModel):
    id: str
    sku: str
    title: str
    brand: str | None = None
    category: str | None = None
    cost: float
    current_price: float
    currency: str = "USD"
    minimum_margin_percent: float = 10.0
    maximum_price_change_percent: float = 20.0
    active: bool = True