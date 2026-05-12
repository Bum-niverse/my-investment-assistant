from __future__ import annotations


def calculate_position_value(quantity: float, current_price: float) -> float:
    return quantity * current_price


def calculate_position_weight(position_value: float, total_assets: float) -> float:
    if total_assets <= 0:
        raise ValueError("total_assets must be greater than 0")
    return position_value / total_assets * 100


def calculate_loss_at_stop(quantity: float, current_price: float, stop_loss: float) -> float:
    return max(0.0, (current_price - stop_loss) * quantity)


def classify_position_weight(weight_percent: float) -> str:
    if weight_percent < 5:
        return "낮은 비중"
    if weight_percent < 10:
        return "보통 비중"
    if weight_percent < 20:
        return "높은 비중"
    return "집중 투자"


def risk_summary(
    quantity: float,
    current_price: float,
    stop_loss: float,
    total_assets: float,
) -> dict:
    position_value = calculate_position_value(quantity, current_price)
    weight = calculate_position_weight(position_value, total_assets)
    loss_at_stop = calculate_loss_at_stop(quantity, current_price, stop_loss)
    loss_ratio = calculate_position_weight(loss_at_stop, total_assets)

    return {
        "position_value": position_value,
        "position_weight_percent": weight,
        "position_weight_class": classify_position_weight(weight),
        "loss_at_stop": loss_at_stop,
        "loss_ratio_to_total_assets_percent": loss_ratio,
    }
