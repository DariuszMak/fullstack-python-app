from dataclasses import replace

from PySide6.QtCore import QObject, Signal

from src.backend.api.models.weather_score_response import BestScoreResponse, PlaceBestScoreRecord
from src.frontend.pyside_ui.dialog_windows.main_window.weather_score_state import (
    WeatherScoreCardData,
    WeatherScoreState,
)
from src.frontend.shared.client.httpx_client import HttpxClient


class WeatherScoreViewModel(QObject):
    state_changed = Signal(object)
    loading_changed = Signal(bool)

    def __init__(self, httpx_client: HttpxClient, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._client: HttpxClient = httpx_client
        self._state: WeatherScoreState = WeatherScoreState()

    @property
    def state(self) -> WeatherScoreState:
        return self._state

    def _set_state(self, state: WeatherScoreState) -> None:
        self._state = state
        self.state_changed.emit(state)

    async def fetch(
        self,
        *,
        apparent_temperature_min_threshold: float,
        apparent_temperature_max_threshold: float,
        penalize_rain: bool,
        forecast_days: int,
        start_day: int,
    ) -> None:
        self._set_state(replace(self._state, is_loading=True, error=None))
        self.loading_changed.emit(True)
        try:
            response: BestScoreResponse = await self._client.fetch_weather_score(
                apparent_temperature_min_threshold=apparent_temperature_min_threshold,
                apparent_temperature_max_threshold=apparent_temperature_max_threshold,
                penalize_rain=penalize_rain,
                forecast_days=forecast_days,
                start_day=start_day,
            )
            self._set_state(self._build_state(response))
        except Exception as exc:
            message: str = str(exc) or type(exc).__name__
            self._set_state(replace(self._state, is_loading=False, cards=(), error=message))
        finally:
            if self._state.is_loading:
                self._set_state(replace(self._state, is_loading=False))
            self.loading_changed.emit(False)

    @staticmethod
    def _build_state(response: BestScoreResponse) -> WeatherScoreState:
        sorted_results: list[PlaceBestScoreRecord] = sorted(response.results, key=lambda r: r.score, reverse=True)
        cards: tuple[WeatherScoreCardData, ...] = ()
        if sorted_results:
            max_score: float = max(r.score for r in sorted_results)
            min_score: float = min(r.score for r in sorted_results)
            score_range: float = max_score - min_score
            built: list[WeatherScoreCardData] = []
            for rank, place in enumerate(sorted_results, start=1):
                percentage: float = 1.0 if score_range == 0 else (place.score - min_score) / score_range
                built.append(
                    WeatherScoreCardData(
                        rank=rank,
                        place=PlaceBestScoreRecord(
                            key=place.key,
                            name=place.name,
                            latitude=place.latitude,
                            longitude=place.longitude,
                            timezone=place.timezone,
                            score=place.score,
                            percentage_score=percentage,
                        ),
                    )
                )
            cards = tuple(built)
        return WeatherScoreState(
            is_loading=False,
            cards=cards,
            error=None,
            min_threshold=response.min_threshold,
            max_threshold=response.max_threshold,
            penalize_rain=response.penalize_rain,
            start_day=response.start_day,
        )
