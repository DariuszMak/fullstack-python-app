from __future__ import annotations

import pandas as pd

from src.backend.api.models.best_score_response import BestScoreQueryParams, PlaceBestScoreRecord
from src.backend.openmeteo.gather import gather_data
from src.backend.openmeteo.places.places import PLACES
from src.backend.openmeteo.request_builder import build_request_parameters


def _day_weight(day_index: int, total_days: int) -> float:
    return 1.0 - (day_index / total_days)


def _score_place(
    daily_df: pd.DataFrame,
    threshold: float,
    penalize_rain: bool,
) -> float:
    total_days = len(daily_df)
    score = 0.0

    for idx, row in daily_df.iterrows():
        apparent_max = float(row["apparent_temperature_max"])
        rain = float(row["rain_sum"])

        if apparent_max <= threshold:
            continue

        day_score = (apparent_max - threshold) * _day_weight(int(idx), total_days)

        if penalize_rain and rain > 0.0:
            day_score = 0.0

        score += day_score

    return score


def calculate_best_scores(params: BestScoreQueryParams) -> list[PlaceBestScoreRecord]:
    records: list[PlaceBestScoreRecord] = []

    for key, place in PLACES.items():
        parameters = build_request_parameters(
            latitude=place.latitude,
            longitude=place.longitude,
            timezone=place.timezone,
            forecast_days=params.forecast_days,
        )
        _, daily_df = gather_data(parameters)
        daily_df = daily_df.reset_index(drop=True)

        score = _score_place(daily_df, params.apparent_temperature_threshold, params.penalize_rain)

        records.append(
            PlaceBestScoreRecord(
                key=key,
                name=place.name,
                latitude=place.latitude,
                longitude=place.longitude,
                timezone=place.timezone,
                score=round(score, 4),
            )
        )

    records.sort(key=lambda r: r.score, reverse=True)
    return records
