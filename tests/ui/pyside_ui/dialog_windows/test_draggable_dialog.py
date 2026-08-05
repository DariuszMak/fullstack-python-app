from unittest.mock import patch

import pytest
from PySide6.QtCore import QPointF, Qt
from PySide6.QtGui import QMouseEvent

from src.ui.pyside_ui.dialog_windows.draggable_window.draggable_dialog import DraggableDialog


def make_mouse_event(button, buttons, pos=QPointF(10, 10)):
    return QMouseEvent(
        QMouseEvent.Type.MouseButtonPress,
        pos,
        pos,
        button,
        buttons,
        Qt.KeyboardModifier.NoModifier,
    )


@pytest.fixture
def dialog(qtbot):
    widget = DraggableDialog()
    qtbot.addWidget(widget)
    return widget


def test_init_sets_up_drag_state(dialog) -> None:
    assert dialog._drag_active is False


def test_mouse_press_event_calls_handler_and_super(dialog) -> None:
    event = make_mouse_event(Qt.MouseButton.LeftButton, Qt.MouseButton.LeftButton)
    with (
        patch.object(DraggableDialog, "_handle_mouse_press") as handler,
        patch("PySide6.QtWidgets.QDialog.mousePressEvent") as super_call,
    ):
        dialog.mousePressEvent(event)

    handler.assert_called_once_with(event)
    super_call.assert_called_once_with(event)


def test_mouse_move_event_calls_handler_and_super(dialog) -> None:
    event = make_mouse_event(Qt.MouseButton.LeftButton, Qt.MouseButton.LeftButton)
    with (
        patch.object(DraggableDialog, "_handle_mouse_move") as handler,
        patch("PySide6.QtWidgets.QDialog.mouseMoveEvent") as super_call,
    ):
        dialog.mouseMoveEvent(event)

    handler.assert_called_once_with(event)
    super_call.assert_called_once_with(event)


def test_mouse_release_event_calls_handler_and_super(dialog) -> None:
    event = make_mouse_event(Qt.MouseButton.LeftButton, Qt.MouseButton.LeftButton)
    with (
        patch.object(DraggableDialog, "_handle_mouse_release") as handler,
        patch("PySide6.QtWidgets.QDialog.mouseReleaseEvent") as super_call,
    ):
        dialog.mouseReleaseEvent(event)

    handler.assert_called_once_with(event)
    super_call.assert_called_once_with(event)
