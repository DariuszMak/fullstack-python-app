import structlog
from PySide6.QtCore import QEvent, Qt
from PySide6.QtGui import QCloseEvent, QPixmap
from PySide6.QtWidgets import QWidget

from src.helpers.style_loader import StyleLoader
from src.ui.pyside_ui.dialog_windows.draggable_window.draggable_dialog import DraggableDialog
from src.ui.pyside_ui.forms.moc_warning_dialog import Ui_Dialog

logger = structlog.get_logger(__name__)


class WarningDialog(DraggableDialog):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__()
        self._ui = Ui_Dialog()
        self._ui.setupUi(self)  # type: ignore[no-untyped-call]
        StyleLoader.style_window(self)

        self.setWindowFlags(Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        self._ui.btn_close.clicked.connect(self.close)
        StyleLoader.center_window(self, parent)

        pixmap = QPixmap(":/logos/icons/images/warning.png")
        self._ui.label_warning.setPixmap(pixmap.scaled(40, 40, Qt.AspectRatioMode.KeepAspectRatio))

        logger.debug("warning_dialog_initialized", parent=type(parent).__name__ if parent else None)

    def changeEvent(self, event: QEvent) -> None:  # noqa: N802
        if event.type() == QEvent.Type.LanguageChange:
            self._ui.retranslateUi(self)  # type: ignore[no-untyped-call]
            logger.debug("dialog_language_changed")
        super().changeEvent(event)

    def closeEvent(self, event: QCloseEvent) -> None:  # noqa: N802
        logger.info("warning_dialog_closed")
        super().closeEvent(event)
