def minimum_allowed_price(cost: float, minimum_margin_percent: float) -> float:
    return cost * (1 + minimum_margin_percent / 100)


def margin_percent(cost: float, price: float) -> float:
    if price <= 0:
        return 0.0
    return ((price - cost) / price) * 100