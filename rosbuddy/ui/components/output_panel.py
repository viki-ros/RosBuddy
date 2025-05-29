# Output Display component for ROSBuddy UI

from PyQt6.QtWidgets import QTextEdit, QVBoxLayout, QWidget, QToolButton, QLabel, QHBoxLayout
from PyQt6.QtCore import Qt

class OutputDisplay(QTextEdit):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setReadOnly(True)
        self.setObjectName("outputDisplay")
        self.setMinimumHeight(120)
        self.setStyleSheet("font-family: 'Fira Mono', 'Consolas', 'Monaco', monospace;")

    def append_text(self, text: str):
        self.append(text)

class OutputPanel(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.output_display = OutputDisplay(self)
        self.clear_output_button = QToolButton()
        self.clear_output_button.setText("Clear")
        self.clear_output_button.setToolTip("Clear Output Console")
        self.clear_output_button.setObjectName("clearOutputButton")
        output_header = QLabel("Output Console")
        output_header.setStyleSheet("color: #b0b0b0; font-size: 15px; font-weight: bold; padding: 8px 0 4px 8px;")
        output_toolbar_container = QWidget()
        output_toolbar_layout = QHBoxLayout(output_toolbar_container)
        output_toolbar_layout.setContentsMargins(2,2,2,2)
        output_toolbar_layout.setSpacing(5)
        output_toolbar_layout.addStretch()
        output_toolbar_layout.addWidget(self.clear_output_button)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8,8,8,8)
        layout.setSpacing(6)
        layout.addWidget(output_header)
        layout.addWidget(output_toolbar_container)
        layout.addWidget(self.output_display, stretch=1)
        self.setLayout(layout)
