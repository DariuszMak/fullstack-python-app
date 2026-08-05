from unittest.mock import patch

import pytest
from PySide6.QtCore import QEvent, Qt
from PySide6.QtGui import QCloseEvent
from PySide6.QtWidgets import QWidget
from pytestqt.qtbot import QtBot

from src.ui.pyside_ui.dialog_windows.settings_dialog import SettingsDialog


@pytest.fixture
def dialog(qtbot: QtBot) -> SettingsDialog:
    with (
        patch("src.ui.pyside_ui.dialog_windows.settings_dialog.StyleLoader.style_window"),
        patch("src.ui.pyside_ui.dialog_windows.settings_dialog.StyleLoader.center_window"),
    ):
        widget = SettingsDialog()
    qtbot.addWidget(widget)
    return widget


def test_init_without_parent(dialog) -> None:
    assert dialog._ui is not None
    assert dialog.windowFlags() & Qt.WindowType.FramelessWindowHint
    assert dialog.testAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)


def test_init_with_parent_calls_style_loader(qtbot) -> None:
    parent = QWidget()
    qtbot.addWidget(parent)

    with (
        patch("src.ui.pyside_ui.dialog_windows.settings_dialog.StyleLoader.style_window") as style_window,
        patch("src.ui.pyside_ui.dialog_windows.settings_dialog.StyleLoader.center_window") as center_window,
    ):
        widget = SettingsDialog(parent)
        qtbot.addWidget(widget)

    style_window.assert_called_once_with(widget)
    center_window.assert_called_once_with(widget, parent)


def test_btn_close_click_closes_dialog(dialog, qtbot) -> None:
    dialog.show()
    assert dialog.isVisible() is True
    dialog._ui.btn_close.click()
    assert dialog.isVisible() is False


def test_change_event_language_change_retranslates(dialog) -> None:
    event = QEvent(QEvent.Type.LanguageChange)
    with patch.object(dialog._ui, "retranslateUi") as retranslate:
        dialog.changeEvent(event)
    retranslate.assert_called_once_with(dialog)


def test_change_event_other_type_does_not_retranslate(dialog) -> None:
    event = QEvent(QEvent.Type.Resize)
    with patch.object(dialog._ui, "retranslateUi") as retranslate:
        dialog.changeEvent(event)
    retranslate.assert_not_called()


def test_close_event_calls_super(dialog) -> None:
    event = QCloseEvent()
    with patch("src.ui.pyside_ui.dialog_windows.settings_dialog.DraggableDialog.closeEvent") as super_close:
        dialog.closeEvent(event)
    super_close.assert_called_once_with(event)
