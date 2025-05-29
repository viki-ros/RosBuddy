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
        self.view_title = view_title
        self._init_base_layout()

    def _init_base_layout(self):
        # Create the base layout with proper margins
        self._base_layout = QVBoxLayout(self)
        self._base_layout.setContentsMargins(10, 10, 10, 10)
        self._base_layout.setSpacing(10)
        
        # Placeholder content - subclasses should call clear_base_layout() first
        self.placeholder_label = QLabel(f"Content for {self.view_title}")
        self.placeholder_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._base_layout.addWidget(self.placeholder_label)

    def clear_base_layout(self):
        """Safely clears all widgets from the base layout."""
        while self._base_layout.count():
            item = self._base_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
            elif item.layout():
                # Recursively clear any nested layouts
                while item.layout().count():
                    nested_item = item.layout().takeAt(0)
                    if nested_item.widget():
                        nested_item.widget().deleteLater()
        return self._base_layout

    def get_view_title(self) -> str:
        return self.view_title

    def set_view_title(self, title: str):
        self.view_title = title
        self.placeholder_label.setText(f"Content for {self.view_title}")
        # If this view is in a tab, the tab text might need to be updated externally