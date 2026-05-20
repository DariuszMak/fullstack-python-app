from __future__ import annotations

import math
from datetime import datetime, time, timedelta, timezone

from PySide6.QtCore import QPointF

from src.ui.shared.model.data_types import ClockHands, HandsPosition


def polar_to_cartesian(center: QPointF, length: float, angle_radians: float) -> QPointF:
    x = center.x() + math.sin(angle_radians) * length
    y = center.y() - math.cos(angle_radians) * length
    return QPointF(x, y)

def clock_hands_in_radians(hands: ClockHands) -> tuple[float, float, float]:
    second_angle = (hands.second / 60.0) * 2.0 * math.pi
    minute_angle = (hands.minute / 60.0) * 2.0 * math.pi
    hour_angle = (hands.hour / 12.0) * 2.0 * math.pi
    return second_angle, minute_angle, hour_angle

def convert_clock_pid_to_cartesian(clock_hands: ClockHands, center: QPointF, radius: float) -> HandsPosition:
    second_polar, minute_polar, hour_polar = clock_hands_in_radians(clock_hands)

    second_hand_cartesian = polar_to_cartesian(center, radius * 0.9, second_polar)
    minute_hand_cartesian = polar_to_cartesian(center, radius * 0.7, minute_polar)
    hour_hand_cartesian = polar_to_cartesian(center, radius * 0.5, hour_polar)

    return HandsPosition(second_hand_cartesian, minute_hand_cartesian, hour_hand_cartesian)


def calculate_clock_hands_angles(
    start_dt: datetime,
    duration: timedelta,
    display_tz: timezone | None = None,
) -> ClockHands:
    if start_dt.tzinfo is None:
        local_dt = start_dt
    elif display_tz is not None:
        local_dt = start_dt.astimezone(display_tz)
    else:
        local_dt = start_dt.astimezone()

    midnight = datetime.combine(local_dt.date(), time(0, 0, 0), tzinfo=local_dt.tzinfo)
    start_ms = int((local_dt - midnight).total_seconds() * 1000)
    elapsed_ms = int(duration.total_seconds() * 1000)

    start_s = start_ms / 1000.0
    elapsed_s = elapsed_ms / 1000.0

    seconds_angle = start_s % 60.0 + elapsed_s
    minutes_angle = (start_s / 60.0) % 60.0 + elapsed_s / 60.0
    hours_angle = (start_s / 3600.0) % 12.0 + elapsed_s / 3600.0

    return ClockHands(second=float(seconds_angle), minute=float(minutes_angle), hour=float(hours_angle))


def format_datetime(datetime: datetime) -> str:
    formatted = f"{datetime.hour:02}:{datetime.minute:02}:{datetime.second:02}."
    formatted += f"{int(datetime.microsecond / 1000):03}"
    return formatted



