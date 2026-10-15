from typing import TYPE_CHECKING, cast

from PySide6.QtCore import QPoint, Qt
from PySide6.QtGui import QMouseEvent

if TYPE_CHECKING:
    from PySide6.QtWidgets import QWidget


class DraggableMixin:
    def __init__(self) -> None:
        self._drag_active = False
        self._drag_position = QPoint()

    def _can_drag(self) -> bool:
        return True

    def _handle_mouse_press(self, event: QMouseEvent) -> bool:
        widget = cast("QWidget", self)

        if event.button() == Qt.MouseButton.LeftButton and self._can_drag():
            window_handle = widget.windowHandle()

            if window_handle is not None and window_handle.startSystemMove():
                return True

            self._drag_active = True
            self._drag_position = event.globalPosition().toPoint() - widget.frameGeometry().topLeft()

            event.accept()
            return True

        return False

    def _handle_mouse_move(self, event: QMouseEvent) -> bool:
        widget = cast("QWidget", self)

        if self._drag_active and event.buttons() & Qt.MouseButton.LeftButton:
            widget.move(event.globalPosition().toPoint() - self._drag_position)
            event.accept()
            return True

        return False

    def _handle_mouse_release(self, event: QMouseEvent) -> bool:
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_active = False
            event.accept()
            return True

        return False
