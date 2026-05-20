from __future__ import annotations

from src.ui.shared.model.interface.movement_strategy import MovementStrategy
from src.ui.shared.model.pid import PID


class PIDMovementStrategy(MovementStrategy):
    def __init__(self, kp: float, ki: float, kd: float) -> None:
        self._pid = PID(kp=kp, ki=ki, kd=kd)

    def update(self, current_value: float, target_value: float) -> float:
        error = target_value - current_value
        return current_value + self._pid.update(error)

    def reset(self) -> None:
        self._pid.reset()
