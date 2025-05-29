# rosbuddy/ui/views/ai_assistant_view.py
from PyQt6.QtWidgets import QVBoxLayout, QLabel, QTextEdit, QLineEdit, QPushButton
from PyQt6.QtCore import Qt
from .base_view import BaseView

class AIAssistantView(BaseView):
    """
    A placeholder view for the AI Assistant.
    """
    def __init__(self, parent=None):
        super().__init__(view_title="AI Assistant", parent=parent)
        self.setObjectName("aiAssistantView")

        layout = QVBoxLayout(self)

        title_label = QLabel("🧠 AI Assistant")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_label.setStyleSheet("font-size: 16pt; font-weight: bold; margin-bottom: 10px;")
        layout.addWidget(title_label)

        self.chat_history_display = QTextEdit()
        self.chat_history_display.setReadOnly(True)
        self.chat_history_display.append("AI: Hello! How can I assist you with ROS today?")
        layout.addWidget(self.chat_history_display, 1) # Stretch factor

        self.user_input_field = QLineEdit()
        self.user_input_field.setPlaceholderText("Ask the AI something...")
        
        send_button = QPushButton("Send")
        
        input_layout = QVBoxLayout() # Changed to QVBoxLayout for better spacing control
        input_layout.addWidget(self.user_input_field)
        input_layout.addWidget(send_button, alignment=Qt.AlignmentFlag.AlignRight)
        
        layout.addLayout(input_layout)
        self.setLayout(layout)