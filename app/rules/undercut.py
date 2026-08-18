from app.models.product import Product
from app.models.competitor import CompetitorPrice
from app.services.competitor import get_lowest_price
from app.services.margin import minimum_allowed_price


def recommend_undercut_price(
    product: Product,
    competitors: list[CompetitorPrice],
    undercut_amount: float = 1.0,
):
    lowest = get_lowest_price(competitors)

    minimum_price = minimum_allowed_price(
        product.cost,
        product.minimum_margin_percent,
    )

    if lowest is None:
        return {
            "recommended_price": product.current_price,
            "reason": "No available competitor prices.",
            "safe_to_apply": False,
        }

    target_price = lowest - undercut_amount

    recommended = max(target_price, minimum_price)

    return {
        "recommended_price": round(recommended, 2),
        "reason": (
            f"Targeting ₹{undercut_amount:.2f} below "
            f"lowest competitor."
        ),
        "safe_to_apply": recommended >= minimum_price,
    }