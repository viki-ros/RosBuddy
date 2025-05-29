# rosbuddy/ui/views/launch_runner_view.py
from PyQt6.QtWidgets import QVBoxLayout, QLabel
from PyQt6.QtCore import Qt
from .base_view import BaseView

class LaunchRunnerView(BaseView):
    def __init__(self, parent=None):
        super().__init__(view_title="Launch Runner", parent=parent)
        self.setObjectName("launchRunnerView")
        self.placeholder_label.setText("🚀 Launch Runner - Content Coming Soon")
