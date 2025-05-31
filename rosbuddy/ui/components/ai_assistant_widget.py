# AI Assistant Sidebar Widget for ROSBuddy
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, QTextEdit
from PyQt6.QtCore import Qt

class AIAssistantWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(8)

        self.title = QLabel("AI Assistant")
        self.title.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.title.setStyleSheet("font-weight: bold; font-size: 16px;")
        layout.addWidget(self.title)

        self.response_area = QTextEdit()
        self.response_area.setReadOnly(True)
        self.response_area.setPlaceholderText("AI responses will appear here...")
        layout.addWidget(self.response_area, 1)

        input_row = QHBoxLayout()
        self.input_box = QLineEdit()
        self.input_box.setPlaceholderText("Ask the AI something...")
        input_row.addWidget(self.input_box, 1)
        self.send_button = QPushButton("Send")
        input_row.addWidget(self.send_button)
        layout.addLayout(input_row)

        self.send_button.clicked.connect(self.on_send)
        self.input_box.returnPressed.connect(self.on_send)

    def on_send(self):
        text = self.input_box.text().strip()
        if not text:
            return
        # For now, just echo the input as a fake response
        self.response_area.append(f"<b>You:</b> {text}")
        self.response_area.append(f"<b>AI:</b> (This is a stub response)")
        self.input_box.clear()
