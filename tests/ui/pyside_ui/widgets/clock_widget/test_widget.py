import time
from datetime import UTC, datetime, timedelta

from PySide6.QtWidgets import QApplication

from src.ui.pyside_ui.widgets.clock_widget.view.clock_widget import ClockWidget


def test_clock_widget_runs() -> None:
    app = QApplication.instance() or QApplication([])

    widget = ClockWidget()
    widget.show()

    before = (
        widget._controller._clock_hands.second,
        widget._controller._clock_hands.minute,
        widget._controller._clock_hands.hour,
    )

    end_time = time.time() + 0.1
    while time.time() < end_time:
        app.processEvents()

    after = (
        widget._controller._clock_hands.second,
        widget._controller._clock_hands.minute,
        widget._controller._clock_hands.hour,
    )

    assert before != after

    widget._timer.stop()
    widget.hide()
    widget.deleteLater()
    app.processEvents()


def test_clock_widget_no_drift_accumulation() -> None:
    QApplication.instance() or QApplication([])
    widget = ClockWidget()

    server_time = datetime(2025, 1, 1, 12, 0, 0, tzinfo=UTC)
    widget.set_current_datetime(server_time)

    simulated_elapsed = 5.0
    widget._wall_anchor_mono -= simulated_elapsed

    actual = widget._server_anchor + timedelta(seconds=time.monotonic() - widget._wall_anchor_mono)
    expected = server_time + timedelta(seconds=simulated_elapsed)

    assert abs((actual - expected).total_seconds()) < 0.05


def test_clock_widget_current_datetime_reflects_anchors() -> None:
    QApplication.instance() or QApplication([])
    widget = ClockWidget()

    t1 = datetime(2025, 6, 15, 9, 30, 0, tzinfo=UTC)
    widget.set_current_datetime(t1)
    widget._wall_anchor_mono -= 10.0

    actual = widget._server_anchor + timedelta(seconds=time.monotonic() - widget._wall_anchor_mono)
    assert abs((actual - t1).total_seconds() - 10.0) < 0.05

    t2 = datetime(2025, 6, 15, 9, 30, 45, tzinfo=UTC)
    widget.set_current_datetime(t2)

    actual2 = widget._server_anchor + timedelta(seconds=time.monotonic() - widget._wall_anchor_mono)
    assert abs((actual2 - t2).total_seconds()) < 0.05
