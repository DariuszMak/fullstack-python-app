import asyncio
from PySide6.QtCore import QObject, Signal

from src.backend.api.models.weather_score_response import BestScoreResponse
from src.frontend.shared.client.httpx_client import HttpxClient
from src.frontend.pyside_ui.dialog_windows.main_window.weather_score_state import WeatherScoreState


class WeatherScoreViewModel(QObject):
    state_changed = Signal(WeatherScoreState)
    loading_changed = Signal(bool)

    def __init__(self, httpx_client: HttpxClient, parent=None):
        super().__init__(parent)
        self._client = httpx_client
        self._state = WeatherScoreState()

    @property
    def state(self) -> WeatherScoreState:
        return self._state

    async def fetch(self, **kwargs) -> None:
        self._state.is_loading = True
        self.state_changed.emit(self._state)
        self.loading_changed.emit(True)
        try:
            response: BestScoreResponse = await self._client.fetch_weather_score(**kwargs)
            self._process_response(response)
            self._state.is_loading = False
            self._state.error = None
        except Exception as e:
            self._state.is_loading = False
            self._state.error = str(e)
        finally:
            self.state_changed.emit(self._state)
            self.loading_changed.emit(False)

    def _process_response(self, response: BestScoreResponse) -> None:
        self._state.min_threshold = response.min_threshold
        self._state.max_threshold = response.max_threshold
        self._state.penalize_rain = response.penalize_rain
        self._state.start_day = response.start_day
        self._state.cards = []
        if not response.results:
            return
        sorted_results = sorted(response.results, key=lambda x: x.score, reverse=True)
        max_score = max(r.score for r in sorted_results)
        min_score = min(r.score for r in sorted_results)
        score_range = max_score - min_score
        for rank, place in enumerate(sorted_results, start=1):
            percentage = 1.0 if score_range == 0 else (place.score - min_score) / score_range
            self._state.cards.append({
                "rank": rank,
                "key": place.key,
                "name": place.name,
                "latitude": place.latitude,
                "longitude": place.longitude,
                "timezone": place.timezone,
                "score": place.score,
                "percentage": percentage,
            })
