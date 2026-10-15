import math

import pytest

from src.frontend.shared.model.data_types import ClockHands
from src.frontend.shared.model.pid import PID


def approx_eq(a: float, b: float, epsilon: float = 1e-10) -> bool:
    return abs(a - b) < epsilon


def test_pid_update() -> None:
    pid = PID(kp=1.0, ki=0.1, kd=0.5)
    output1 = pid.update(1.0)
    assert output1 == pytest.approx(1.0 + 0.1 + 0.5)

    output2 = pid.update(0.5)
    expected = 0.5 * pid._kp + (1.0 + 0.5) * pid._ki + (0.5 - 1.0) * pid._kd
    assert output2 == pytest.approx(expected)


def test_pid_reset() -> None:
    pid = PID(kp=1.0, ki=0.1, kd=0.5)
    pid.update(1.0)
    pid.update(0.5)
    assert pid._integral != pytest.approx(0.0)
    assert pid._prev_error != pytest.approx(0.0)

    pid.reset()
    assert pid._integral == pytest.approx(0.0)
    assert pid._prev_error == pytest.approx(0.0)


def test_clock_hands_reset() -> None:
    hands = ClockHands(second=10.5, minute=20.3, hour=5.7)
    assert hands.second == pytest.approx(10.5)
    assert hands.minute == pytest.approx(20.3)
    assert hands.hour == pytest.approx(5.7)

    hands.second = 0.0
    hands.minute = 0.0
    hands.hour = 0.0

    assert hands.second == pytest.approx(0.0)
    assert hands.minute == pytest.approx(0.0)
    assert hands.hour == pytest.approx(0.0)


def test_clock_hands_angles_in_radians() -> None:
    hands = ClockHands(second=15.0, minute=30.0, hour=6.0)

    s_rad = (hands.second / 60.0) * 2.0 * math.pi
    m_rad = (hands.minute / 60.0) * 2.0 * math.pi
    h_rad = (hands.hour / 12.0) * 2.0 * math.pi

    assert approx_eq(s_rad, math.pi / 2.0)
    assert approx_eq(m_rad, math.pi)
    assert approx_eq(h_rad, math.pi)


def test_clock_hands_angles_edge_cases() -> None:
    def rad(h: float, max_val: float) -> float:
        return (h / max_val) * 2.0 * math.pi

    cases = [
        (0.0, 0.0, 0.0),
        (30.0, 30.0, 6.0),
        (60.0, 60.0, 12.0),
        (15.0, 15.0, 3.0),
    ]

    for s, m, h in cases:
        hands = ClockHands(second=s, minute=m, hour=h)
        s_rad, m_rad, h_rad = rad(hands.second, 60.0), rad(hands.minute, 60.0), rad(hands.hour, 12.0)
        assert approx_eq(s_rad, (s / 60.0) * 2.0 * math.pi)
        assert approx_eq(m_rad, (m / 60.0) * 2.0 * math.pi)
        assert approx_eq(h_rad, (h / 12.0) * 2.0 * math.pi)
