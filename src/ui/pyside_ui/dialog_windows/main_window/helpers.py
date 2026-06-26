import structlog
from PySide6.QtWidgets import QLabel, QLayout, QVBoxLayout

from src.backend.api.models.weather_score_response import BestScoreResponse
from src.ui.pyside_ui.widgets.weather_score_card import WeatherScoreCard

logger = structlog.get_logger(__name__)


def _clear_layout(layout: QLayout) -> None:
    while layout.count():
        item = layout.takeAt(0)
        if item is None:
            continue
        widget = item.widget()
        if widget is not None:
            widget.setParent(None)
            widget.deleteLater()


def _render_weather_score(layout: QVBoxLayout, result: BestScoreResponse) -> None:
    _clear_layout(layout)

    summary = QLabel(
        f"Apparent temperature range: {result.min_threshold:.1f}\u00b0C - {result.max_threshold:.1f}\u00b0C"
        f"   Penalize rain: {result.penalize_rain}   Start day offset: {result.start_day}"
    )
    summary.setWordWrap(True)
    layout.addWidget(summary)

    if not result.results:
        empty_label = QLabel("No matching places found.")
        empty_label.setWordWrap(True)
        layout.addWidget(empty_label)
        layout.addStretch(1)
        return

    sorted_results = sorted(result.results, key=lambda place: place.score, reverse=True)

    max_score = max(place.score for place in sorted_results)
    min_score = min(place.score for place in sorted_results)

    score_range = max_score - min_score

    for place in sorted_results:
        if score_range == 0:
            place.percentage_score = 1.0
        else:
            place.percentage_score = (place.score - min_score) / score_range

    for rank, place in enumerate(sorted_results, start=1):
        layout.addWidget(WeatherScoreCard(place, rank=rank))

    layout.addStretch(1)
