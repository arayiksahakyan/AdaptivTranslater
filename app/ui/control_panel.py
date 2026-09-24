from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QKeyEvent
from PySide6.QtWidgets import (
    QComboBox,
    QFormLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from app.translation.provider import LANGUAGES
from app.translation.registry import PROVIDER_LABELS


class ControlPanel(QWidget):
    toggle_requested = Signal()
    mode_requested = Signal()
    edit_requested = Signal()
    languages_changed = Signal(str, str)
    provider_changed = Signal(str)
    close_requested = Signal()

    def __init__(
        self, source: str, target: str, ocr_language: str, provider: str = "argos-local",
    ) -> None:
        super().__init__()
        self.setWindowTitle("Translation Lens")
        self.setMinimumWidth(340)
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating)
        layout = QVBoxLayout(self)
        title = QLabel("Translation Lens")
        title.setStyleSheet("font-size: 23px; font-weight: 600;")
        layout.addWidget(title)
        note = QLabel("Local OCR · translation provider selected below")
        note.setWordWrap(True)
        layout.addWidget(note)
        form = QFormLayout()
        self.provider = QComboBox()
        for identifier, label in PROVIDER_LABELS.items():
            self.provider.addItem(label, identifier)
        self.provider.setItemData(
            self.provider.findData("argos-local"), "Argos Translate", Qt.ItemDataRole.ToolTipRole
        )
        self.provider.setCurrentIndex(self.provider.findData(provider))
        form.addRow("Translation provider", self.provider)
        self.source = QComboBox()
        self.target = QComboBox()
        self.source.addItem("Auto", "auto")
        for code, name in LANGUAGES:
            self.source.addItem(name, code)
            self.target.addItem(name, code)
        self.source.setCurrentIndex(self.source.findData(source))
        self.target.setCurrentIndex(self.target.findData(target))
        form.addRow("Source", self.source)
        form.addRow("Target", self.target)
        layout.addLayout(form)
        self.privacy_note = QLabel()
        self.privacy_note.setWordWrap(True)
        layout.addWidget(self.privacy_note)
        self._update_privacy_note()
        model_note = QLabel(
            f"OCR model language: {ocr_language}. Set at launch with --ocr-language."
        )
        model_note.setWordWrap(True)
        layout.addWidget(model_note)
        self.start_button = QPushButton("Start Translation")
        self.start_button.clicked.connect(self.toggle_requested)
        layout.addWidget(self.start_button)
        self.mode_button = QPushButton("Mode: Edit — enable click-through")
        self.mode_button.clicked.connect(self.mode_requested)
        layout.addWidget(self.mode_button)
        self.status = QLabel("Ready — place the lens over text")
        self.status.setWordWrap(True)
        self.status.setTextFormat(Qt.TextFormat.PlainText)
        layout.addWidget(self.status)
        self.metrics = QLabel("OCR: — | Translation: —")
        layout.addWidget(self.metrics)
        self.platform_note = QLabel()
        self.platform_note.setWordWrap(True)
        self.platform_note.setTextFormat(Qt.TextFormat.PlainText)
        layout.addWidget(self.platform_note)
        shortcuts = QLabel("Ctrl+Shift+T: start/pause\nCtrl+Shift+L: mode · Esc: cancel edit")
        layout.addWidget(shortcuts)
        quit_button = QPushButton("Quit")
        quit_button.clicked.connect(self.close_requested)
        layout.addWidget(quit_button)
        self.source.currentIndexChanged.connect(self._languages_changed)
        self.target.currentIndexChanged.connect(self._languages_changed)
        self.provider.currentIndexChanged.connect(self._provider_changed)

    def _languages_changed(self) -> None:
        self.languages_changed.emit(self.source.currentData(), self.target.currentData())

    def _provider_changed(self) -> None:
        self._update_privacy_note()
        self.provider_changed.emit(self.provider.currentData())

    def _update_privacy_note(self) -> None:
        notes = {
            "argos-local": "Local translation — no text leaves your computer. "
            "Choose a source language; installed language models are required.",
            "mock": "Mock output — repeats text with a label; no real translation.",
            "google-cloud-basic": "Recognized text is sent to Google Cloud. "
            "An API key and billing are required.",
        }
        self.privacy_note.setText(notes[self.provider.currentData()])

    def set_running(self, running: bool) -> None:
        self.start_button.setText("Pause Translation" if running else "Start Translation")

    def set_mode(self, click_through: bool) -> None:
        self.mode_button.setText(
            "Mode: Click-through — enable editing"
            if click_through
            else "Mode: Edit — enable click-through"
        )

    def set_status(self, text: str, error: bool = False) -> None:
        self.status.setText(text)
        self.status.setStyleSheet("color: #c13c3c;" if error else "")

    def keyPressEvent(self, event: QKeyEvent) -> None:
        if event.key() == Qt.Key.Key_Escape:
            self.edit_requested.emit()
            event.accept()
        else:
            super().keyPressEvent(event)

    def closeEvent(self, event) -> None:
        event.ignore()
        self.close_requested.emit()
