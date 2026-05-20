import math
from datetime import UTC, datetime, timedelta, timezone

import pytest
from PySide6.QtCore import QPointF

from src.ui.shared.helpers import (
    calculate_clock_hands_angles,
    clock_hands_in_radians,
    convert_clock_pid_to_cartesian,
    format_datetime,
    polar_to_cartesian,
)
from src.ui.shared.model.data_types import ClockHands


def test_polar_to_cartesian_zero_angle() -> None:
    center = QPointF(100.0, 100.0)
    res = polar_to_cartesian(center, 50.0, 0.0)
    assert abs(res.x() - center.x()) < 1e-10
    assert abs(res.y() - (center.y() - 50.0)) < 1e-10


def test_polar_to_cartesian_quarter_angle() -> None:
    center = QPointF(0.0, 0.0)
    res = polar_to_cartesian(center, 1.0, math.pi / 2.0)
    assert abs(res.x() - 1.0) < 1e-10
    assert abs(res.y() - 0.0) < 1e-10


def test_polar_to_cartesian_90_degrees() -> None:
    length = 10.0
    angle = math.pi / 2.0
    res = polar_to_cartesian(QPointF(0.0, 0.0), length, angle)
    assert abs(res.x() - 10.0) < 1e-5
    assert abs(res.y() - 0.0) < 1e-5


def test_polar_to_cartesian_180_degrees() -> None:
    length = 10.0
    angle = math.pi
    res = polar_to_cartesian(QPointF(0.0, 0.0), length, angle)
    assert abs(res.x() - 0.0) < 1e-5
    assert abs(res.y() - 10.0) < 1e-5


def test_clock_hands_in_radians_zero() -> None:
    hands = ClockHands(second=0.0, minute=0.0, hour=0.0)

    second, minute, hour = clock_hands_in_radians(hands)

    assert second == pytest.approx(0.0)
    assert minute == pytest.approx(0.0)
    assert hour == pytest.approx(0.0)


def test_clock_hands_in_radians_quarter_turn() -> None:
    hands = ClockHands(second=15.0, minute=15.0, hour=3.0)

    second, minute, hour = clock_hands_in_radians(hands)

    assert second == pytest.approx(math.pi / 2.0)
    assert minute == pytest.approx(math.pi / 2.0)
    assert hour == pytest.approx(math.pi / 2.0)


def test_clock_hands_in_radians_half_turn() -> None:
    hands = ClockHands(second=30.0, minute=30.0, hour=6.0)

    second, minute, hour = clock_hands_in_radians(hands)

    assert second == pytest.approx(math.pi)
    assert minute == pytest.approx(math.pi)
    assert hour == pytest.approx(math.pi)


def test_clock_hands_in_radians_full_turn() -> None:
    hands = ClockHands(second=60.0, minute=60.0, hour=12.0)

    second, minute, hour = clock_hands_in_radians(hands)

    assert second == pytest.approx(2.0 * math.pi)
    assert minute == pytest.approx(2.0 * math.pi)
    assert hour == pytest.approx(2.0 * math.pi)


def test_clock_hands_in_radians_fractional_values() -> None:
    hands = ClockHands(second=7.5, minute=22.5, hour=1.5)

    second, minute, hour = clock_hands_in_radians(hands)

    assert second == pytest.approx(math.pi / 4.0)
    assert minute == pytest.approx(3.0 * math.pi / 4.0)
    assert hour == pytest.approx(math.pi / 4.0)


def test_clock_hands_in_radians_large_values() -> None:
    hands = ClockHands(second=90.0, minute=90.0, hour=18.0)

    second, minute, hour = clock_hands_in_radians(hands)

    assert second == pytest.approx(3.0 * math.pi)
    assert minute == pytest.approx(3.0 * math.pi)
    assert hour == pytest.approx(3.0 * math.pi)


def test_midnight_clock_hands_angles() -> None:
    dt = datetime(2025, 4, 27, 0, 0, 0, tzinfo=UTC)
    duration = timedelta(0)
    angles = calculate_clock_hands_angles(dt, duration, display_tz=UTC)
    assert angles.second == pytest.approx(0.0)
    assert angles.minute == pytest.approx(0.0)
    assert angles.hour == pytest.approx(0.0)


def test_noon_clock_hands_angles() -> None:
    dt = datetime(2025, 4, 27, 12, 0, 0, tzinfo=UTC)
    duration = timedelta(0)
    angles = calculate_clock_hands_angles(dt, duration, display_tz=UTC)
    assert angles.second == pytest.approx(0.0)
    assert angles.minute == pytest.approx(0.0)
    assert angles.hour == pytest.approx(0.0)


def test_noon_clock_hands_angles_from_milliseconds() -> None:
    dt = datetime(2025, 4, 27, 0, 0, 0, tzinfo=UTC)
    duration = timedelta(milliseconds=12 * 60 * 60 * 1000)
    angles = calculate_clock_hands_angles(dt, duration, display_tz=UTC)
    assert angles.second == pytest.approx(43200.0)
    assert angles.minute == pytest.approx(720.0)
    assert angles.hour == pytest.approx(12.0)


