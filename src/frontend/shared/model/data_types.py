from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from PySide6.QtCore import QPointF


@dataclass
class ClockHands:
    second: float
    minute: float
    hour: float


@dataclass
class HandsPosition:
    second: QPointF
    minute: QPointF
    hour: QPointF
