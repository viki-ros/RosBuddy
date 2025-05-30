# rosbuddy/ui/dialogs/select_dependency_dialog.py
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QDialogButtonBox, QListWidget, QListWidgetItem, QApplication
)
from PyQt6.QtCore import Qt, QStringListModel # For potential future completer on filter
from typing import List, Optional

COMMON_INTERFACE_PACKAGES = sorted([
    "std_msgs", "geometry_msgs", "sensor_msgs", "nav_msgs", "action_msgs",
    "visualization_msgs", "tf2_msgs", "trajectory_msgs", "builtin_interfaces",
    "rosgraph_msgs", "diagnostic_msgs",
    # Common sub-packages often directly depended upon for interfaces
    "unique_identifier_msgs", "statistics_msgs", "std_srvs",
    "shape_msgs", "stereo_msgs", "control_msgs", "tf2_geometry_msgs"
])

class SelectRosPackageDependencyDialog(QDialog):
    def __init__(self, current_package_dependencies: List[str], parent=None):
        super().__init__(parent)
        self.setWindowTitle("Select Interface Package Dependencies")
        self.setMinimumSize(450, 400) # Give it more space

        self.all_known_packages_for_display = list(COMMON_INTERFACE_PACKAGES) # Base list
        # In the future, this list would be augmented by PackageDiscovery results

        self.layout = QVBoxLayout(self)

        # Filter for the list of known packages
        self.filter_edit = QLineEdit()
        self.filter_edit.setPlaceholderText("Filter known packages (e.g., 'geo')")
        self.filter_edit.setToolTip("Type to filter the list of known interface packages below.")
        self.filter_edit.textChanged.connect(self._filter_package_list)
        self.layout.addWidget(QLabel("Available Known Packages (multi-select enabled):"))
        self.layout.addWidget(self.filter_edit)

        # List of known/common packages
        self.known_packages_list_widget = QListWidget()
        self.known_packages_list_widget.setSelectionMode(QListWidget.SelectionMode.ExtendedSelection) # Multi-select
        self.known_packages_list_widget.setToolTip("Select one or more packages from this list.\nThese are common interface-providing packages.")
        self._populate_known_packages_list() # Initial population
        self.layout.addWidget(self.known_packages_list_widget)

        # Field for adding a package not in the list
        self.layout.addWidget(QLabel("Add Other Package (if not listed above):"))
        self.custom_dep_edit = QLineEdit()
        self.custom_dep_edit.setPlaceholderText("e.g., my_other_custom_interface_pkg")
        self.custom_dep_edit.setToolTip("If a required package is not in the list, enter its name here.")
        self.layout.addWidget(self.custom_dep_edit)

        # Dialog Buttons
        self.button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)
        self.button_box.button(QDialogButtonBox.StandardButton.Ok).setToolTip("Add selected/entered packages as dependencies.")
        self.button_box.button(QDialogButtonBox.StandardButton.Cancel).setToolTip("Cancel adding dependencies.")
        self.layout.addWidget(self.button_box)

        # OK button state (can always be enabled as user might just want to add custom)
        # self.ok_button = self.button_box.button(QDialogButtonBox.StandardButton.Ok)
        # self.known_packages_list_widget.itemSelectionChanged.connect(self._update_ok_button_state)
        # self.custom_dep_edit.textChanged.connect(self._update_ok_button_state)
        # self._update_ok_button_state() # Initial check

    def _populate_known_packages_list(self, filter_text: str = ""):
        self.known_packages_list_widget.clear()
        filter_text = filter_text.lower()
        for pkg_name in self.all_known_packages_for_display:
            if not filter_text or filter_text in pkg_name.lower():
                item = QListWidgetItem(pkg_name)
                self.known_packages_list_widget.addItem(item)

    def _filter_package_list(self, text: str):
        self._populate_known_packages_list(text)

    # def _update_ok_button_state(self):
    #     # Enable OK if any package is selected in the list OR custom text is entered
    #     list_selected = bool(self.known_packages_list_widget.selectedItems())
    #     custom_typed = bool(self.custom_dep_edit.text().strip())
    #     self.ok_button.setEnabled(list_selected or custom_typed)

    def get_selected_dependencies(self) -> List[str]: # Returns a list
        selected_deps = []
        if self.result() == QDialog.DialogCode.Accepted:
            # Get from QListWidget
            for item in self.known_packages_list_widget.selectedItems():
                selected_deps.append(item.text())
            
            # Get from custom QLineEdit
            custom_text = self.custom_dep_edit.text().strip()
            if custom_text and custom_text not in selected_deps: # Avoid duplicates if typed same as selected
                selected_deps.append(custom_text)
        
        return sorted(list(set(selected_deps))) # Ensure unique and sorted

# Standalone test for this dialog
if __name__ == '__main__':
    import sys
    app = QApplication(sys.argv)
    # Simulate some already existing dependencies for context if needed by dialog logic
    # For this version, the dialog doesn't strictly need them passed in, but it's good practice.
    current_dialog_deps = ["existing_dep_1"]
    dialog = SelectRosPackageDependencyDialog(current_dialog_deps)
    if dialog.exec():
        deps = dialog.get_selected_dependencies()
        if deps:
            print(f"Selected dependencies: {deps}")
        else:
            print("No dependencies selected or dialog cancelled before OK.")
    else:
        print("Dialog cancelled.")