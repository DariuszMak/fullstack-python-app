from unittest.mock import MagicMock, patch

import pytest
from PySide6.QtCore import QPoint, QPointF, Qt
from PySide6.QtGui import QMouseEvent

from src.ui.pyside_ui.dialog_windows.draggable_window.draggable_mixin import DraggableMixin


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
def mixin():
    instance = DraggableMixin()
    return instance


def test_init_sets_defaults(mixin) -> None:
    assert mixin._drag_active is False
    assert mixin._drag_position == QPoint()


def test_can_drag_default_true(mixin) -> None:
    assert mixin._can_drag() is True


def test_handle_mouse_press_wrong_button_returns_false(mixin) -> None:
    with patch.object(DraggableMixin, "_can_drag", return_value=True):
        widget = MagicMock()
        with patch(
            "src.ui.pyside_ui.dialog_windows.draggable_window.draggable_mixin.cast",
            return_value=widget,
        ):
            event = make_mouse_event(Qt.MouseButton.RightButton, Qt.MouseButton.RightButton)
            result = mixin._handle_mouse_press(event)
    assert result is False
    assert mixin._drag_active is False


def test_handle_mouse_press_cannot_drag_returns_false(mixin) -> None:
    with patch.object(DraggableMixin, "_can_drag", return_value=False):
        widget = MagicMock()
        with patch(
            "src.ui.pyside_ui.dialog_windows.draggable_window.draggable_mixin.cast",
            return_value=widget,
        ):
            event = make_mouse_event(Qt.MouseButton.LeftButton, Qt.MouseButton.LeftButton)
            result = mixin._handle_mouse_press(event)
    assert result is False
    assert mixin._drag_active is False


def test_handle_mouse_press_with_system_move_success(mixin) -> None:
    widget = MagicMock()
    widget.windowHandle.return_value.startSystemMove.return_value = True

    with patch(
        "src.ui.pyside_ui.dialog_windows.draggable_window.draggable_mixin.cast",
        return_value=widget,
    ):
        event = make_mouse_event(Qt.MouseButton.LeftButton, Qt.MouseButton.LeftButton)
        result = mixin._handle_mouse_press(event)

    assert result is True
    assert mixin._drag_active is False


def test_handle_mouse_press_no_window_handle_sets_drag_active(mixin) -> None:
    widget = MagicMock()
    widget.windowHandle.return_value = None
    widget.frameGeometry.return_value.topLeft.return_value = QPoint(0, 0)

    with patch(
        "src.ui.pyside_ui.dialog_windows.draggable_window.draggable_mixin.cast",
        return_value=widget,
    ):
        event = make_mouse_event(Qt.MouseButton.LeftButton, Qt.MouseButton.LeftButton)
        result = mixin._handle_mouse_press(event)

    assert result is True
    assert mixin._drag_active is True
    assert isinstance(mixin._drag_position, QPoint)


def test_handle_mouse_press_system_move_fails_sets_drag_active(mixin) -> None:
    widget = MagicMock()
    widget.windowHandle.return_value.startSystemMove.return_value = False
    widget.frameGeometry.return_value.topLeft.return_value = QPoint(0, 0)

    with patch(
        "src.ui.pyside_ui.dialog_windows.draggable_window.draggable_mixin.cast",
        return_value=widget,
    ):
        event = make_mouse_event(Qt.MouseButton.LeftButton, Qt.MouseButton.LeftButton)
        result = mixin._handle_mouse_press(event)

    assert result is True
    assert mixin._drag_active is True


def test_handle_mouse_move_active_and_left_button_moves_widget(mixin) -> None:
    mixin._drag_active = True
    mixin._drag_position = QPoint(1, 1)
    widget = MagicMock()

    with patch(
        "src.ui.pyside_ui.dialog_windows.draggable_window.draggable_mixin.cast",
        return_value=widget,
    ):
        event = make_mouse_event(Qt.MouseButton.LeftButton, Qt.MouseButton.LeftButton)
        result = mixin._handle_mouse_move(event)

    assert result is True
    widget.move.assert_called_once()


def test_handle_mouse_move_not_active_returns_false(mixin) -> None:
    mixin._drag_active = False
    widget = MagicMock()

    with patch(
        "src.ui.pyside_ui.dialog_windows.draggable_window.draggable_mixin.cast",
        return_value=widget,
    ):
        event = make_mouse_event(Qt.MouseButton.LeftButton, Qt.MouseButton.LeftButton)
        result = mixin._handle_mouse_move(event)

    assert result is False
    widget.move.assert_not_called()


def test_handle_mouse_move_active_but_no_left_button_returns_false(mixin) -> None:
    mixin._drag_active = True
    widget = MagicMock()

    with patch(
        "src.ui.pyside_ui.dialog_windows.draggable_window.draggable_mixin.cast",
        return_value=widget,
    ):
        event = make_mouse_event(Qt.MouseButton.RightButton, Qt.MouseButton.RightButton)
        result = mixin._handle_mouse_move(event)

    assert result is False
    widget.move.assert_not_called()


def test_handle_mouse_release_left_button_resets_drag_active(mixin) -> None:
    mixin._drag_active = True
    event = make_mouse_event(Qt.MouseButton.LeftButton, Qt.MouseButton.LeftButton)

    result = mixin._handle_mouse_release(event)

    assert result is True
    assert mixin._drag_active is False


def test_handle_mouse_release_other_button_returns_false(mixin) -> None:
    mixin._drag_active = True
    event = make_mouse_event(Qt.MouseButton.RightButton, Qt.MouseButton.RightButton)

    result = mixin._handle_mouse_release(event)

    assert result is False
    assert mixin._drag_active is True
