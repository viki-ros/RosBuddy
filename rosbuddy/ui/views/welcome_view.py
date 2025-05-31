# rosbuddy/ui/views/welcome_view.py
from PyQt6.QtWidgets import QVBoxLayout, QLabel, QGridLayout, QScrollArea, QWidget
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QIcon
from .base_view import BaseView
from rosbuddy.ui.components.action_card import ActionCard # Import ActionCard

class WelcomeView(BaseView):
    """
    A welcome view with quick actions.
    """
    action_card_clicked = pyqtSignal(str) # Emits the action_id of the clicked card

    def __init__(self, parent=None):
        super().__init__(view_title="Welcome", parent=parent)
        self.setObjectName("welcomeView")
        self._init_ui()

    def _init_ui(self):
        # Use the layout from BaseView after clearing it
        main_layout = self.clear_base_layout()
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(20)

        # ScrollArea for the cards
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)

        title_label = QLabel("Welcome to ROSBuddy!")
        title_label.setStyleSheet("font-size: 24pt; font-weight: bold; margin-bottom: 20px;")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(title_label)

        info_label = QLabel(
            "Your assistant for ROS 2 development.\n"
            "Select an item from the Workspace Explorer, or use the sidebar to access tools."
        )
        info_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        info_label.setWordWrap(True)
        info_label.setStyleSheet("font-size: 12pt; margin-bottom: 30px;")
        main_layout.addWidget(info_label)

        # --- Action Cards Grid ---
        cards_container = QWidget()
        grid_layout = QGridLayout(cards_container)
        grid_layout.setSpacing(20)
        grid_layout.setAlignment(Qt.AlignmentFlag.AlignCenter) # Center the grid if fewer items

        # Define card data (action_id, title, description, icon_name_or_path)
        card_definitions = [
            ("open_workspace", "Open Workspace", "Open an existing ROS 2 workspace.", "document-open"),
            ("new_workspace", "New Workspace", "Create a new ROS 2 workspace.", "document-new"),
            ("create_package", "Create Package", "Scaffold a new ROS 2 package.", "package-x-generic"),
            ("ai_assistant", "AI Assistant", "Chat with the AI for help and guidance.", "preferences-desktop-ai-assistant"),
            ("settings", "Settings", "Configure ROSBuddy application settings.", "preferences-system"),
            ("launch_runner", "Launch Runner", "Manage and run ROS 2 launch files.", "application-x-executable"), # Placeholder icon
        ]

        from rosbuddy.utils.icon_manager import IconManager
        icon_manager = IconManager(self.style())

        row, col = 0, 0
        max_cols = 3 # Adjust as needed

        for action_id, title, desc, icon_name in card_definitions:
            icon = icon_manager.get_icon(icon_name)
            card = ActionCard(action_id, title, desc, icon)
            card.clicked.connect(self.action_card_clicked) # Emit signal from WelcomeView
            grid_layout.addWidget(card, row, col)
            
            col += 1
            if col >= max_cols:
                col = 0
                row += 1
        
        # Add stretch to fill remaining space in the grid if not full
        # for r_idx in range(row + 1):
        #     grid_layout.setRowStretch(r_idx, 0)
        # for c_idx in range(max_cols):
        #     grid_layout.setColumnStretch(c_idx, 0)
        # grid_layout.setRowStretch(row + 1, 1)
        # grid_layout.setColumnStretch(max_cols, 1)

        scroll_area.setWidget(cards_container)
        main_layout.addWidget(scroll_area, 1) # Scroll area takes remaining space

        main_layout.addStretch()
