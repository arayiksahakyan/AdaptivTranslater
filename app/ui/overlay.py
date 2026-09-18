from PySide6.QtCore import QEvent, QPoint, QRect, Qt, Signal
from PySide6.QtGui import QColor, QKeyEvent, QMouseEvent, QPainter, QPen
from PySide6.QtWidgets import QLabel, QWidget


class LensOverlay(QWidget):
    """Transparent lens with a title-strip drag target and eight resize targets."""

    geometry_changed = Signal()
    interaction_changed = Signal(bool)
    edit_requested = Signal()
    close_requested = Signal()
    BORDER = 8
    HEADER = 38

    def __init__(self) -> None:
        super().__init__(
            None, Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint
        )
        self.setWindowTitle("Translation Lens — lens")
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setMouseTracking(True)
        self.setMinimumSize(280, 180)
        self.resize(720, 360)
        self.click_through = False
        self._anchor: QPoint | None = None
        self._original = QRect()
        self._edges: frozenset[str] = frozenset()
        self.output = QLabel(self)
        self.output.setTextFormat(Qt.TextFormat.PlainText)
        self.output.setWordWrap(True)
        self.output.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
        self.output.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self.output.setStyleSheet(
            "QLabel { color: #f4f7ff; background: rgba(16, 22, 34, 220);"
            " border-radius: 8px; padding: 10px; font-size: 14px; }"
        )
        self.output.hide()

    @property
    def interacting(self) -> bool:
        return self._anchor is not None

    def capture_rect(self) -> QRect:
        return QRect(
            self.BORDER,
            self.HEADER,
            self.width() - 2 * self.BORDER,
            self.height() - self.HEADER - self.BORDER,
        )

    def set_translation(self, text: str) -> None:
        self.output.setText(text[:6000] + ("\n…" if len(text) > 6000 else ""))
        self.output.setVisible(bool(text))
        self._layout_output()

    def set_mode(self, click_through: bool) -> None:
        self.cancel_interaction()
        self.click_through = click_through
        self.update()

    def event(self, event: QEvent) -> bool:
        if event.type() == QEvent.Type.DevicePixelRatioChange:
            self.geometry_changed.emit()
        return super().event(event)

    def _layout_output(self) -> None:
        height = min(150, int(self.height() * 0.42))
        self.output.setGeometry(14, self.height() - height - 14, self.width() - 28, height)

    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        color = QColor("#43d8b3" if self.click_through else "#79aaff")
        painter.setPen(QPen(color, 2))
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawRoundedRect(self.rect().adjusted(2, 2, -2, -2), 8, 8)
        painter.fillRect(4, 4, self.width() - 8, self.HEADER - 8, QColor(16, 22, 34, 225))
        painter.setPen(color)
        mode = "Click-through · Ctrl+Shift+L to edit" if self.click_through else "Edit · drag here"
        painter.drawText(14, 25, f"Translation Lens  |  {mode}")
        if not self.click_through:
            painter.drawLine(
                self.width() - 18, self.height() - 6, self.width() - 6, self.height() - 18
            )

    def resizeEvent(self, event) -> None:
        self._layout_output()
        self.geometry_changed.emit()
        super().resizeEvent(event)

    def moveEvent(self, event) -> None:
        self.geometry_changed.emit()
        super().moveEvent(event)

    def _hit_edges(self, point: QPoint) -> frozenset[str]:
        edges = set()
        if point.x() < self.BORDER:
            edges.add("left")
        if point.x() >= self.width() - self.BORDER:
            edges.add("right")
        if point.y() < self.BORDER:
            edges.add("top")
        if point.y() >= self.height() - self.BORDER:
            edges.add("bottom")
        return frozenset(edges)

    def mousePressEvent(self, event: QMouseEvent) -> None:
        if self.click_through or event.button() != Qt.MouseButton.LeftButton:
            return
        edges = self._hit_edges(event.position().toPoint())
        if not edges and event.position().y() >= self.HEADER:
            return
        self._anchor = event.globalPosition().toPoint()
        self._original = self.geometry()
        self._edges = edges
        self.setFocus()
        self.interaction_changed.emit(True)
        event.accept()

    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        if self.click_through:
            return
        if self._anchor is None:
            edges = self._hit_edges(event.position().toPoint())
            if len(edges) == 2:
                cursor = (
                    Qt.CursorShape.SizeFDiagCursor
                    if edges in (frozenset(("left", "top")), frozenset(("right", "bottom")))
                    else Qt.CursorShape.SizeBDiagCursor
                )
            elif edges & {"left", "right"}:
                cursor = Qt.CursorShape.SizeHorCursor
            elif edges:
                cursor = Qt.CursorShape.SizeVerCursor
            else:
                cursor = Qt.CursorShape.ArrowCursor
            self.setCursor(cursor)
            return
        delta = event.globalPosition().toPoint() - self._anchor
        rect = QRect(self._original)
        if not self._edges:
            rect.translate(delta)
        else:
            if "left" in self._edges:
                rect.setLeft(min(rect.left() + delta.x(), rect.right() - self.minimumWidth() + 1))
            if "right" in self._edges:
                rect.setRight(max(rect.right() + delta.x(), rect.left() + self.minimumWidth() - 1))
            if "top" in self._edges:
                rect.setTop(min(rect.top() + delta.y(), rect.bottom() - self.minimumHeight() + 1))
            if "bottom" in self._edges:
                rect.setBottom(
                    max(rect.bottom() + delta.y(), rect.top() + self.minimumHeight() - 1)
                )
        self.setGeometry(rect)
        event.accept()

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        if event.button() == Qt.MouseButton.LeftButton and self._anchor is not None:
            self._anchor = None
            self.interaction_changed.emit(False)

    def cancel_interaction(self) -> None:
        if self._anchor is not None:
            self.setGeometry(self._original)
            self._anchor = None
            self.interaction_changed.emit(False)

    def keyPressEvent(self, event: QKeyEvent) -> None:
        if event.key() == Qt.Key.Key_Escape:
            self.cancel_interaction()
            self.edit_requested.emit()
            event.accept()
        else:
            super().keyPressEvent(event)

    def closeEvent(self, event) -> None:
        event.ignore()
        self.close_requested.emit()
