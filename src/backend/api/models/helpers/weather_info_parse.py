import math

import structlog
from fastapi import APIRouter

logger = structlog.get_logger(__name__)
router = APIRouter()


def _sanitize_float(value: float) -> float:
    if math.isnan(value) or math.isinf(value):
        return 0.0
    return float(value)
