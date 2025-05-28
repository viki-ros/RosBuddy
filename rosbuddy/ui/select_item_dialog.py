# rosbuddy/ui/dialogs/select_item_dialog.py
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QFormLayout, QComboBox, 
    QDialogButtonBox, QLabel, QMessageBox, QWidget, QHBoxLayout
)
from PyQt6.QtCore import Qt
from typing import List, Dict, Any, Optional, Tuple

# Import PackageDiscovery and PackageInfo
from rosbuddy.core_logic import PackageDiscovery, PackageInfo 

class SelectRosItemDialog(QDialog):
    """
    A dialog for selecting a ROS 2 package and then either an executable or a launch file
    from that package using dynamic dropdowns.
    """
    def __init__(self, 
                 package_discovery: PackageDiscovery, 
                 mode: str, # "run" or "launch"
                 parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"Select ROS 2 Package & {'Executable' if mode == 'run' else 'Launch File'}")
        self.setMinimumWidth(500)

        self.package_discovery = package_discovery
        self.mode = mode # "run" or "launch"

        self.discovered_packages: List[PackageInfo] = []
        self.selected_package_info: Optional[PackageInfo] = None
        self.selected_item_name: Optional[str] = None

        self._init_ui()
        self._load_packages()

    def _init_ui(self):
        self.main_layout = QVBoxLayout(self)
        self.form_layout = QFormLayout()

        # --- Package Selection ---
        self.package_label = QLabel("Select Package:")
        self.package_combo = QComboBox()
        self.package_combo.setPlaceholderText("Loading packages...")
        self.package_combo.setMinimumContentsLength(20) # Ensure enough space for names
        self.package_combo.activated.connect(self._on_package_selected)
        self.form_layout.addRow(self.package_label, self.package_combo)

        # --- Item (Executable/Launch File) Selection ---
        self.item_label = QLabel(f"Select {'Executable' if self.mode == 'run' else 'Launch File'}:")
        self.item_combo = QComboBox()
        self.item_combo.setPlaceholderText("Select a package first...")
        self.item_combo.setMinimumContentsLength(20) # Ensure enough space for names
        self.item_combo.activated.connect(self._on_item_selected)
        self.item_combo.setEnabled(False) # Disabled until package is selected
        self.form_layout.addRow(self.item_label, self.item_combo)

        self.main_layout.addLayout(self.form_layout)

        # --- Dialog Buttons ---
        self.button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)
        
        self.ok_button = self.button_box.button(QDialogButtonBox.StandardButton.Ok)
        self.ok_button.setEnabled(False) # Disabled until both package and item are selected

        self.main_layout.addWidget(self.button_box)

    def _load_packages(self):
        """Discovers packages and populates the package dropdown."""
        self.package_combo.clear()
        self.package_combo.addItem("Loading packages...") # Indicate loading
        self.package_combo.setEnabled(False)
        self.item_combo.clear()
        self.item_combo.setEnabled(False)
        self.ok_button.setEnabled(False)

        # In a real app, this might be a threaded operation too if many packages
        # For now, it runs in main thread.
        try:
            self.discovered_packages = self.package_discovery.find_packages_in_active_workspace()
            self.package_combo.clear()
            if not self.discovered_packages:
                self.package_combo.addItem("No packages found.")
                QMessageBox.information(self, "No Packages", "No ROS 2 packages found in the active workspace. Please create one.")
                return

            self.package_combo.addItem("-- Select a package --") # Default placeholder
            for pkg_info in self.discovered_packages:
                self.package_combo.addItem(pkg_info.name)
            
            self.package_combo.setEnabled(True)
            self.package_combo.setCurrentIndex(0) # Select the placeholder

        except Exception as e:
            msg = f"Error discovering packages: {e}"
            QMessageBox.critical(self, "Package Discovery Error", msg)
            self.package_combo.clear()
            self.package_combo.addItem("Error loading packages.")
            print(f"ERROR: {msg}")
            # Optionally log full traceback: traceback.print_exc()

    def _on_package_selected(self, index: int):
        """Called when a package is selected in the dropdown."""
        if index <= 0: # -- Select a package -- or No packages found
            self.selected_package_info = None
            self.item_combo.clear()
            self.item_combo.setEnabled(False)
            self.item_combo.setPlaceholderText("Select a package first...")
            self.ok_button.setEnabled(False)
            return

        self.selected_package_info = self.discovered_packages[index - 1] # -1 because of placeholder item
        self.item_combo.clear()
        self.selected_item_name = None

        items_to_display: List[str] = []
        if self.mode == "run":
            items_to_display = self.selected_package_info.executables
        elif self.mode == "launch":
            items_to_display = self.selected_package_info.launch_files
        
        if not items_to_display:
            self.item_combo.addItem(f"No {'executables' if self.mode == 'run' else 'launch files'} found in this package.")
            self.item_combo.setEnabled(False)
            self.ok_button.setEnabled(False)
            return

        self.item_combo.addItem(f"-- Select a {'executable' if self.mode == 'run' else 'launch file'} --") # Placeholder
        for item_name in items_to_display:
            self.item_combo.addItem(item_name)
        
        self.item_combo.setEnabled(True)
        self.item_combo.setCurrentIndex(0) # Select the placeholder

    def _on_item_selected(self, index: int):
        """Called when an item (executable/launch file) is selected."""
        if index <= 0: # Placeholder selected
            self.selected_item_name = None
            self.ok_button.setEnabled(False)
        else:
            self.selected_item_name = self.item_combo.currentText()
            self.ok_button.setEnabled(True)

    def get_selection(self) -> Optional[Tuple[str, str]]:
        """
        Returns the selected package name and item name (executable or launch file).
        Returns None if dialog is rejected or selection is incomplete.
        """
        if self.result() == QDialog.DialogCode.Accepted:
            if self.selected_package_info and self.selected_item_name:
                return self.selected_package_info.name, self.selected_item_name
        return None


