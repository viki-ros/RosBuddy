from PyQt6.QtWidgets import QDialog, QVBoxLayout, QLabel, QTextEdit, QPushButton, QHBoxLayout

class PackageConfigEditorDialog(QDialog):
    """Dialog for editing package.xml and CMakeLists.txt dependencies."""
    def __init__(self, current_deps='', parent=None):
        super().__init__(parent)
        self.setWindowTitle("Edit package.xml/CMakeLists.txt")
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Dependencies (comma separated):"))
        self.deps_edit = QTextEdit()
        self.deps_edit.setPlainText(current_deps)
        layout.addWidget(self.deps_edit)
        btn_layout = QHBoxLayout()
        self.ok_btn = QPushButton("Save")
        self.cancel_btn = QPushButton("Cancel")
        btn_layout.addWidget(self.ok_btn)
        btn_layout.addWidget(self.cancel_btn)
        layout.addLayout(btn_layout)
        self.ok_btn.clicked.connect(self.accept)
        self.cancel_btn.clicked.connect(self.reject)
    def get_data(self):
        return {
            'dependencies': [d.strip() for d in self.deps_edit.toPlainText().split(',') if d.strip()],
        }
