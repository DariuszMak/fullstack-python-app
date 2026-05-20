from __future__ import annotations

import logging
from datetime import UTC, datetime, timedelta, timezone
from typing import TYPE_CHECKING, cast
from unittest.mock import MagicMock, patch

import pytest

from src.ui.shared.controller.clock_controller import ClockController
from src.ui.shared.model.data_types import ClockHands

if TYPE_CHECKING:
    from src.ui.shared.model.strategy.pid_strategy import PIDMovementStrategy


def make_dt(hour: int = 12, minute: int = 0, second: int = 0, tz: timezone = UTC) -> datetime:
    return datetime(2024, 1, 1, hour, minute, second, tzinfo=tz)


def test_initial_clock_hands_are_zero() -> None:
    controller = ClockController(start_time=make_dt())
    assert controller._clock_hands == ClockHands(0.0, 0.0, 0.0)


def test_three_pid_strategies_created() -> None:
    controller = ClockController(start_time=make_dt())
    assert len(controller._strategies) == 3


def test_start_time_stored() -> None:
    start = make_dt(10, 30, 0)
    controller = ClockController(start_time=start)
    assert controller._start_time == start


def test_update_changes_clock_hands_from_zero() -> None:
    start = make_dt(12, 0, 0)
    controller = ClockController(start_time=start)
    now = start + timedelta(seconds=5)

    controller.update(now)

    hands = controller._clock_hands
    assert hands.second != pytest.approx(0.0) or hands.minute != pytest.approx(0.0) or hands.hour != pytest.approx(0.0)


def test_update_called_multiple_times_advances_hands() -> None:
    start = make_dt(12, 0, 0)
    controller = ClockController(start_time=start)

    controller.update(start + timedelta(seconds=1))
    hands_after_first = ClockHands(
        controller._clock_hands.second,
        controller._clock_hands.minute,
        controller._clock_hands.hour,
    )

    controller.update(start + timedelta(seconds=10))
    hands_after_second = controller._clock_hands

    assert hands_after_second.second >= hands_after_first.second


def test_update_with_zero_elapsed_time() -> None:
    start = make_dt(12, 0, 0)
    controller = ClockController(start_time=start)

    controller.update(start)

    hands = controller._clock_hands
    assert abs(hands.second) < 1.0
    assert abs(hands.minute) < 1.0
    assert abs(hands.hour) < 1.0


@patch("src.ui.shared.controller.clock_controller.update_clock_hands")
@patch("src.ui.shared.controller.clock_controller.calculate_clock_hands_angles")
def test_update_delegates_to_helpers(mock_calc: MagicMock, mock_update: MagicMock) -> None:
    target = ClockHands(10.0, 5.0, 1.0)
    new_hands = ClockHands(9.0, 4.5, 0.9)
    mock_calc.return_value = target
    mock_update.return_value = new_hands

    start = make_dt()
    controller = ClockController(start_time=start)
    now = start + timedelta(seconds=30)

    controller.update(now)

    mock_calc.assert_called_once_with(start, now - start)
    mock_update.assert_called_once_with(ClockHands(0.0, 0.0, 0.0), target, controller._strategies)
    assert controller._clock_hands == new_hands


def test_reset_updates_start_time() -> None:
    original_start = make_dt(8, 0, 0)
    controller = ClockController(start_time=original_start)

    new_start = make_dt(10, 0, 0)
    controller.reset(new_start)

    assert controller._start_time == new_start


def test_reset_zeroes_clock_hands() -> None:
    start = make_dt()
    controller = ClockController(start_time=start)
    controller.update(start + timedelta(seconds=30))

    controller.reset(make_dt(9, 0, 0))

    assert controller._clock_hands == ClockHands(0.0, 0.0, 0.0)


def test_reset_calls_strategy_reset() -> None:
    controller = ClockController(start_time=make_dt())
    mock_strategies = [MagicMock() for _ in range(3)]

    controller._strategies = cast(
        "tuple[PIDMovementStrategy, PIDMovementStrategy, PIDMovementStrategy]",
        tuple(mock_strategies),
    )

    controller.reset(make_dt(11, 0, 0))

    for strategy in mock_strategies:
        strategy.reset.assert_called_once()


def test_reset_logs_warning_when_strategy_reset_raises(caplog: pytest.LogCaptureFixture) -> None:
    controller = ClockController(start_time=make_dt())

    failing_strategy = MagicMock()
    failing_strategy.reset.side_effect = RuntimeError("boom")
    controller._strategies = cast(
        "tuple[PIDMovementStrategy, PIDMovementStrategy, PIDMovementStrategy]",
        (failing_strategy, failing_strategy, failing_strategy),
    )

    with caplog.at_level(logging.WARNING, logger="src.ui.shared.controller.clock_controller"):
        controller.reset(make_dt(11, 0, 0))

    assert any("boom" in record.message for record in caplog.records)


def test_after_reset_update_uses_new_start_time() -> None:
    start = make_dt(12, 0, 0)
    controller = ClockController(start_time=start)
    controller.update(start + timedelta(minutes=5))

    new_start = make_dt(6, 0, 0)
    controller.reset(new_start)
    controller.update(new_start + timedelta(seconds=5))

    assert controller._start_time == new_start

    hands = controller._clock_hands
    assert abs(hands.second) < 60.0
