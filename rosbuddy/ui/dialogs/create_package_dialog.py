# rosbuddy/ui/dialogs/create_package_dialog.py
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QFormLayout, QLineEdit, QComboBox, 
    QDialogButtonBox, QLabel, QCheckBox, QTextEdit
)
from PyQt6.QtCore import Qt
from typing import Dict, Any, Optional

class CreatePackageDialog(QDialog):
    def __init__(self, default_maintainer_name="", default_maintainer_email="", parent=None):
        super().__init__(parent)
        self.setWindowTitle("Create New ROS 2 Package")
        self.setMinimumWidth(450)

        self.layout = QVBoxLayout(self)
        self.form_layout = QFormLayout()

        # --- Input Fields ---
        self.package_name_edit = QLineEdit()
        self.package_name_edit.setPlaceholderText("e.g., my_robot_controller")
        self.form_layout.addRow(QLabel("Package Name:"), self.package_name_edit)

        self.build_type_combo = QComboBox()
        self.build_type_combo.addItems(["ament_python", "ament_cmake"])
        self.form_layout.addRow(QLabel("Build Type:"), self.build_type_combo)

        self.version_edit = QLineEdit("0.0.0")
        self.form_layout.addRow(QLabel("Version:"), self.version_edit)

        self.description_edit = QTextEdit() # QTextEdit for potentially longer descriptions
        self.description_edit.setPlaceholderText("A brief description of the package.")
        self.description_edit.setFixedHeight(60) # Set a reasonable initial height
        self.form_layout.addRow(QLabel("Description:"), self.description_edit)

        self.maintainer_name_edit = QLineEdit(default_maintainer_name)
        self.maintainer_name_edit.setPlaceholderText("Your Name")
        self.form_layout.addRow(QLabel("Maintainer Name:"), self.maintainer_name_edit)
        
        self.maintainer_email_edit = QLineEdit(default_maintainer_email)
        self.maintainer_email_edit.setPlaceholderText("you@example.com")
        self.form_layout.addRow(QLabel("Maintainer Email:"), self.maintainer_email_edit)

        self.license_combo = QComboBox()
        self.license_combo.addItems([
            "Apache License 2.0", 
            "MIT License", 
            "BSD-3-Clause", 
            "TODO" # For custom or unspecified
        ])
        self.license_combo.setEditable(True) # Allow user to type a custom license
        self.license_combo.setCurrentText("Apache License 2.0") # Default
        self.form_layout.addRow(QLabel("License:"), self.license_combo)

        self.include_hello_world_checkbox = QCheckBox("Include 'Hello World' example node/executable")
        self.include_hello_world_checkbox.setChecked(True) # Default to including it
        self.form_layout.addRow(self.include_hello_world_checkbox)


        self.layout.addLayout(self.form_layout)

        # --- Dialog Buttons ---
        self.button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)
        
        # Initially disable OK button until package name is entered
        self.ok_button = self.button_box.button(QDialogButtonBox.StandardButton.Ok)
        self.ok_button.setEnabled(False)
        self.package_name_edit.textChanged.connect(self._update_ok_button_state)

        self.layout.addWidget(self.button_box)

    def _update_ok_button_state(self, text):
        """Enable OK button only if package name is not empty."""
        self.ok_button.setEnabled(bool(text.strip()))


    def get_package_data(self) -> Optional[Dict[str, Any]]:
        """
        Returns the entered package data as a dictionary if dialog is accepted.
        Returns None if rejected or data is invalid (though basic validation is handled by button state).
        """
        if self.result() == QDialog.DialogCode.Accepted:
            desc = self.description_edit.toPlainText().strip()
            if not desc:
                desc = "TODO: Package description" # Default if empty
            return {
                "name": self.package_name_edit.text().strip(),
                "build_type": self.build_type_combo.currentText(),
                "version": self.version_edit.text().strip(),
                "description": desc,
                "maintainer_name": self.maintainer_name_edit.text().strip(),
                "maintainer_email": self.maintainer_email_edit.text().strip(),
                "license_name": self.license_combo.currentText().strip(),
                "include_hello_world": self.include_hello_world_checkbox.isChecked()
            }
        return None

if __name__ == '__main__': # For testing this dialog directly
    import sys
    from PyQt6.QtWidgets import QApplication
    app = QApplication(sys.argv)
    # Example usage:
    dialog = CreatePackageDialog(default_maintainer_name="Test User", default_maintainer_email="test@user.com")
    if dialog.exec() == QDialog.DialogCode.Accepted:
        data = dialog.get_package_data()
        print("Package Data Accepted:")
        for key, value in data.items():
            print(f"  {key}: {value}")
    else:
        print("Package Creation Cancelled.")
    # sys.exit(app.exec()) # No need for app.exec() if dialog.exec() is blocking