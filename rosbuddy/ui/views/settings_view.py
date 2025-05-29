# rosbuddy/ui/views/settings_view.py
from PyQt6.QtWidgets import QVBoxLayout, QLabel, QLineEdit, QFormLayout, QPushButton
from PyQt6.QtCore import Qt
from .base_view import BaseView

class SettingsView(BaseView):
    """
    A placeholder view for application settings.
    """
    def __init__(self, parent=None):
        super().__init__(view_title="Settings", parent=parent)
        self.setObjectName("settingsView") # For potential QSS styling

        # Clear the placeholder from BaseView if not needed
        # Or, build upon it. For now, let's replace the layout.
        
        layout = QVBoxLayout(self) # New layout for this specific view
        
        title_label = QLabel("⚙️ Application Settings")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_label.setStyleSheet("font-size: 16pt; font-weight: bold; margin-bottom: 10px;")
        layout.addWidget(title_label)

        form_layout = QFormLayout()
        self.theme_combo = QLineEdit("Dark (Current)") # Placeholder for QComboBox
        self.theme_combo.setReadOnly(True)
        form_layout.addRow("Theme:", self.theme_combo)

        self.ros_cli_path_input = QLineEdit("/usr/bin/ros2") # Placeholder
        form_layout.addRow("ROS CLI Path:", self.ros_cli_path_input)
        
        layout.addLayout(form_layout)
        
        save_button = QPushButton("Save Settings (Not Implemented)")
        layout.addWidget(save_button, alignment=Qt.AlignmentFlag.AlignRight)

        layout.addStretch() # Pushes content to the top

        self.setLayout(layout) # Set the new layout