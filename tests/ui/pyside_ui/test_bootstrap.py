from unittest.mock import MagicMock, patch

from pytestqt.qtbot import QtBot

from src.ui.pyside_ui.bootstrap import bootstrap


def test_bootstrap_initializes_ui(qtbot: QtBot) -> None:
    with (
        patch("src.ui.pyside_ui.bootstrap.create_application") as mock_create_app,
        patch("src.ui.pyside_ui.bootstrap.QPixmap") as mock_pixmap_cls,
        patch("src.ui.pyside_ui.bootstrap.QSplashScreen") as mock_splash_cls,
        patch("src.ui.pyside_ui.bootstrap.StyleLoader.center_window") as center_window,
        patch("src.ui.pyside_ui.bootstrap.MainWindow") as mock_main_window_cls,
        patch("src.ui.pyside_ui.bootstrap.QTimer.singleShot") as single_shot,
    ):
        app = MagicMock()
        loop = MagicMock()

        mock_create_app.return_value = (app, loop)

        pixmap = MagicMock()
        mock_pixmap_cls.return_value.scaled.return_value = pixmap

        splash = MagicMock()
        mock_splash_cls.return_value = splash

        window = MagicMock()
        mock_main_window_cls.return_value = window

        returned_app, returned_loop, returned_window = bootstrap()

        assert returned_app is app
        assert returned_loop is loop
        assert returned_window is window

        mock_create_app.assert_called_once()

        mock_splash_cls.assert_called_once_with(pixmap)

        center_window.assert_called_once_with(splash)

        splash.show.assert_called_once()

        app.processEvents.assert_called_once()

        mock_main_window_cls.assert_called_once_with(fetch_server_time=False)

        window.show.assert_called_once()

        splash.finish.assert_called_once_with(window)

        single_shot.assert_called_once_with(0, window.fetch_server_time)
