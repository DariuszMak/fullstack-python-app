from typing import Final

MIN_TEMP_SLIDER_RANGE: Final[tuple[int, int]] = (-20, 40)
MAX_TEMP_SLIDER_RANGE: Final[tuple[int, int]] = (-20, 40)
DEFAULT_MIN_TEMP: Final[int] = 18
DEFAULT_MAX_TEMP: Final[int] = 25
DEFAULT_PENALIZE_RAIN: Final[bool] = True
FORECAST_DAYS_SLIDER_RANGE: Final[tuple[int, int]] = (1, 16)
START_DAY_SLIDER_RANGE: Final[tuple[int, int]] = (1, 16)
DEFAULT_FORECAST_DAYS: Final[int] = 3
DEFAULT_START_DAY: Final[int] = 1

HOUR_SECONDS: Final[float] = 3600.0
DAY_SECONDS: Final[float] = 86400.0
LONG_SPAN_DAYS: Final[float] = 3.0
MIN_DAY_LABEL_PIXELS: Final[float] = 60.0
DAY_LABEL_FORMAT: Final[str] = "%d %b"
BAR_WIDTH_RATIO: Final[float] = 0.8
PRECIPITATION_COLOR: Final[tuple[int, int, int]] = (46, 204, 113)
PRECIPITATION_BAR_ALPHA: Final[int] = 170
PRECIPITATION_HEADROOM: Final[float] = 1.2
MIN_PRECIPITATION_AXIS_MAX: Final[float] = 1.0

INFO_STYLE: Final[str] = "color: rgb(85, 170, 255);"
ERROR_STYLE: Final[str] = "color: rgb(231, 76, 60);"
