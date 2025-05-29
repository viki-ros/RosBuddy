# Contextual View Placeholder component for ROSBuddy UI

from PyQt6.QtWidgets import QLabel
from PyQt6.QtCore import Qt

class ContextualViewPlaceholder(QLabel):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setText("Contextual View (Coming Soon)")
        self.setObjectName("contextualViewPlaceholder")
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setStyleSheet("color: #b0b0b0; font-size: 15px; font-weight: 600; padding: 16px;")
