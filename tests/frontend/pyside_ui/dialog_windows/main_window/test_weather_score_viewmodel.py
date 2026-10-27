from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest

from src.backend.api.models.weather_score_response import BestScoreResponse, PlaceBestScoreRecord
from src.frontend.pyside_ui.dialog_windows.main_window.weather_score_state import WeatherScoreState
from src.frontend.pyside_ui.dialog_windows.main_window.weather_score_viewmodel import WeatherScoreViewModel

FETCH_KWARGS: dict[str, object] = {
    "apparent_temperature_min_threshold": 18.0,
    "apparent_temperature_max_threshold": 25.0,
    "penalize_rain": True,
    "forecast_days": 3,
    "start_day": 0,
}


def make_place(key: str, score: float) -> PlaceBestScoreRecord:
    return PlaceBestScoreRecord(
        key=key,
        name=key.title(),
        latitude=51.1,
        longitude=17.0,
        timezone="Europe/Warsaw",
        score=score,
    )


def make_response(
    scores: dict[str, float] | None = None,
    *,
    min_threshold: float = 20.0,
    max_threshold: float = 25.0,
    penalize_rain: bool = True,
    start_day: int = 0,
) -> BestScoreResponse:
    values = scores if scores is not None else {"wroclaw": 0.5, "krakow": 0.8}
    return BestScoreResponse(
        results=[make_place(key, score) for key, score in values.items()],
        min_threshold=min_threshold,
        max_threshold=max_threshold,
        penalize_rain=penalize_rain,
        start_day=start_day,
    )


def make_viewmodel(
    *,
    response: BestScoreResponse | None = None,
    error: Exception | None = None,
) -> tuple[WeatherScoreViewModel, MagicMock]:
    client = MagicMock()
    if error is not None:
        client.fetch_weather_score = AsyncMock(side_effect=error)
    else:
        client.fetch_weather_score = AsyncMock(return_value=response if response is not None else make_response())
    return WeatherScoreViewModel(client), client


def record_states(viewmodel: WeatherScoreViewModel) -> list[WeatherScoreState]:
    states: list[WeatherScoreState] = []
    viewmodel.state_changed.connect(states.append)
    return states


def record_loading(viewmodel: WeatherScoreViewModel) -> list[bool]:
    values: list[bool] = []
    viewmodel.loading_changed.connect(values.append)
    return values


def test_initial_state_is_default() -> None:
    viewmodel, _ = make_viewmodel()

    assert viewmodel.state == WeatherScoreState()


@pytest.mark.asyncio
async def test_fetch_passes_arguments_to_client() -> None:
    viewmodel, client = make_viewmodel()

    await viewmodel.fetch(
        apparent_temperature_min_threshold=10.0,
        apparent_temperature_max_threshold=18.0,
        penalize_rain=False,
        forecast_days=7,
        start_day=2,
    )

    client.fetch_weather_score.assert_called_once_with(
        apparent_temperature_min_threshold=10.0,
        apparent_temperature_max_threshold=18.0,
        penalize_rain=False,
        forecast_days=7,
        start_day=2,
    )


@pytest.mark.asyncio
async def test_fetch_emits_loading_state_then_result_state() -> None:
    viewmodel, _ = make_viewmodel()
    states = record_states(viewmodel)

    await viewmodel.fetch(**FETCH_KWARGS)  # type: ignore[arg-type]

    assert len(states) == 2
    assert states[0].is_loading is True
    assert states[0].error is None
    assert states[1].is_loading is False
    assert len(states[1].cards) == 2


@pytest.mark.asyncio
async def test_fetch_emits_loading_changed_true_then_false_on_success() -> None:
    viewmodel, _ = make_viewmodel()
    loading = record_loading(viewmodel)

    await viewmodel.fetch(**FETCH_KWARGS)  # type: ignore[arg-type]

    assert loading == [True, False]


