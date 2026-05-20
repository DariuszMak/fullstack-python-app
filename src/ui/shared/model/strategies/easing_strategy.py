from __future__ import annotations

from src.ui.shared.model.interface.movement_strategy import MovementStrategy


class EasingMovementStrategy(MovementStrategy):
    def __init__(self, factor: float = 0.1) -> None:
        self._factor = float(factor)

    def update(self, current_value: float, target_value: float) -> float:
        return current_value + (target_value - current_value) * self._factor