def test_maximum_clock_hands_angles() -> None:
    dt = datetime(2025, 4, 27, 23, 59, 59, tzinfo=UTC)
    duration = timedelta(0)
    angles = calculate_clock_hands_angles(dt, duration, display_tz=UTC)
    assert angles.second == pytest.approx(59.0)
    assert angles.minute == pytest.approx(59.983334, rel=1e-6)
    assert angles.hour == pytest.approx(11.9997225, rel=1e-6)


def test_maximum_clock_hands_angles_from_milliseconds() -> None:
    dt = datetime(2025, 4, 27, 0, 0, 0, tzinfo=UTC)
    duration = timedelta(milliseconds=(23 * 60 * 60 * 1000 + 59 * 60 * 1000 + 59 * 1000 + 999))
    angles = calculate_clock_hands_angles(dt, duration, display_tz=UTC)
    assert angles.second == pytest.approx(86400.0)
    assert angles.minute == pytest.approx(1440.0)
    assert angles.hour == pytest.approx(24.0)


def test_half_past_three_clock_hands_angles() -> None:
    dt = datetime(2025, 4, 27, 3, 30, 0, tzinfo=UTC)
    duration = timedelta(0)
    angles = calculate_clock_hands_angles(dt, duration, display_tz=UTC)
    assert angles.second == pytest.approx(0.0)
    assert angles.minute == pytest.approx(30.0)
    assert angles.hour == pytest.approx(3.5)


def test_half_past_three_clock_hands_angles_from_milliseconds() -> None:
    dt = datetime(2025, 4, 27, 0, 0, 0, tzinfo=UTC)
    duration = timedelta(milliseconds=(3 * 60 * 60 * 1000 + 30 * 60 * 1000))
    angles = calculate_clock_hands_angles(dt, duration, display_tz=UTC)
    assert angles.second == pytest.approx(12600.0)
    assert angles.minute == pytest.approx(210.0)
    assert angles.hour == pytest.approx(3.5)


def test_circled_clock_hands_angles() -> None:
    dt = datetime(2025, 4, 27, 0, 0, 0, tzinfo=UTC)
    duration = timedelta(milliseconds=(33 * 60 * 60 * 1000 + 65 * 60 * 1000 + 61 * 1000 + 2))
    angles = calculate_clock_hands_angles(dt, duration, display_tz=UTC)
    assert angles.second == pytest.approx(122761.0)
    assert angles.minute == pytest.approx(2046.0167, rel=1e-5)
    assert angles.hour == pytest.approx(34.100277, rel=1e-5)


def test_circled_clock_hands_angles_after_month() -> None:
    dt = datetime(2025, 4, 27, 0, 0, 0, tzinfo=UTC)
    duration = timedelta(milliseconds=(37 * 24 * 60 * 60 * 1000 + 65 * 60 * 1000 + 61 * 1000 + 2))
    angles = calculate_clock_hands_angles(dt, duration, display_tz=UTC)
    assert angles.second == pytest.approx(3200761.0)
    assert angles.minute == pytest.approx(53346.016, rel=1e-5)
    assert angles.hour == pytest.approx(889.1003, rel=1e-5)


def test_clock_hands_angles_from_epoch_to_recent_date() -> None:
    epoch = datetime(1970, 1, 1, 0, 0, 0, tzinfo=UTC)
    recent = datetime(2025, 4, 27, 15, 30, 45, tzinfo=UTC)

    duration = recent - epoch

    angles = calculate_clock_hands_angles(epoch, duration, display_tz=UTC)

    total_seconds = duration.total_seconds()
    total_minutes = total_seconds / 60.0
    total_hours = total_seconds / 3600.0

    assert angles.second == pytest.approx(total_seconds, rel=1e-9)
    assert angles.minute == pytest.approx(total_minutes, rel=1e-9)
    assert angles.hour == pytest.approx(total_hours, rel=1e-9)

    assert angles.second > 60.0 * 1_000_000
    assert angles.minute > 60.0 * 10_000
    assert angles.hour > 12.0 * 1_000


def test_timezone_utc_plus1_shows_local_hour() -> None:
    tz_plus1 = timezone(timedelta(hours=1))

    local_dt = datetime(2025, 4, 27, 15, 30, 0, tzinfo=tz_plus1)

    angles = calculate_clock_hands_angles(local_dt, timedelta(0), display_tz=tz_plus1)

    assert angles.second == pytest.approx(0.0)
    assert angles.minute == pytest.approx(30.0)
    assert angles.hour == pytest.approx(3.5)


