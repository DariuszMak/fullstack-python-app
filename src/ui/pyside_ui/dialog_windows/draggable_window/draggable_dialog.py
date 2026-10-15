from PySide6.QtGui import QMouseEvent
from PySide6.QtWidgets import QDialog, QWidget

from src.frontend.pyside_ui.dialog_windows.draggable_window.draggable_mixin import DraggableMixin


class DraggableDialog(QDialog, DraggableMixin):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        DraggableMixin.__init__(self)

    def mousePressEvent(self, event: QMouseEvent) -> None:  # noqa: N802
        self._handle_mouse_press(event)
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event: QMouseEvent) -> None:  # noqa: N802
        self._handle_mouse_move(event)
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:  # noqa: N802
        self._handle_mouse_release(event)
        super().mouseReleaseEvent(event)
