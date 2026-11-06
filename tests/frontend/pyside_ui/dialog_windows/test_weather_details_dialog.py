from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING
from unittest.mock import AsyncMock, MagicMock, patch

import numpy as np
import pandas as pd
import pyqtgraph as pg
import pytest
from PySide6.QtCore import QEvent, Qt
from PySide6.QtGui import QCloseEvent
from PySide6.QtWidgets import QApplication, QWidget

from src.backend.api.models.weather_info_response import HourlyRecord, WeatherInfoResponse
from src.backend.api.models.weather_score_response import PlaceBestScoreRecord
from src.frontend.pyside_ui.dialog_windows.weather_details_dialog import WeatherDetailsDialog

if TYPE_CHECKING:
    from pytestqt.qtbot import QtBot

SUPER_CLOSE = "src.frontend.pyside_ui.dialog_windows.draggable_window.draggable_dialog.DraggableDialog.closeEvent"
MODULE = "src.frontend.pyside_ui.dialog_windows.weather_details_dialog"
HALF_HOUR = 1800.0


def make_record(date: str = "2026-01-01T00:00:00+00:00", precipitation: float = 0.0) -> HourlyRecord:
    return HourlyRecord(
        date=date,
        temperature_2m=10.0,
        cloud_cover=50.0,
        precipitation=precipitation,
        apparent_temperature=8.0,
        soil_temperature_6cm=12.0,
        relative_humidity_2m=60.0,
        surface_pressure=1013.0,
        wind_speed_10m=5.0,
        wind_direction_10m=180.0,
        wind_gusts_10m=10.0,
        soil_moisture_0_to_1cm=0.2,
    )


def make_response(*records: HourlyRecord) -> WeatherInfoResponse:
    hourly = list(records) if records else [make_record()]
    return WeatherInfoResponse(hourly=hourly, daily=[], hourly_rows=len(hourly), daily_rows=0)


def make_place(
    score: float = 0.5,
    percentage_score: float = 0.5,
    name: str = "Wroclaw",
) -> PlaceBestScoreRecord:
    return PlaceBestScoreRecord(
        key="wroclaw",
        name=name,
        latitude=51.1,
        longitude=17.0,
        timezone="Europe/Warsaw",
        score=score,
        percentage_score=percentage_score,
    )


def build_dialog(qtbot: QtBot, **kwargs: object) -> WeatherDetailsDialog:
    with (
        patch(f"{MODULE}.StyleLoader.style_window"),
        patch(f"{MODULE}.StyleLoader.center_window"),
    ):
        widget = WeatherDetailsDialog(make_place(), **kwargs)  # type: ignore[arg-type]
    qtbot.addWidget(widget)
    return widget


@pytest.fixture
def dialog(qtbot: QtBot) -> WeatherDetailsDialog:
    with (
        patch(f"{MODULE}.StyleLoader.style_window"),
        patch(f"{MODULE}.StyleLoader.center_window"),
    ):
        widget = WeatherDetailsDialog(
            make_place(score=0.42, percentage_score=0.8), rank=2, forecast_days=3, start_day=1
        )

    qtbot.addWidget(widget)
    return widget


def test_init_without_parent(dialog: WeatherDetailsDialog) -> None:
    assert dialog.windowFlags() & Qt.WindowType.FramelessWindowHint
    assert dialog.testAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)


def test_init_with_parent_calls_style_loader(qtbot: QtBot) -> None:
    parent = QWidget()
    qtbot.addWidget(parent)

    with (
        patch(f"{MODULE}.StyleLoader.style_window") as style_window,
        patch(f"{MODULE}.StyleLoader.center_window") as center_window,
    ):
        widget = WeatherDetailsDialog(make_place(), parent=parent, forecast_days=3, start_day=1)
        qtbot.addWidget(widget)

    style_window.assert_called_once_with(widget)
    center_window.assert_called_once_with(widget, parent)


def test_dialog_stores_place(dialog: WeatherDetailsDialog) -> None:
    assert dialog.place.key == "wroclaw"


def test_dialog_stores_forecast_days_and_start_day(dialog: WeatherDetailsDialog) -> None:
    assert dialog._forecast_days == 3
    assert dialog._start_day == 1


