from PyQt6.QtWidgets import QDialog, QVBoxLayout, QLineEdit, QLabel, QComboBox, QTextEdit, QPushButton, QHBoxLayout

class MsgSrvActionEditorDialog(QDialog):
    """Dialog for creating a new ROS 2 message, service, or action file."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Create Msg/Srv/Action")
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Type:"))
        self.type_combo = QComboBox()
        self.type_combo.addItems(["msg", "srv", "action"])
        layout.addWidget(self.type_combo)
        layout.addWidget(QLabel("Name:"))
        self.name_edit = QLineEdit()
        layout.addWidget(self.name_edit)
        layout.addWidget(QLabel("Fields (one per line, e.g. 'int32 data'):"))
        self.fields_edit = QTextEdit()
        layout.addWidget(self.fields_edit)
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
            'type': self.type_combo.currentText(),
            'name': self.name_edit.text().strip(),
            'fields': [line.strip() for line in self.fields_edit.toPlainText().splitlines() if line.strip()],
        }
