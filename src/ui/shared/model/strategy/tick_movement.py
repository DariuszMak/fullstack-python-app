from __future__ import annotations

from src.ui.shared.model.strategy.interface.movement_strategy import MovementStrategy


class TickMovement(MovementStrategy):
    def update(self, _: float, target_value: float) -> float:
        return float(target_value)
