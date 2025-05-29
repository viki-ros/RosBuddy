# rosbuddy/ui/views/ros_doctor_view.py
from PyQt6.QtWidgets import QVBoxLayout, QLabel
from PyQt6.QtCore import Qt
from .base_view import BaseView

class RosDoctorView(BaseView):
    def __init__(self, parent=None):
        super().__init__(view_title="ROS Doctor", parent=parent)
        self.setObjectName("rosDoctorView")
        self.placeholder_label.setText("🩺 ROS Doctor - Content Coming Soon")
