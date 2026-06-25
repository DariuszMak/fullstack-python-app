from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QProgressBar, QSizePolicy, QWidget

from src.backend.api.models.weather_score_response import PlaceBestScoreRecord


class WeatherScoreCard(QFrame):
    def __init__(self, place: PlaceBestScoreRecord, rank: int | None = None, parent: QWidget | None = None) -> None:
        super().__init__(parent)

        self.setObjectName("weatherScoreCard")
        self.setFrameShape(QFrame.Shape.StyledPanel)
        self.setToolTip(f"{place.latitude:.4f}, {place.longitude:.4f} ({place.timezone})")

        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 8, 10, 8)
        layout.setSpacing(10)

        self._rank_label = QLabel(f"#{rank}" if rank is not None else "", self)
        self._rank_label.setFixedWidth(30)
        self._rank_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        rank_font = self._rank_label.font()
        rank_font.setBold(True)
        self._rank_label.setFont(rank_font)

        self._name_label = QLabel(place.name, self)
        self._name_label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)

        self._score_bar = QProgressBar(self)
        self._score_bar.setRange(0, 100)
        self._score_bar.setTextVisible(False)
        self._score_bar.setFixedWidth(140)

        self._score_label = QLabel(self)
        self._score_label.setFixedWidth(50)
        self._score_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)

        layout.addWidget(self._rank_label)
        layout.addWidget(self._name_label)
        layout.addWidget(self._score_bar)
        layout.addWidget(self._score_label)

        self.set_score(place.score)

    def set_score(self, score: float) -> None:
        clamped = max(0.0, min(1.0, score))
        percentage = int(round(clamped * 100))

        self._score_bar.setValue(percentage)
        self._score_label.setText(f"{score:.2f}")

        color = self._color_for_score(clamped)
        self._score_bar.setStyleSheet(
            "QProgressBar { border-radius: 4px; background-color: rgb(52, 59, 72); }"
            f"QProgressBar::chunk {{ background-color: {color}; border-radius: 4px; }}"
        )

    @property
    def name(self) -> str:
        return self._name_label.text()

    @property
    def score_value(self) -> int:
        return self._score_bar.value()

    @property
    def score_text(self) -> str:
        return self._score_label.text()

    @staticmethod
    def _color_for_score(score: float) -> str:
        if score >= 0.66:
            return "rgb(46, 204, 113)"
        if score >= 0.33:
            return "rgb(241, 196, 15)"
        return "rgb(231, 76, 60)"