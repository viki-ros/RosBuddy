from PyQt6.QtWidgets import QDialog, QVBoxLayout, QLineEdit, QLabel, QListWidget, QPushButton, QHBoxLayout

class LaunchFileComposerDialog(QDialog):
    """Dialog for composing a new ROS 2 launch file."""
    def __init__(self, available_nodes=None, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Create New Launch File")
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Launch File Name:"))
        self.launch_name_edit = QLineEdit()
        layout.addWidget(self.launch_name_edit)
        layout.addWidget(QLabel("Select Nodes to Launch:"))
        self.node_list = QListWidget()
        if available_nodes:
            self.node_list.addItems(available_nodes)
        self.node_list.setSelectionMode(QListWidget.SelectionMode.MultiSelection)
        layout.addWidget(self.node_list)
        btn_layout = QHBoxLayout()
        self.ok_btn = QPushButton("Create")
        self.cancel_btn = QPushButton("Cancel")
        btn_layout.addWidget(self.ok_btn)
        btn_layout.addWidget(self.cancel_btn)
        layout.addLayout(btn_layout)
        self.ok_btn.clicked.connect(self.accept)
        self.cancel_btn.clicked.connect(self.reject)
    def get_data(self):
        return {
            'launch_name': self.launch_name_edit.text().strip(),
            'selected_nodes': [item.text() for item in self.node_list.selectedItems()],
        }