def test_dialog_defaults_forecast_days_and_start_day(qtbot: QtBot) -> None:
    widget = build_dialog(qtbot)

    assert widget._forecast_days == 3
    assert widget._start_day == 0


def test_title_shows_place_name(dialog: WeatherDetailsDialog) -> None:
    assert dialog._title_label.text() == "Wroclaw"


def test_dialog_displays_place_data(dialog: WeatherDetailsDialog) -> None:
    assert dialog.value("name") == "Wroclaw"
    assert dialog.value("key") == "wroclaw"
    assert dialog.value("latitude") == "51.1000"
    assert dialog.value("longitude") == "17.0000"
    assert dialog.value("timezone") == "Europe/Warsaw"


def test_dialog_displays_scores(dialog: WeatherDetailsDialog) -> None:
    assert dialog.value("score") == "0.42"
    assert dialog.value("calculated_score") == "0.80"


def test_dialog_shows_rank(dialog: WeatherDetailsDialog) -> None:
    assert dialog.value("rank") == "#2"


def test_dialog_without_rank_shows_placeholder(qtbot: QtBot) -> None:
    widget = build_dialog(qtbot)

    assert widget.value("rank") == "-"


def test_change_event_language_change_retranslates(
    dialog: WeatherDetailsDialog,
) -> None:
    event = QEvent(QEvent.Type.LanguageChange)

    with patch.object(dialog._ui, "retranslateUi") as retranslate:
        dialog.changeEvent(event)

    retranslate.assert_called_once_with(dialog)


def test_change_event_other_type_does_not_retranslate(
    dialog: WeatherDetailsDialog,
) -> None:
    event = QEvent(QEvent.Type.Resize)

    with patch.object(dialog._ui, "retranslateUi") as retranslate:
        dialog.changeEvent(event)

    retranslate.assert_not_called()


def test_btn_close_click_closes_dialog(dialog: WeatherDetailsDialog) -> None:
    dialog.show()
    assert dialog.isVisible() is True

    dialog._ui.btn_close.click()

    assert dialog.isVisible() is False


def test_close_event_calls_super(dialog: WeatherDetailsDialog) -> None:
    event = QCloseEvent()

    with patch(f"{MODULE}.DraggableDialog.closeEvent") as super_close:
        dialog.closeEvent(event)

    super_close.assert_called_once_with(event)


def test_show_event_triggers_fetch(qtbot: QtBot) -> None:
    with (
        patch(f"{MODULE}.StyleLoader.style_window"),
        patch(f"{MODULE}.StyleLoader.center_window"),
        patch.object(WeatherDetailsDialog, "_fetch_weather_info") as fetch,
    ):
        widget = WeatherDetailsDialog(make_place())
        qtbot.addWidget(widget)
        widget.show()
        QApplication.processEvents()

    fetch.assert_called_once()


def test_fetch_weather_info_creates_task_when_loop_running(qtbot: QtBot) -> None:
    widget = build_dialog(qtbot)

    fake_loop = MagicMock()
    with (
        patch(f"{MODULE}.asyncio.get_running_loop") as get_loop,
        patch.object(WeatherDetailsDialog, "_do_fetch_weather_info", new=MagicMock()),
    ):
        get_loop.return_value = fake_loop
        widget._fetch_weather_info()

    fake_loop.create_task.assert_called_once()


def test_fetch_weather_info_without_running_loop_does_nothing(qtbot: QtBot) -> None:
    widget = build_dialog(qtbot)

    with patch(f"{MODULE}.asyncio.get_running_loop", side_effect=RuntimeError):
        widget._fetch_weather_info()

    assert widget._weather_info_task is None


def test_fetch_weather_info_skips_when_task_pending(qtbot: QtBot) -> None:
    widget = build_dialog(qtbot)
    pending = MagicMock()
    pending.done.return_value = False
    widget._weather_info_task = pending

    with patch(f"{MODULE}.asyncio.get_running_loop") as get_loop:
        widget._fetch_weather_info()

    get_loop.assert_not_called()


