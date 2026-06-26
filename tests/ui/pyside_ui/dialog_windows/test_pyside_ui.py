from _pytest.monkeypatch import MonkeyPatch
from PySide6.QtCore import Qt
from pytestqt.qtbot import QtBot

from src.ui.pyside_ui.dialog_windows.main_window import MainWindow


def test_pressing_q_triggers_close(qtbot: QtBot, monkeypatch: MonkeyPatch) -> None:
    window = MainWindow()
    qtbot.addWidget(window)
    window.show()

    called = {"close": False}

    def fake_close() -> None:
        called["close"] = True

    monkeypatch.setattr(window, "close", fake_close)

    qtbot.keyPress(window, Qt.Key.Key_Q)  # type: ignore[no-untyped-call]

    assert called["close"] is True
