# rosbuddy/ui/views/settings_view.py
from PyQt6.QtWidgets import QVBoxLayout, QLabel, QLineEdit, QFormLayout, QPushButton, QComboBox, QGroupBox, QCheckBox
from PyQt6.QtCore import Qt
from .base_view import BaseView

class SettingsView(BaseView):
    """
    View for application settings.
    """
    def __init__(self, parent=None):
        super().__init__(view_title="Settings", parent=parent)
        self.setObjectName("settingsView")
        self._init_ui()

    def _init_ui(self):
        # Use the new base layout clearing method
        main_layout = self.clear_base_layout()
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(15)

        # Title
        title_label = QLabel("⚙️ Application Settings")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_label.setStyleSheet("font-size: 16pt; font-weight: bold; margin-bottom: 10px;")
        main_layout.addWidget(title_label)

        # Group Box Style
        group_style = """
            QGroupBox {
                font-weight: bold;
                border: 1px solid #353b45;
                border-radius: 6px;
                padding-top: 20px;
                margin-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                subcontrol-position: top left;
                padding: 0 5px;
                left: 10px;
            }
        """

        # --- Appearance Section ---
        appearance_group = QGroupBox("Appearance")
        appearance_group.setStyleSheet(group_style)
        appearance_layout = QFormLayout(appearance_group)
        appearance_layout.setContentsMargins(15, 15, 15, 15)
        appearance_layout.setSpacing(10)
        
        self.theme_combo = QComboBox()
        self.theme_combo.addItems(["Dark", "Light (Not Implemented)"])
        appearance_layout.addRow("Theme:", self.theme_combo)
        main_layout.addWidget(appearance_group)

        # --- ROS Configuration Section ---
        ros_config_group = QGroupBox("ROS Configuration")
        ros_config_group.setStyleSheet(group_style)
        ros_config_layout = QFormLayout(ros_config_group)
        ros_config_layout.setContentsMargins(15, 15, 15, 15)
        ros_config_layout.setSpacing(10)

        self.ros_cli_path_input = QLineEdit("/usr/bin/ros2")
        ros_config_layout.addRow("ROS CLI Path:", self.ros_cli_path_input)

        self.default_workspace_path_input = QLineEdit("~/ros2_ws")
        ros_config_layout.addRow("Default Workspace Path:", self.default_workspace_path_input)

        self.ros_distro_combo = QComboBox()
        self.ros_distro_combo.addItems(["humble", "iron", "jazzy", "rolling"])
        ros_config_layout.addRow("Current ROS Distro:", self.ros_distro_combo)
        main_layout.addWidget(ros_config_group)

        # --- Logging & Debugging Section ---
        logging_group = QGroupBox("Logging & Debugging")
        logging_group.setStyleSheet(group_style)
        logging_layout = QFormLayout(logging_group)
        logging_layout.setContentsMargins(15, 15, 15, 15)
        logging_layout.setSpacing(10)

        self.logging_verbosity_combo = QComboBox()
        self.logging_verbosity_combo.addItems(["DEBUG", "INFO", "WARNING", "ERROR"])
        self.logging_verbosity_combo.setCurrentText("INFO")
        logging_layout.addRow("Logging Verbosity:", self.logging_verbosity_combo)
        main_layout.addWidget(logging_group)

        # --- Keyboard Shortcuts Section ---
        shortcuts_group = QGroupBox("Keyboard Shortcuts")
        shortcuts_group.setStyleSheet(group_style)
        shortcuts_layout = QVBoxLayout(shortcuts_group)
        shortcuts_layout.setContentsMargins(15, 15, 15, 15)
        shortcuts_layout.setSpacing(10)

        shortcuts_label = QLabel("Keyboard shortcut customization coming soon.")
        shortcuts_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        shortcuts_label.setStyleSheet("color: #888; font-style: italic;")
        shortcuts_layout.addWidget(shortcuts_label)
        main_layout.addWidget(shortcuts_group)

        # --- Save Button ---
        save_button = QPushButton("Save Settings")
        save_button.setStyleSheet("""
            QPushButton {
                min-width: 120px;
                padding: 8px 16px;
            }
        """)
        main_layout.addWidget(save_button, alignment=Qt.AlignmentFlag.AlignRight)

        # Add stretch at the end to push everything to the top
        main_layout.addStretch()