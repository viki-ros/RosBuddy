# rosbuddy/ui/views/debug_view.py
from PyQt6.QtWidgets import QVBoxLayout, QLabel
from PyQt6.QtCore import Qt
from .base_view import BaseView

class DebugView(BaseView):
    def __init__(self, parent=None):
        super().__init__(view_title="Debug View", parent=parent)
        self.setObjectName("debugView")
        self.placeholder_label.setText("🐞 Debug View - Content Coming Soon")
