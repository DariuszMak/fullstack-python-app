import pytest
from PySide6.QtCore import QEvent, Qt
from pytestqt.qtbot import QtBot

from src.ui.pyside_ui.dialog_windows.main_window import MainWindow


def test_minimize_hides_window_to_tray(qtbot: QtBot, monkeypatch: pytest.MonkeyPatch) -> None:
    window = MainWindow(fetch_server_time=False)
    qtbot.addWidget(window)
    window.show()

    called = {"notify": False}

    if window._tray is None:

        class DummyTray:
            def notify_hidden(self) -> None:
                called["notify"] = True

        monkeypatch.setattr(window, "_tray", DummyTray())
    else:
        monkeypatch.setattr(window._tray, "notify_hidden", lambda: called.update({"notify": True}))

    window.setWindowState(Qt.WindowState.WindowMinimized)
    event = QEvent(QEvent.Type.WindowStateChange)
    window.changeEvent(event)

    qtbot.wait(20)

    assert window.isVisible() is False
    assert called["notify"] is True
