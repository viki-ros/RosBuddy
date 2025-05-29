# rosbuddy/ui/views/node_wizard_view.py
from PyQt6.QtWidgets import QVBoxLayout, QLabel
from PyQt6.QtCore import Qt
from .base_view import BaseView

class NodeWizardView(BaseView):
    def __init__(self, parent=None):
        super().__init__(view_title="Node Wizard", parent=parent)
        self.setObjectName("nodeWizardView")
        # self.layout() is the QVBoxLayout from BaseView
        self.placeholder_label.setText("🧙 Node Wizard - Content Coming Soon")
