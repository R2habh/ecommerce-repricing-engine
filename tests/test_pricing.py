from app.models.product import Product
from app.models.competitor import CompetitorPrice
from app.rules.undercut import recommend_undercut_price


def test_undercuts_lowest_competitor():
    product = Product(
        id="P001",
        sku="SKU001",
        title="Wireless Headphones",
        cost=700,
        current_price=999,
        currency="INR",
        minimum_margin_percent=15,
    )

    competitors = [
        CompetitorPrice(
            product_id="P001",
            competitor_name="A",
            product_title="Wireless Headphones",
            price=949,
            currency="INR",
            available=True,
            collected_at="2026-08-18T09:00:00",
        ),
        CompetitorPrice(
            product_id="P001",
            competitor_name="B",
            product_title="Wireless Headphones",
            price=979,
            currency="INR",
            available=True,
            collected_at="2026-08-18T09:00:00",
        ),
    ]

    result = recommend_undercut_price(product, competitors)

    assert result["recommended_price"] == 948
    assert result["safe_to_apply"] is True