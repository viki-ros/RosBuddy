# rosbuddy/ui/components/action_card.py
from PyQt6.QtWidgets import (
    QFrame, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QSizePolicy, QGraphicsDropShadowEffect
)
from PyQt6.QtGui import QIcon, QColor, QMouseEvent, QEnterEvent
from PyQt6.QtCore import Qt, pyqtSignal, QPropertyAnimation, QPoint, QEasingCurve

class ActionCard(QFrame):
    """
    A clickable card for displaying an action with an icon, title, and description.
    Emits a clicked signal with an action_id.
    """
    clicked = pyqtSignal(str)  # Emits the action_id when clicked

    def __init__(self, action_id: str, title: str, description: str, icon: QIcon = None, parent=None):
        super().__init__(parent)
        self.action_id = action_id
        self.setFrameShape(QFrame.Shape.StyledPanel)
        self.setFrameShadow(QFrame.Shadow.Raised) # Initial shadow
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setObjectName("actionCard")
        self.setMinimumSize(200, 120)
        self.setMaximumSize(280, 180)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)

        self._init_ui(title, description, icon)
        self._apply_stylesheet()

        # Animation for hover effect (optional, can be done with QSS too)
        self.animation = QPropertyAnimation(self, b"pos")
        self.animation.setDuration(150)
        self.animation.setEasingCurve(QEasingCurve.Type.OutQuad)
        self.original_pos = QPoint()

    def _init_ui(self, title_text: str, description_text: str, icon: QIcon):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(10)

        header_layout = QHBoxLayout()
        if icon:
            icon_label = QLabel()
            icon_label.setPixmap(icon.pixmap(32, 32)) # Adjust size as needed
            header_layout.addWidget(icon_label)

        title_label = QLabel(title_text)
        title_label.setObjectName("actionCardTitle")
        title_label.setStyleSheet("font-size: 14pt; font-weight: bold;")
        header_layout.addWidget(title_label, 1) # Stretch
        layout.addLayout(header_layout)

        description_label = QLabel(description_text)
        description_label.setObjectName("actionCardDescription")
        description_label.setWordWrap(True)
        description_label.setStyleSheet("font-size: 10pt; color: #c0c0c0;")
        layout.addWidget(description_label, 1) # Stretch

        layout.addStretch(0)

    def _apply_stylesheet(self):
        # Basic styling, can be enhanced
        self.setStyleSheet("""
            ActionCard#actionCard {
                background-color: #2c313a; /* Slightly lighter than main bg */
                border: 1px solid #353b45;
                border-radius: 8px;
            }
            ActionCard#actionCard:hover {
                background-color: #353b45;
                border: 1px solid #00AEEF; /* Primary color border on hover */
            }
        """)
        # Shadow effect (can be performance intensive if many cards)
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(15)
        shadow.setColor(QColor(0, 0, 0, 100))
        shadow.setOffset(3, 3)
        self.setGraphicsEffect(shadow)

    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit(self.action_id)
        super().mousePressEvent(event)

    def enterEvent(self, event: QEnterEvent):
        # self.original_pos = self.pos()
        # self.animation.setStartValue(self.original_pos)
        # self.animation.setEndValue(self.original_pos - QPoint(0, 5)) # Move up
        # self.animation.start()
        super().enterEvent(event)

    def leaveEvent(self, event: QMouseEvent): # QMouseEvent for leaveEvent
        # self.animation.setStartValue(self.pos())
        # self.animation.setEndValue(self.original_pos)
        # self.animation.start()
        super().leaveEvent(event)