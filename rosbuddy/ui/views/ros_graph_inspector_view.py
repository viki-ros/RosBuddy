# rosbuddy/ui/views/ros_graph_inspector_view.py
from PyQt6.QtWidgets import QVBoxLayout, QLabel
from PyQt6.QtCore import Qt
from .base_view import BaseView

class RosGraphInspectorView(BaseView):
    def __init__(self, parent=None):
        super().__init__(view_title="ROS Graph Inspector", parent=parent)
        self.setObjectName("rosGraphInspectorView")
        self.placeholder_label.setText("📈 ROS Graph Inspector - Content Coming Soon")