@pytest.mark.asyncio
async def test_fetch_updates_state_property() -> None:
    viewmodel, _ = make_viewmodel()

    await viewmodel.fetch(**FETCH_KWARGS)  # type: ignore[arg-type]

    assert viewmodel.state.is_loading is False
    assert len(viewmodel.state.cards) == 2


@pytest.mark.asyncio
async def test_fetch_sorts_cards_by_score_descending_and_assigns_ranks() -> None:
    viewmodel, _ = make_viewmodel(response=make_response({"a": 0.2, "b": 0.9, "c": 0.5}))

    await viewmodel.fetch(**FETCH_KWARGS)  # type: ignore[arg-type]

    cards = viewmodel.state.cards
    assert [card.place.key for card in cards] == ["b", "c", "a"]
    assert [card.rank for card in cards] == [1, 2, 3]


@pytest.mark.asyncio
async def test_fetch_computes_relative_percentage_scores() -> None:
    viewmodel, _ = make_viewmodel(response=make_response({"a": 0.2, "b": 0.8, "c": 0.5}))

    await viewmodel.fetch(**FETCH_KWARGS)  # type: ignore[arg-type]

    percentages = [card.place.percentage_score for card in viewmodel.state.cards]
    assert percentages == pytest.approx([1.0, 0.5, 0.0])


@pytest.mark.asyncio
async def test_fetch_single_result_has_full_percentage() -> None:
    viewmodel, _ = make_viewmodel(response=make_response({"a": 0.4}))

    await viewmodel.fetch(**FETCH_KWARGS)  # type: ignore[arg-type]

    assert len(viewmodel.state.cards) == 1
    assert viewmodel.state.cards[0].place.percentage_score == pytest.approx(1.0)


@pytest.mark.asyncio
async def test_fetch_equal_scores_have_full_percentage() -> None:
    viewmodel, _ = make_viewmodel(response=make_response({"a": 0.4, "b": 0.4}))

    await viewmodel.fetch(**FETCH_KWARGS)  # type: ignore[arg-type]

    percentages = [card.place.percentage_score for card in viewmodel.state.cards]
    assert percentages == pytest.approx([1.0, 1.0])


@pytest.mark.asyncio
async def test_fetch_preserves_place_fields() -> None:
    viewmodel, _ = make_viewmodel(response=make_response({"krakow": 0.7}))

    await viewmodel.fetch(**FETCH_KWARGS)  # type: ignore[arg-type]

    place = viewmodel.state.cards[0].place
    assert place.key == "krakow"
    assert place.name == "Krakow"
    assert place.latitude == pytest.approx(51.1)
    assert place.longitude == pytest.approx(17.0)
    assert place.timezone == "Europe/Warsaw"
    assert place.score == pytest.approx(0.7)


@pytest.mark.asyncio
async def test_fetch_with_no_results_yields_no_cards() -> None:
    viewmodel, _ = make_viewmodel(response=make_response({}))

    await viewmodel.fetch(**FETCH_KWARGS)  # type: ignore[arg-type]

    assert viewmodel.state.cards == ()
    assert viewmodel.state.error is None
    assert viewmodel.state.is_loading is False


@pytest.mark.asyncio
async def test_fetch_propagates_response_metadata_to_state() -> None:
    response = make_response(min_threshold=11.0, max_threshold=22.0, penalize_rain=False, start_day=4)
    viewmodel, _ = make_viewmodel(response=response)

    await viewmodel.fetch(**FETCH_KWARGS)  # type: ignore[arg-type]

    assert viewmodel.state.min_threshold == pytest.approx(11.0)
    assert viewmodel.state.max_threshold == pytest.approx(22.0)
    assert viewmodel.state.penalize_rain is False
    assert viewmodel.state.start_day == 4


