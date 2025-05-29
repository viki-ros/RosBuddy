# rosbuddy/ui/views/ai_assistant_view.py
from PyQt6.QtWidgets import QVBoxLayout, QHBoxLayout, QLabel, QTextEdit, QLineEdit, QPushButton, QScrollArea, QWidget
from PyQt6.QtCore import Qt
from .base_view import BaseView

class AIAssistantView(BaseView):
    """
    View for the AI Assistant interface.
    """
    def __init__(self, parent=None):
        super().__init__(view_title="AI Assistant", parent=parent)
        self.setObjectName("aiAssistantView")
        self._init_ui()

    def _init_ui(self):
        # Use the new base layout clearing method
        main_layout = self.clear_base_layout()
        main_layout.setContentsMargins(15, 15, 15, 15)
        main_layout.setSpacing(10)

        # Title Section
        title_label = QLabel("🧠 AI Assistant")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_label.setStyleSheet("font-size: 16pt; font-weight: bold; margin-bottom: 10px;")
        main_layout.addWidget(title_label)

        # Context Section
        context_label = QLabel("Context: Current Workspace (my_ros_ws), Active File (None)")
        context_label.setStyleSheet("font-size: 9pt; color: #aaa; margin-bottom: 5px;")
        main_layout.addWidget(context_label)

        # Chat History
        self.chat_history_display = QTextEdit()
        self.chat_history_display.setReadOnly(True)
        self.chat_history_display.setObjectName("aiChatHistory")
        self.chat_history_display.setStyleSheet("""
            QTextEdit {
                background-color: #2c313a;
                border-radius: 6px;
                padding: 8px;
            }
        """)
        self.chat_history_display.append("AI: Hello! How can I assist you with ROS today?")
        main_layout.addWidget(self.chat_history_display, 1)  # Stretch factor

        # Quick Prompts Section
        prompts_container = QWidget()
        prompts_container.setFixedHeight(50)  # Fixed height for the prompt area
        prompts_layout = QHBoxLayout(prompts_container)
        prompts_layout.setContentsMargins(0, 0, 0, 0)
        prompts_layout.setSpacing(8)

        prompts = ["Explain this code", "How to create a publisher?", "Debug common errors", "What is TF?"]
        for prompt_text in prompts:
            btn = QPushButton(prompt_text)
            btn.setMinimumWidth(120)
            btn.setMaximumWidth(200)
            # btn.clicked.connect(lambda checked, text=prompt_text: self.on_quick_prompt_clicked(text))
            prompts_layout.addWidget(btn)
        prompts_layout.addStretch()

        # Wrap prompts in a scroll area
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setWidget(prompts_container)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll_area.setStyleSheet("QScrollArea { border: none; }")
        scroll_area.setFixedHeight(60)
        main_layout.addWidget(scroll_area)

        # Input Area
        input_container = QWidget()
        input_layout = QHBoxLayout(input_container)
        input_layout.setContentsMargins(0, 0, 0, 0)
        input_layout.setSpacing(8)

        self.user_input_field = QLineEdit()
        self.user_input_field.setPlaceholderText("Ask the AI something...")
        self.user_input_field.setObjectName("aiUserInput")
        self.user_input_field.setStyleSheet("""
            QLineEdit {
                padding: 8px;
                border-radius: 4px;
                border: 1px solid #353b45;
            }
        """)
        
        send_button = QPushButton("Send")
        send_button.setMinimumWidth(80)
        
        input_layout.addWidget(self.user_input_field, 1)
        input_layout.addWidget(send_button)
        
        main_layout.addWidget(input_container)