def test_do_fetch_passes_forecast_days_and_start_day_to_client(qtbot: QtBot) -> None:
    widget = build_dialog(qtbot, forecast_days=5, start_day=2)
    client = MagicMock()
    client.fetch_weather_info = AsyncMock(return_value=make_response())

    with patch(f"{MODULE}.Config"), patch(f"{MODULE}.HttpxClient", return_value=client):
        asyncio.run(widget._do_fetch_weather_info())

    client.fetch_weather_info.assert_awaited_once_with(
        latitude=51.1,
        longitude=17.0,
        timezone="Europe/Warsaw",
        forecast_days=5,
        start_day=2,
    )


def test_do_fetch_emits_signal_on_success(qtbot: QtBot) -> None:
    widget = build_dialog(qtbot)
    response = make_response()
    client = MagicMock()
    client.fetch_weather_info = AsyncMock(return_value=response)

    with (
        patch(f"{MODULE}.Config"),
        patch(f"{MODULE}.HttpxClient", return_value=client),
        qtbot.waitSignal(widget.weather_info_ready, timeout=1000) as blocker,
    ):
        asyncio.run(widget._do_fetch_weather_info())

    assert blocker.args == [response]


def test_do_fetch_swallows_client_errors(qtbot: QtBot) -> None:
    widget = build_dialog(qtbot)
    client = MagicMock()
    client.fetch_weather_info = AsyncMock(side_effect=RuntimeError("boom"))

    with (
        patch(f"{MODULE}.Config"),
        patch(f"{MODULE}.HttpxClient", return_value=client),
        qtbot.assertNotEmitted(widget.weather_info_ready),
    ):
        asyncio.run(widget._do_fetch_weather_info())


def test_do_fetch_reraises_cancellation(qtbot: QtBot) -> None:
    widget = build_dialog(qtbot)
    client = MagicMock()
    client.fetch_weather_info = AsyncMock(side_effect=asyncio.CancelledError)

    with (
        patch(f"{MODULE}.Config"),
        patch(f"{MODULE}.HttpxClient", return_value=client),
        pytest.raises(asyncio.CancelledError),
    ):
        asyncio.run(widget._do_fetch_weather_info())


def test_update_plot_displays_temperature_curves(qtbot: QtBot) -> None:
    widget = build_dialog(qtbot)

    widget._update_plot(make_response())

    assert widget._plot_widget is not None
    curves = widget._plot_widget.getPlotItem().curves
    assert len(curves) == 2
    x_data, y_data = curves[0].getData()
    assert x_data is not None
    assert x_data.dtype.kind == "f"
    assert list(y_data) == [10.0]


def test_precipitation_is_drawn_as_bars_not_as_curve(qtbot: QtBot) -> None:
    widget = build_dialog(qtbot)

    widget._update_plot(make_response(make_record(precipitation=5.2)))

    assert widget._plot_widget is not None
    assert len(widget._plot_widget.getPlotItem().curves) == 2
    assert isinstance(widget._precipitation_bars, pg.BarGraphItem)
    assert list(widget._precipitation_bars.opts["height"]) == [5.2]


def test_precipitation_bars_live_in_secondary_view(qtbot: QtBot) -> None:
    widget = build_dialog(qtbot)

    widget._update_plot(make_response(make_record(precipitation=2.0)))

    assert widget._precip_view is not None
    assert widget._precipitation_bars in widget._precip_view.addedItems


def test_precipitation_axis_scales_to_data_with_headroom(qtbot: QtBot) -> None:
    widget = build_dialog(qtbot)

    widget._update_plot(make_response(make_record(precipitation=5.0)))

    assert widget._precip_view is not None
    low, high = widget._precip_view.viewRange()[1]
    assert low == pytest.approx(0.0)
    assert high == pytest.approx(6.0)


def test_precipitation_axis_has_minimum_range_when_dry(qtbot: QtBot) -> None:
    widget = build_dialog(qtbot)

    widget._update_plot(make_response(make_record(precipitation=0.0)))

    assert widget._precip_view is not None
    low, high = widget._precip_view.viewRange()[1]
    assert low == pytest.approx(0.0)
    assert high == pytest.approx(1.0)


def test_precipitation_axis_is_independent_of_temperature_axis(qtbot: QtBot) -> None:
    widget = build_dialog(qtbot)

    widget._update_plot(make_response(make_record(precipitation=0.4)))

    assert widget._plot_widget is not None
    assert widget._precip_view is not None
    temp_range = widget._plot_widget.getPlotItem().vb.viewRange()[1]
    precip_range = widget._precip_view.viewRange()[1]
    assert temp_range != precip_range


