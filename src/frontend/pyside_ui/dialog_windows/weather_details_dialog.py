from __future__ import annotations

from typing import TYPE_CHECKING

import structlog
from PySide6.QtCore import QEvent, Qt
from PySide6.QtWidgets import QFrame, QGridLayout, QHBoxLayout, QLabel, QVBoxLayout, QWidget

from src.frontend.pyside_ui.dialog_windows.draggable_window.draggable_dialog import DraggableDialog
from src.frontend.pyside_ui.forms.moc_weather_details_dialog import Ui_Dialog
from src.helpers.style_loader import StyleLoader

if TYPE_CHECKING:
    from PySide6.QtGui import QCloseEvent

    from src.backend.api.models.weather_score_response import PlaceBestScoreRecord

logger = structlog.get_logger(__name__)


class WeatherDetailsDialog(DraggableDialog):
    def __init__(self, place: PlaceBestScoreRecord, rank: int | None = None, parent: QWidget | None = None) -> None:
        super().__init__()
        self._place = place
        self._values: dict[str, QLabel] = {}

        self._ui = Ui_Dialog()
        self._ui.setupUi(self)  # type: ignore[no-untyped-call]
        self._build_ui(rank)
        StyleLoader.style_window(self)

        self.setWindowFlags(Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        self._ui.btn_close.clicked.connect(self.close)
        StyleLoader.center_window(self, parent)
        self.setMinimumSize(500, 200)
        self.setMaximumSize(16777215, 16777215)
        self.ensurePolished()
        self.adjustSize()
        logger.debug("weather_details_dialog_initialized", parent=type(parent).__name__ if parent else None)

    @property
    def place(self) -> PlaceBestScoreRecord:
        return self._place

    def value(self, field: str) -> str:
        return self._values[field].text()

    def _build_ui(self, rank: int | None) -> None:
        outer_layout = self._ui.formLayout

        self._container = QFrame(self)
        self._container.setObjectName("weatherDetailsFrame")
        outer_layout.addWidget(self._container)

        container_layout = QVBoxLayout(self._container)
        container_layout.setContentsMargins(20, 10, 20, 20)
        container_layout.setSpacing(14)

        title_layout = QHBoxLayout()
        title_layout.setContentsMargins(0, 0, 0, 0)

        self._title_label = QLabel(self._place.name, self._container)
        self._title_label.setObjectName("label_title_bar_top")
        title_font = self._title_label.font()
        title_font.setBold(True)
        title_font.setPointSize(title_font.pointSize() + 4)
        self._title_label.setFont(title_font)

        title_layout.addWidget(self._title_label, 1)
        container_layout.addLayout(title_layout)

        separator = QFrame(self._container)
        separator.setFixedHeight(1)
        container_layout.addWidget(separator)

        grid = QGridLayout()
        grid.setContentsMargins(0, 0, 0, 0)
        grid.setHorizontalSpacing(20)
        grid.setVerticalSpacing(10)
        grid.setColumnStretch(1, 1)

        rows = (
            ("name", "Name", self._place.name),
            ("rank", "Rank", f"#{rank}" if rank is not None else "-"),
            ("key", "Key", self._place.key),
            ("latitude", "Latitude", f"{self._place.latitude:.4f}"),
            ("longitude", "Longitude", f"{self._place.longitude:.4f}"),
            ("timezone", "Timezone", self._place.timezone),
            ("score", "Score", f"{self._place.score:.2f}"),
            ("calculated_score", "Calculated score", f"{self._place.percentage_score:.2f}"),
        )

        for row, (field, caption, text) in enumerate(rows):
            caption_label = QLabel(caption, self._container)

            value_label = QLabel(text, self._container)
            value_label.setWordWrap(True)

            grid.addWidget(caption_label, row, 0, Qt.AlignmentFlag.AlignTop)
            grid.addWidget(value_label, row, 1)

            self._values[field] = value_label

        container_layout.addLayout(grid)
        container_layout.addStretch(1)

    def changeEvent(self, event: QEvent) -> None:  # noqa: N802
        if event.type() == QEvent.Type.LanguageChange:
            self._ui.retranslateUi(self)  # type: ignore[no-untyped-call]
            logger.debug("dialog_language_changed")
        super().changeEvent(event)

    def closeEvent(self, event: QCloseEvent) -> None:  # noqa: N802
        logger.info("weather_details_dialog_closed", place=self._place.key)
        super().closeEvent(event)
