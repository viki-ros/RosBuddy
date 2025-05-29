from PyQt6.QtWidgets import QDialog, QVBoxLayout, QLineEdit, QComboBox, QLabel, QPushButton, QHBoxLayout

class NodeCreatorDialog(QDialog):
    """Dialog for creating a new ROS 2 node (Python or C++)."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Create New Node")
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Node Name:"))
        self.node_name_edit = QLineEdit()
        layout.addWidget(self.node_name_edit)
        layout.addWidget(QLabel("Language:"))
        self.lang_combo = QComboBox()
        self.lang_combo.addItems(["Python", "C++"])
        layout.addWidget(self.lang_combo)
        layout.addWidget(QLabel("Subscribe Topic(s): (comma separated)"))
        self.sub_topics_edit = QLineEdit()
        layout.addWidget(self.sub_topics_edit)
        layout.addWidget(QLabel("Publish Topic(s): (comma separated)"))
        self.pub_topics_edit = QLineEdit()
        layout.addWidget(self.pub_topics_edit)
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
            'node_name': self.node_name_edit.text().strip(),
            'language': self.lang_combo.currentText(),
            'subscribe_topics': [t.strip() for t in self.sub_topics_edit.text().split(',') if t.strip()],
            'publish_topics': [t.strip() for t in self.pub_topics_edit.text().split(',') if t.strip()],
        }
