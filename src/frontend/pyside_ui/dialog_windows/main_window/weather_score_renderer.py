from PySide6.QtWidgets import QVBoxLayout, QLabel
from src.backend.api.models.weather_score_response import PlaceBestScoreRecord
from src.frontend.pyside_ui.dialog_windows.main_window.weather_score_state import WeatherScoreState
from src.frontend.pyside_ui.widgets.weather_score_card import WeatherScoreCard


class WeatherScoreRenderer:
    def __init__(self, layout: QVBoxLayout):
        self._layout = layout
        self._cards = []

    def render(self, state: WeatherScoreState):
        for card in self._cards:
            card.setParent(None)
            card.deleteLater()
        self._cards.clear()

        if state.is_loading:
            self._show_info("Fetching weather score...")
            return

        if state.error:
            self._show_error(f"Failed to fetch weather score: {state.error}")
            return

        if not state.cards:
            self._show_info("No matching places found.")
            return

        for card_data in state.cards:
            place = PlaceBestScoreRecord(
                key=card_data["key"],
                name=card_data["name"],
                latitude=card_data["latitude"],
                longitude=card_data["longitude"],
                timezone=card_data["timezone"],
                score=card_data["score"],
                percentage_score=card_data["percentage"],
            )
            card = WeatherScoreCard(place=place, rank=card_data["rank"])
            self._layout.addWidget(card)
            self._cards.append(card)

        self._layout.addStretch(1)

    def _show_info(self, message: str):
        for card in self._cards:
            card.setParent(None)
            card.deleteLater()
        self._cards.clear()
        label = QLabel(message)
        label.setWordWrap(True)
        label.setStyleSheet("color: rgb(85, 170, 255);")
        self._layout.addWidget(label)
        self._layout.addStretch(1)

    def _show_error(self, message: str):
        for card in self._cards:
            card.setParent(None)
            card.deleteLater()
        self._cards.clear()
        label = QLabel(message)
        label.setWordWrap(True)
        label.setStyleSheet("color: rgb(231, 76, 60);")
        self._layout.addWidget(label)
        self._layout.addStretch(1)
