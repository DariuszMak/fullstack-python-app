import pytest

from src.ui.shared.model.strategy.easing_movement import EasingMovementStrategy
from src.ui.shared.model.strategy.interface.movement_strategy import MovementStrategy
from src.ui.shared.model.strategy.pid_strategy import PIDMovementStrategy
from src.ui.shared.model.strategy.tick_strategy import TickMovementStrategy


def test_movement_strategy_is_abstract() -> None:
    with pytest.raises(TypeError):
        MovementStrategy()  # type: ignore[abstract]


def test_easing_strategy_moves_fractionally() -> None:
    strategy = EasingMovementStrategy(factor=0.2)
    assert strategy.update(0.0, 10.0) == pytest.approx(2.0)
    assert strategy.update(5.0, 15.0) == pytest.approx(7.0)


def test_easing_strategy_factor_1_moves_directly() -> None:
    strategy = EasingMovementStrategy(factor=1.0)
    assert strategy.update(3.0, 10.0) == pytest.approx(10.0)


def test_easing_strategy_factor_0_stays_same() -> None:
    strategy = EasingMovementStrategy(factor=0.0)
    assert strategy.update(3.0, 10.0) == pytest.approx(3.0)


def test_tick_strategy_snaps_to_target() -> None:
    strategy = TickMovementStrategy()
    assert strategy.update(5.0, 20.0) == pytest.approx(20.0)
    assert strategy.update(-10.0, -3.5) == pytest.approx(-3.5)


def test_pid_strategy_moves_toward_target() -> None:
    strategy = PIDMovementStrategy(0.1, 0.0, 0.0)
    v1 = strategy.update(0.0, 10.0)
    assert v1 > 0.0
    v2 = strategy.update(v1, 10.0)
    assert v2 > v1


def test_pid_strategy_reset() -> None:
    strategy = PIDMovementStrategy(0.1, 0.1, 0.0)
    v1 = strategy.update(0.0, 10.0)
    strategy.reset()
    v2 = strategy.update(0.0, 10.0)
    assert v2 == pytest.approx(v1)