def test_precipitation_nan_values_become_zero(qtbot: QtBot) -> None:
    widget = build_dialog(qtbot)
    record = make_record(precipitation=1.0).model_copy(update={"precipitation": float("nan")})

    widget._update_plot(make_response(record))

    assert widget._precipitation_bars is not None
    assert list(widget._precipitation_bars.opts["height"]) == [0.0]


def test_update_plot_replaces_previous_bars(qtbot: QtBot) -> None:
    widget = build_dialog(qtbot)

    widget._update_plot(make_response(make_record(precipitation=1.0)))
    widget._update_plot(make_response(make_record(precipitation=3.0)))

    assert widget._precip_view is not None
    assert len(widget._precip_view.addedItems) == 1
    assert list(widget._precipitation_bars.opts["height"]) == [3.0]  # type: ignore[union-attr]
    assert len(widget._plot_widget.getPlotItem().curves) == 2  # type: ignore[union-attr]


def test_update_plot_fits_x_range_to_data(qtbot: QtBot) -> None:
    widget = build_dialog(qtbot)
    stamps = pd.date_range("2026-01-01T00:00:00+00:00", "2026-01-03T00:00:00+00:00", freq="h")
    records = [make_record(ts.isoformat()) for ts in stamps]

    widget._update_plot(make_response(*records))

    assert widget._plot_widget is not None
    x_min, x_max = widget._plot_widget.getPlotItem().vb.viewRange()[0]
    assert x_min == pytest.approx(widget._to_epoch(records[0].date) - HALF_HOUR)
    assert x_max == pytest.approx(widget._to_epoch(records[-1].date) + HALF_HOUR)


def test_update_plot_x_range_follows_new_date_window(qtbot: QtBot) -> None:
    widget = build_dialog(qtbot)
    early = make_record("2026-01-01T00:00:00+00:00")
    later = make_record("2026-02-10T00:00:00+00:00")

    widget._update_plot(make_response(early))
    assert widget._plot_widget is not None
    first_range = widget._plot_widget.getPlotItem().vb.viewRange()[0]

    widget._update_plot(make_response(later))
    second_range = widget._plot_widget.getPlotItem().vb.viewRange()[0]

    assert second_range[0] == pytest.approx(widget._to_epoch(later.date) - HALF_HOUR)
    assert second_range[1] == pytest.approx(widget._to_epoch(later.date) + HALF_HOUR)
    assert first_range != second_range


def test_update_plot_title_shows_date_range(qtbot: QtBot) -> None:
    widget = build_dialog(qtbot)

    widget._update_plot(
        make_response(
            make_record("2026-01-01T00:00:00+00:00"),
            make_record("2026-01-03T00:00:00+00:00"),
        )
    )

    assert widget._plot_widget is not None
    title = widget._plot_widget.getPlotItem().titleLabel.text
    assert "2026-01-01" in title
    assert "2026-01-03" in title


def test_update_plot_title_shows_single_date_when_range_is_one_day(qtbot: QtBot) -> None:
    widget = build_dialog(qtbot)

    widget._update_plot(
        make_response(
            make_record("2026-01-01T09:00:00+00:00"),
            make_record("2026-01-01T10:00:00+00:00"),
        )
    )

    assert widget._plot_widget is not None
    title = widget._plot_widget.getPlotItem().titleLabel.text
    assert "2026-01-01" in title
    assert " to " not in title


def test_update_plot_with_empty_hourly_keeps_plot_untouched(qtbot: QtBot) -> None:
    widget = build_dialog(qtbot)
    response = WeatherInfoResponse(hourly=[], daily=[], hourly_rows=0, daily_rows=0)

    widget._update_plot(response)

    assert widget._plot_widget is not None
    assert len(widget._plot_widget.getPlotItem().curves) == 0
    assert widget._precipitation_bars is None


def test_bar_step_defaults_to_one_hour_for_single_point() -> None:
    assert WeatherDetailsDialog._bar_step(np.array([100.0])) == 3600.0


