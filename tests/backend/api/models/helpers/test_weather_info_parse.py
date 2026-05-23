import pytest

from src.backend.api.models.helpers.weather_info_parse import _sanitize_float


def test_sanitize_float_passes_normal_values() -> None:
    assert _sanitize_float(3.14) == pytest.approx(3.14)
    assert _sanitize_float(0.0) == pytest.approx(0.0)
    assert _sanitize_float(-273.15) == pytest.approx(-273.15)


def test_sanitize_float_replaces_nan() -> None:
    assert _sanitize_float(float("nan")) == pytest.approx(0.0)


def test_sanitize_float_replaces_inf() -> None:
    assert _sanitize_float(float("inf")) == pytest.approx(0.0)
    assert _sanitize_float(float("-inf")) == pytest.approx(0.0)