def test_timezone_utc_and_local_same_instant_differ_by_offset() -> None:
    tz_plus1 = timezone(timedelta(hours=1))
    utc_dt = datetime(2025, 4, 27, 14, 30, 0, tzinfo=UTC)
    local_dt = utc_dt.astimezone(tz_plus1)

    angles_utc = calculate_clock_hands_angles(utc_dt, timedelta(0), display_tz=UTC)
    angles_local = calculate_clock_hands_angles(local_dt, timedelta(0), display_tz=tz_plus1)

    assert angles_utc.hour == pytest.approx(2.5)

    assert angles_local.hour == pytest.approx(3.5)

    assert angles_local.hour - angles_utc.hour == pytest.approx(1.0)


def test_timezone_utc_minus5_shows_local_hour() -> None:
    tz_minus5 = timezone(timedelta(hours=-5))
    local_dt = datetime(2025, 4, 27, 15, 0, 0, tzinfo=tz_minus5)

    angles = calculate_clock_hands_angles(local_dt, timedelta(0), display_tz=tz_minus5)

    assert angles.second == pytest.approx(0.0)
    assert angles.minute == pytest.approx(0.0)
    assert angles.hour == pytest.approx(3.0)


def test_timezone_utc_offset_does_not_bleed_into_elapsed() -> None:
    tz_plus2 = timezone(timedelta(hours=2))

    start_local = datetime(2025, 4, 27, 0, 0, 0, tzinfo=tz_plus2)

    duration = timedelta(hours=1)

    angles = calculate_clock_hands_angles(start_local, duration, display_tz=tz_plus2)

    assert angles.second == pytest.approx(3600.0)
    assert angles.minute == pytest.approx(60.0)
    assert angles.hour == pytest.approx(1.0)


def test_timezone_noon_in_utc_plus1_is_not_midnight() -> None:
    tz_plus1 = timezone(timedelta(hours=1))
    utc_dt = datetime(2025, 4, 27, 11, 0, 0, tzinfo=UTC)

    angles = calculate_clock_hands_angles(utc_dt, timedelta(0), display_tz=tz_plus1)

    assert angles.hour == pytest.approx(0.0)
    assert angles.minute == pytest.approx(0.0)
    assert angles.second == pytest.approx(0.0)


def test_timezone_old_bug_utc_shows_wrong_hour_on_utc_plus1() -> None:
    tz_plus1 = timezone(timedelta(hours=1))
    utc_dt = datetime(2025, 4, 27, 14, 30, 0, tzinfo=UTC)

    angles_wrong = calculate_clock_hands_angles(utc_dt, timedelta(0), display_tz=UTC)
    angles_correct = calculate_clock_hands_angles(utc_dt, timedelta(0), display_tz=tz_plus1)

    assert angles_wrong.hour == pytest.approx(2.5)
    assert angles_correct.hour == pytest.approx(3.5)


def test_format_datetime() -> None:
    dt = datetime(2024, 1, 2, 3, 4, 5, 678901, tzinfo=UTC)
    result = format_datetime(dt)
    assert result == "03:04:05.678"


def test_convert_clock_pid_to_cartesian() -> None:
    center = QPointF(100.0, 100.0)
    radius = 50.0

    clock_angles = ClockHands(
        second=0.0,
        minute=15.0,
        hour=6.0,
    )

    hands = convert_clock_pid_to_cartesian(clock_angles, center, radius)

    assert hands.second == QPointF(100.0, 100.0 - radius * 0.9)
    assert hands.minute == QPointF(100.0 + radius * 0.7, 100.0)
    assert hands.hour == QPointF(100.0, 100.0 + radius * 0.5)


def test_naive_datetime_used_as_local_no_conversion() -> None:
    naive_dt = datetime(2025, 4, 27, 3, 30, 0)  # noqa: DTZ001
    angles = calculate_clock_hands_angles(naive_dt, timedelta(0))
    assert angles.second == pytest.approx(0.0)
    assert angles.minute == pytest.approx(30.0)
    assert angles.hour == pytest.approx(3.5)


def test_naive_datetime_no_display_tz_does_not_shift() -> None:
    naive_dt = datetime(2025, 4, 27, 6, 0, 0)  # noqa: DTZ001
    angles = calculate_clock_hands_angles(naive_dt, timedelta(0))
    assert angles.hour == pytest.approx(6.0)
    assert angles.minute == pytest.approx(0.0)
    assert angles.second == pytest.approx(0.0)


def test_naive_datetime_with_duration() -> None:
    naive_dt = datetime(2025, 4, 27, 0, 0, 0)  # noqa: DTZ001
    duration = timedelta(hours=3, minutes=30)
    angles = calculate_clock_hands_angles(naive_dt, duration)
    assert angles.second == pytest.approx(12600.0)
    assert angles.minute == pytest.approx(210.0)
    assert angles.hour == pytest.approx(3.5)


def test_aware_datetime_no_display_tz_uses_local_conversion() -> None:
    utc_dt = datetime(2025, 4, 27, 12, 0, 0, tzinfo=UTC)
    angles = calculate_clock_hands_angles(utc_dt, timedelta(0), display_tz=None)
    assert math.isfinite(angles.second)
    assert math.isfinite(angles.minute)
    assert math.isfinite(angles.hour)
