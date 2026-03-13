from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass
class LogicMetrics:
    weekly_progress_rate: Optional[float]
    goal_achievement_percentage: Optional[float]
    time_to_goal_weeks: Optional[float]


def weekly_progress_rate(
    *,
    weight_history: Optional[list[float]] = None,
    current_weight: Optional[float] = None,
    previous_weight: Optional[float] = None,
    elapsed_weeks: float = 1.0,
) -> Optional[float]:
    """
    Compute weekly progress rate (kg/week).

    Positive value => weight increased.
    Negative value => weight decreased.
    """
    if weight_history and len(weight_history) >= 2:
        cleaned = [float(v) for v in weight_history if v is not None]
        if len(cleaned) >= 2:
            weeks = max(1.0, float(len(cleaned) - 1))
            return (cleaned[-1] - cleaned[0]) / weeks

    if current_weight is None or previous_weight is None:
        return None
    if elapsed_weeks <= 0:
        return None
    return (float(current_weight) - float(previous_weight)) / float(elapsed_weeks)


def goal_achievement_percentage(
    *,
    start_value: Optional[float],
    current_value: Optional[float],
    target_value: Optional[float],
    direction: str = "decrease",
) -> Optional[float]:
    """
    Compute how much of the goal has been achieved in percentage.

    direction:
    - "decrease": goal is to go down (e.g., fat loss)
    - "increase": goal is to go up (e.g., muscle gain / strength)
    """
    if start_value is None or current_value is None or target_value is None:
        return None

    start = float(start_value)
    current = float(current_value)
    target = float(target_value)

    if direction == "increase":
        denominator = target - start
        if denominator == 0:
            return 100.0
        progress = (current - start) / denominator
    else:
        denominator = start - target
        if denominator == 0:
            return 100.0
        progress = (start - current) / denominator

    progress_pct = max(0.0, min(100.0, progress * 100.0))
    return progress_pct


def time_to_goal_estimation(
    *,
    current_value: Optional[float],
    target_value: Optional[float],
    weekly_rate: Optional[float],
    direction: str = "decrease",
) -> Optional[float]:
    """
    Estimate remaining weeks to reach target.

    Returns None when rate is missing, zero, or moving away from target.
    """
    if current_value is None or target_value is None or weekly_rate is None:
        return None

    current = float(current_value)
    target = float(target_value)
    rate = float(weekly_rate)

    if rate == 0:
        return None

    remaining = target - current
    moving_toward_target = remaining * rate > 0
    if not moving_toward_target:
        return None

    return abs(remaining / rate)


def evaluate_logic_metrics(
    *,
    start_value: Optional[float],
    current_value: Optional[float],
    target_value: Optional[float],
    direction: str = "decrease",
    weight_history: Optional[list[float]] = None,
    previous_value: Optional[float] = None,
    elapsed_weeks: float = 1.0,
) -> LogicMetrics:
    rate = weekly_progress_rate(
        weight_history=weight_history,
        current_weight=current_value,
        previous_weight=previous_value,
        elapsed_weeks=elapsed_weeks,
    )
    achievement = goal_achievement_percentage(
        start_value=start_value,
        current_value=current_value,
        target_value=target_value,
        direction=direction,
    )
    eta = time_to_goal_estimation(
        current_value=current_value,
        target_value=target_value,
        weekly_rate=rate,
        direction=direction,
    )
    return LogicMetrics(
        weekly_progress_rate=rate,
        goal_achievement_percentage=achievement,
        time_to_goal_weeks=eta,
    )

