# rosbuddy/ui/views/base_view.py
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel
from PyQt6.QtCore import Qt

class BaseView(QWidget):
    """
    A base class for views that will be displayed in tabs.
    Provides a common structure or functionality if needed in the future.
    """
    def __init__(self, view_title: str = "View", parent=None):
        super().__init__(parent)
        self.view_title = view_title # Could be used for tab identification or internal state

        # Basic layout
        layout = QVBoxLayout(self)
        # Placeholder content - subclasses should override or add to this
        self.placeholder_label = QLabel(f"Content for {self.view_title}")
        self.placeholder_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.placeholder_label)
        self.setLayout(layout)

    def get_view_title(self) -> str:
        return self.view_title

    def set_view_title(self, title: str):
        self.view_title = title
        self.placeholder_label.setText(f"Content for {self.view_title}")
        # If this view is in a tab, the tab text might need to be updated externally