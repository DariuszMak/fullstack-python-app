from PySide6.QtWidgets import QLabel, QLayoutItem, QVBoxLayout, QWidget

from src.frontend.pyside_ui.dialog_windows.main_window.weather_score_state import (
    WeatherScoreCardData,
    WeatherScoreState,
)
from src.frontend.pyside_ui.widgets.weather_score_card import WeatherScoreCard

INFO_STYLE: str = "color: rgb(85, 170, 255);"
ERROR_STYLE: str = "color: rgb(231, 76, 60);"


class WeatherScoreRenderer:
    def __init__(self, layout: QVBoxLayout) -> None:
        self._layout: QVBoxLayout = layout
        self._container = layout.parentWidget()

    def render(self, state: WeatherScoreState) -> None:
        self._clear()

        if state.is_loading:
            self._show_message("Fetching weather score...", INFO_STYLE)
            return

        if state.error is not None:
            self._show_message(f"Failed to fetch weather score: {state.error}", ERROR_STYLE)
            return

        if not state.cards:
            self._show_message("No matching places found.", INFO_STYLE)
            return

        card_data: WeatherScoreCardData
        for card_data in state.cards:
            card: WeatherScoreCard = WeatherScoreCard(place=card_data.place, rank=card_data.rank)
            self._layout.addWidget(card)

        self._layout.addStretch(1)

    def _clear(self) -> None:
        item: QLayoutItem | None = self._layout.takeAt(0)
        while item is not None:
            widget: QWidget | None = item.widget()
            if widget is not None:
                widget.setParent(None)
                widget.deleteLater()
            item = self._layout.takeAt(0)

    def _show_message(self, message: str, style: str) -> None:
        label: QLabel = QLabel(message)
        label.setWordWrap(True)
        label.setStyleSheet(style)
        self._layout.addWidget(label)
        self._layout.addStretch(1)
