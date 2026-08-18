from app.models.competitor import CompetitorPrice


def get_lowest_price(competitors: list[CompetitorPrice]) -> float | None:
    available_prices = [
        competitor.price
        for competitor in competitors
        if competitor.available and competitor.price > 0
    ]

    if not available_prices:
        return None

    return min(available_prices)