def test_bar_step_uses_median_spacing() -> None:
    assert WeatherDetailsDialog._bar_step(np.array([0.0, 7200.0, 14400.0])) == 7200.0


def test_bar_step_falls_back_when_spacing_is_zero() -> None:
    assert WeatherDetailsDialog._bar_step(np.array([5.0, 5.0, 5.0])) == 3600.0


def test_sync_precipitation_view_is_noop_without_plot(dialog: WeatherDetailsDialog) -> None:
    dialog._plot_widget = None

    dialog._sync_precipitation_view()


def test_close_event_cancels_pending_fetch(dialog: WeatherDetailsDialog) -> None:
    task = MagicMock()
    task.done.return_value = False
    dialog._weather_info_task = task

    with patch(SUPER_CLOSE):
        dialog.closeEvent(QCloseEvent())

    task.cancel.assert_called_once()


def test_close_event_does_not_cancel_finished_fetch(dialog: WeatherDetailsDialog) -> None:
    task = MagicMock()
    task.done.return_value = True
    dialog._weather_info_task = task

    with patch(SUPER_CLOSE):
        dialog.closeEvent(QCloseEvent())

    task.cancel.assert_not_called()


def test_close_event_releases_plot_widget(dialog: WeatherDetailsDialog) -> None:
    plot = dialog._plot_widget
    assert plot is not None

    with patch.object(plot, "deleteLater") as delete_later, patch(SUPER_CLOSE):
        dialog.closeEvent(QCloseEvent())

    delete_later.assert_called_once()
    assert dialog._plot_widget is None


def test_close_event_releases_precipitation_references(dialog: WeatherDetailsDialog) -> None:
    dialog._update_plot(make_response(make_record(precipitation=1.0)))
    assert dialog._precip_view is not None
    assert dialog._precipitation_bars is not None

    with patch(SUPER_CLOSE):
        dialog.closeEvent(QCloseEvent())

    assert dialog._precip_view is None
    assert dialog._precipitation_bars is None


def test_update_plot_ignored_after_plot_released(dialog: WeatherDetailsDialog) -> None:
    dialog._plot_widget = None

    dialog._update_plot(make_response())

    assert dialog._plot_widget is None


def test_weather_info_ready_signal_updates_plot(dialog: WeatherDetailsDialog) -> None:
    dialog.weather_info_ready.emit(make_response())
    QApplication.processEvents()

    assert dialog._plot_widget is not None
    assert len(dialog._plot_widget.getPlotItem().curves) == 2
    assert dialog._precipitation_bars is not None


def test_plot_context_menus_are_disabled(dialog: WeatherDetailsDialog) -> None:
    assert dialog._plot_widget is not None
    plot_item = dialog._plot_widget.getPlotItem()

    assert plot_item.vb.menuEnabled() is False
    assert plot_item.vb.menu is None or plot_item.vb.menuEnabled() is False


def test_plot_scene_has_no_export_action(dialog: WeatherDetailsDialog) -> None:
    assert dialog._plot_widget is not None
    scene = dialog._plot_widget.scene()

    assert scene is not None
    assert list(scene.contextMenu) == []


def test_close_event_closes_existing_export_dialog(dialog: WeatherDetailsDialog) -> None:
    assert dialog._plot_widget is not None
    scene = dialog._plot_widget.scene()
    export_dialog = QWidget()
    export_dialog.show()
    scene.exportDialog = export_dialog
    assert export_dialog.isVisible() is True

    with patch(SUPER_CLOSE):
        dialog.closeEvent(QCloseEvent())

    assert export_dialog.isVisible() is False
    assert scene.exportDialog is None


def test_close_event_without_export_dialog_does_not_fail(dialog: WeatherDetailsDialog) -> None:
    assert dialog._plot_widget is not None
    assert getattr(dialog._plot_widget.scene(), "exportDialog", None) is None

    with patch(SUPER_CLOSE):
        dialog.closeEvent(QCloseEvent())

    assert dialog._plot_widget is None


def test_release_plot_is_idempotent(dialog: WeatherDetailsDialog) -> None:
    with patch(SUPER_CLOSE):
        dialog.closeEvent(QCloseEvent())
        dialog.closeEvent(QCloseEvent())

    assert dialog._plot_widget is None
