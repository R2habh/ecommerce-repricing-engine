from pydantic import BaseModel


class PriceRecommendation(BaseModel):
    product_id: str
    current_price: float
    recommended_price: float
    lowest_competitor_price: float | None = None
    minimum_allowed_price: float
    price_change_percent: float
    reason: str
    safe_to_apply: bool