@pytest.mark.asyncio
async def test_fetch_failure_sets_error_state() -> None:
    viewmodel, _ = make_viewmodel(error=RuntimeError("test_message"))

    await viewmodel.fetch(**FETCH_KWARGS)  # type: ignore[arg-type]

    assert viewmodel.state.error == "test_message"
    assert viewmodel.state.cards == ()
    assert viewmodel.state.is_loading is False


@pytest.mark.asyncio
async def test_fetch_failure_uses_exception_type_when_message_is_empty() -> None:
    viewmodel, _ = make_viewmodel(error=TimeoutError())

    await viewmodel.fetch(**FETCH_KWARGS)  # type: ignore[arg-type]

    assert viewmodel.state.error == "TimeoutError"


@pytest.mark.asyncio
async def test_fetch_failure_does_not_raise() -> None:
    viewmodel, _ = make_viewmodel(error=RuntimeError("boom"))

    await viewmodel.fetch(**FETCH_KWARGS)  # type: ignore[arg-type]


@pytest.mark.asyncio
async def test_fetch_failure_emits_loading_changed_true_then_false() -> None:
    viewmodel, _ = make_viewmodel(error=RuntimeError("boom"))
    loading = record_loading(viewmodel)

    await viewmodel.fetch(**FETCH_KWARGS)  # type: ignore[arg-type]

    assert loading == [True, False]


@pytest.mark.asyncio
async def test_fetch_failure_emits_loading_state_then_error_state() -> None:
    viewmodel, _ = make_viewmodel(error=RuntimeError("boom"))
    states = record_states(viewmodel)

    await viewmodel.fetch(**FETCH_KWARGS)  # type: ignore[arg-type]

    assert states[0].is_loading is True
    assert states[-1].is_loading is False
    assert states[-1].error == "boom"


@pytest.mark.asyncio
async def test_fetch_failure_clears_previous_cards() -> None:
    viewmodel, client = make_viewmodel()
    await viewmodel.fetch(**FETCH_KWARGS)  # type: ignore[arg-type]
    assert len(viewmodel.state.cards) == 2

    client.fetch_weather_score = AsyncMock(side_effect=RuntimeError("boom"))
    await viewmodel.fetch(**FETCH_KWARGS)  # type: ignore[arg-type]

    assert not viewmodel.state.cards
    assert viewmodel.state.error == "boom"


@pytest.mark.asyncio
async def test_fetch_success_clears_previous_error() -> None:
    viewmodel, client = make_viewmodel(error=RuntimeError("boom"))
    await viewmodel.fetch(**FETCH_KWARGS)  # type: ignore[arg-type]
    assert viewmodel.state.error == "boom"

    client.fetch_weather_score = AsyncMock(return_value=make_response())
    await viewmodel.fetch(**FETCH_KWARGS)  # type: ignore[arg-type]

    assert viewmodel.state.error is None
    assert len(viewmodel.state.cards) == 2


@pytest.mark.asyncio
async def test_fetch_sets_loading_state_before_calling_client() -> None:
    client = MagicMock()
    observed: list[bool] = []
    viewmodel = WeatherScoreViewModel(client)

    async def fetch_side_effect(**kwargs: object) -> BestScoreResponse:
        observed.append(viewmodel.state.is_loading)
        return make_response()

    client.fetch_weather_score = AsyncMock(side_effect=fetch_side_effect)

    await viewmodel.fetch(**FETCH_KWARGS)  # type: ignore[arg-type]

    assert observed == [True]


def test_build_state_returns_state_without_loading_or_error() -> None:
    state = WeatherScoreViewModel._build_state(make_response())

    assert state.is_loading is False
    assert state.error is None
    assert len(state.cards) == 2


def test_build_state_with_empty_results() -> None:
    state = WeatherScoreViewModel._build_state(make_response({}))

    assert state.cards == ()


def test_build_state_does_not_mutate_response() -> None:
    response = make_response({"a": 0.2, "b": 0.9})

    WeatherScoreViewModel._build_state(response)

    assert [place.key for place in response.results] == ["a", "b"]