if __name__ == '__main__': # For testing this dialog directly
    import sys
    from PyQt6.QtWidgets import QApplication
    # Need a dummy PackageDiscovery for standalone test
    class DummyPackageInfo:
        def __init__(self, name, path, build_type, executables=None, launch_files=None):
            self.name = name; self.path = pathlib.Path(path); self.build_type = build_type
            self.executables = executables if executables is not None else []
            self.launch_files = launch_files if launch_files is not None else []
    class DummyPackageDiscovery:
        def __init__(self, packages_data): self._packages_data = packages_data
        def find_packages_in_active_workspace(self) -> List[PackageInfo]:
            # Simulate a few packages
            return [
                DummyPackageInfo("my_python_pkg", "/tmp/ws/src/my_python_pkg", "ament_python", 
                                 executables=["hello_world", "talker_node"], 
                                 launch_files=["start.launch.py", "debug.launch.xml"]),
                DummyPackageInfo("my_cpp_pkg", "/tmp/ws/src/my_cpp_pkg", "ament_cmake", 
                                 executables=["cpp_node", "listener_exe"], 
                                 launch_files=["main.launch.py"]),
                DummyPackageInfo("no_exec_pkg", "/tmp/ws/src/no_exec_pkg", "ament_python", 
                                 executables=[], launch_files=["basic.launch.py"]),
                DummyPackageInfo("empty_pkg", "/tmp/ws/src/empty_pkg", "ament_cmake", 
                                 executables=[], launch_files=[]),
            ]

    app = QApplication(sys.argv)
    
    # Test for "Launch File" mode
    dummy_pd_launch = DummyPackageDiscovery(None) # Data loaded in find_packages_in_active_workspace
    dialog_launch = SelectRosItemDialog(package_discovery=dummy_pd_launch, mode="launch")
    if dialog_launch.exec() == QDialog.DialogCode.Accepted:
        pkg, item = dialog_launch.get_selection()
        print(f"Launch Selected: Package='{pkg}', Launch File='{item}'")
    else:
        print("Launch Selection Cancelled.")

    # Test for "Run Executable" mode
    dummy_pd_run = DummyPackageDiscovery(None)
    dialog_run = SelectRosItemDialog(package_discovery=dummy_pd_run, mode="run")
    if dialog_run.exec() == QDialog.DialogCode.Accepted:
        pkg, item = dialog_run.get_selection()
        print(f"Run Selected: Package='{pkg}', Executable='{item}'")
    else:
        print("Run Selection Cancelled.")