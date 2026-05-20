from __future__ import annotations

from typing import TYPE_CHECKING

import structlog

from src.ui.shared.controller.update_logic import update_clock_hands
from src.ui.shared.helpers import calculate_clock_hands_angles
from src.ui.shared.model.data_types import ClockHands
from src.ui.shared.model.strategy.pid_movement import PIDMovementStrategy

if TYPE_CHECKING:
    from datetime import datetime

logger = structlog.get_logger(__name__)


class ClockController:
    def __init__(self, start_time: datetime) -> None:
        self._start_time = start_time

        self._strategies = (
            PIDMovementStrategy(0.15, 0.005, 0.005),
            PIDMovementStrategy(0.08, 0.004, 0.004),
            PIDMovementStrategy(0.08, 0.002, 0.002),
        )

        self._clock_hands = ClockHands(0.0, 0.0, 0.0)
        logger.debug("clock_controller_initialized", start_time=start_time.isoformat())

    def update(self, now: datetime) -> None:
        duration = now - self._start_time
        target = calculate_clock_hands_angles(self._start_time, duration)

        self._clock_hands = update_clock_hands(self._clock_hands, target, self._strategies)

    def reset(self, new_start_time: datetime) -> None:
        log = logger.bind(new_start_time=new_start_time.isoformat())
        log.info("resetting_clock_controller")

        self._start_time = new_start_time
        self._clock_hands = ClockHands(0.0, 0.0, 0.0)

        for i, strategy in enumerate(self._strategies):
            try:
                strategy.reset()
            except Exception as e:
                log.warning("strategy_reset_failed", strategy_index=i, error=str(e))
