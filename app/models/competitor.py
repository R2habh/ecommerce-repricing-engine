from pydantic import BaseModel
from datetime import datetime


class CompetitorPrice(BaseModel):
    product_id: str
    competitor_name: str
    competitor_product_id: str | None = None
    product_title: str
    price: float
    currency: str = "USD"
    available: bool = True
    collected_at: datetime