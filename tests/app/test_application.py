from unittest.mock import patch

from PySide6.QtWidgets import QApplication
from pytestqt.qtbot import QtBot

from src.ui.pyside_ui.application import create_application


def test_create_app_wires_everything(qtbot: QtBot) -> None:
    app = QApplication.instance()

    if app is None:
        app = QApplication([])

    with (
        patch("src.app.application.QEventLoop") as mock_event_loop_cls,
        patch("src.app.application.asyncio.set_event_loop") as mock_set_event_loop,
    ):
        loop = mock_event_loop_cls.return_value

        returned_app, returned_loop = create_application()

        assert returned_app is app
        assert returned_loop is loop

        mock_event_loop_cls.assert_called_once_with(app)
        mock_set_event_loop.assert_called_once_with(loop)
