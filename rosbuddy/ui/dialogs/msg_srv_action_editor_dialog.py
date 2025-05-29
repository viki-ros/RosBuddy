from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QLineEdit, QLabel, QComboBox, 
    QTextEdit, QPushButton, QHBoxLayout, QDialogButtonBox
)
from PyQt6.QtCore import Qt
from rosbuddy.data_models.interface_definition import InterfaceFileDefinition
from typing import Optional

class MsgSrvActionEditorDialog(QDialog):
    """Dialog for creating a new ROS 2 message, service, or action file."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Create New ROS Interface (.msg/.srv/.action)")
        self.setMinimumWidth(450)

        layout = QVBoxLayout(self)

        # Type (msg, srv, action)
        type_layout = QHBoxLayout()
        type_layout.addWidget(QLabel("Interface Type:"))
        self.type_combo = QComboBox()
        self.type_combo.addItems(["msg", "srv", "action"])
        type_layout.addWidget(self.type_combo)
        layout.addLayout(type_layout)

        # Name (e.g., MotorStatus, without extension)
        layout.addWidget(QLabel("Interface Name (e.g., MotorStatus, SetTarget):"))
        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("MyCustomMessage")
        layout.addWidget(self.name_edit)

        # Fields/Definition Content
        layout.addWidget(QLabel("Definition Content (e.g., 'int32 data', 'string name'):"))
        self.fields_edit = QTextEdit()
        self.fields_edit.setPlaceholderText(
            "Example for .msg:\nint32 motor_id\nfloat64 position\nfloat64 velocity\n\n"
            "Example for .srv:\nfloat64 request_value\n---\nbool success\nstring response_message\n\n"
            "Example for .action:\nGoalType goal\n---\nResultType result\n---\nFeedbackType feedback"
        )
        self.fields_edit.setMinimumHeight(150)
        layout.addWidget(self.fields_edit)

        # Interface Package Dependencies
        layout.addWidget(QLabel("Package Dependencies (optional, comma-separated, e.g., std_msgs, geometry_msgs):"))
        self.dependencies_edit = QLineEdit()
        self.dependencies_edit.setPlaceholderText("std_msgs, geometry_msgs")
        layout.addWidget(self.dependencies_edit)
        
        # Dialog Buttons
        self.button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)

        # Enable OK button only if name is provided
        self.ok_button = self.button_box.button(QDialogButtonBox.StandardButton.Ok)
        self.ok_button.setEnabled(False)
        self.name_edit.textChanged.connect(self._update_ok_button_state)

        layout.addWidget(self.button_box)

    def _update_ok_button_state(self, text: str):
        self.ok_button.setEnabled(bool(text.strip()))

    def get_data(self) -> Optional[InterfaceFileDefinition]:
        """
        Returns an InterfaceFileDefinition object if dialog is accepted, else None.
        """
        if self.result() != QDialog.DialogCode.Accepted:
            return None

        base_name = self.name_edit.text().strip()
        iface_type = self.type_combo.currentText()
        if not base_name:
            return None
        file_name_with_ext = f"{base_name}.{iface_type}"
        content = self.fields_edit.toPlainText().strip()
        raw_deps_str = self.dependencies_edit.text().strip()
        dependencies = [dep.strip() for dep in raw_deps_str.split(',') if dep.strip()]
        return InterfaceFileDefinition(
            file_name=file_name_with_ext,
            interface_type=iface_type,
            content=content,
            interface_package_dependencies=dependencies
        )

# Standalone test for the dialog
if __name__ == '__main__':
    import sys
    from PyQt6.QtWidgets import QApplication
    app = QApplication(sys.argv)
    dialog = MsgSrvActionEditorDialog()
    if dialog.exec():
        data = dialog.get_data()
        if data:
            print("Interface Data Accepted:")
            print(f"  File Name: {data.file_name}")
            print(f"  Type: {data.interface_type}")
            print(f"  Relative Path: {data.relative_path}")
            print(f"  Content:\n{data.content}")
            print(f"  Dependencies: {data.interface_package_dependencies}")
    else:
        print("Interface Creation Cancelled.")
