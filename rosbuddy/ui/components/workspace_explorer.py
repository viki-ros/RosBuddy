# Workspace Explorer component for ROSBuddy UI

import pathlib # Added for path manipulation
from PyQt6.QtWidgets import QTreeView, QVBoxLayout, QWidget, QLabel, QStyle # Added QStyle
from PyQt6.QtGui import QStandardItemModel, QStandardItem, QIcon # Added QIcon
from PyQt6.QtCore import Qt, pyqtSignal, QModelIndex # Added pyqtSignal and QModelIndex
import logging

logger = logging.getLogger(__name__)

class WorkspaceExplorer(QWidget):
    # Define the signal that this custom widget will emit
    doubleClicked = pyqtSignal(QModelIndex)

    def __init__(self, package_discovery, workspace_manager, parent=None):
        super().__init__(parent)
        self.package_discovery = package_discovery
        self.workspace_manager = workspace_manager
        self.model = QStandardItemModel(self)
        self.view = QTreeView(self)
        self.view.setModel(self.model)
        self.view.setHeaderHidden(True)
        self.view.setObjectName("workspaceExplorerView")

        # Connect the internal tree's signal to this widget's custom signal
        self.view.doubleClicked.connect(self.doubleClicked.emit)

        self.header = QLabel("Workspace Explorer")
        self.header.setStyleSheet("color: #b0b0b0; font-size: 15px; font-weight: bold; padding: 8px 0 4px 8px;")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(self.header)
        layout.addWidget(self.view)
        self.setLayout(layout)

    def _populate_directory_item(self, parent_item: QStandardItem, dir_path: pathlib.Path, depth: int = 0, max_depth: int = 1):
        """
        Populates a parent item with contents of a directory.
        - parent_item: The QStandardItem representing the directory.
        - dir_path: The pathlib.Path object for the directory.
        - depth: Current recursion depth.
        - max_depth: How many levels of subdirectories to populate for important_dirs.
        """
        if not dir_path.is_dir():
            return

        # Important files and directories to always show
        important_files = ["package.xml", "CMakeLists.txt", "setup.py"]
        important_dirs = [
            "src", "launch", "include", "config", "test", "msg", "srv", "action",
            "resource", "params", "worlds", "models", "urdf", "rviz"
        ]
        # Recognized file extensions for ROS/typical text files
        recognized_exts = {".py", ".cpp", ".hpp", ".xml", ".yaml", ".yml", ".txt", ".md", ".msg", ".srv", ".action"}

        # Icons
        icon_file = self.style().standardIcon(QStyle.StandardPixmap.SP_FileIcon)
        icon_folder = self.style().standardIcon(QStyle.StandardPixmap.SP_DirIcon)
        icon_xml = QIcon.fromTheme("text-xml", icon_file)
        icon_cmake = QIcon.fromTheme("text-x-cmake", icon_file)
        icon_python = QIcon.fromTheme("text-x-python", icon_file)
        icon_yaml = QIcon.fromTheme("text-x-yaml", icon_file)
        icon_msg = QIcon.fromTheme("text-x-generic", icon_file)
        icon_srv = QIcon.fromTheme("text-x-generic", icon_file)
        icon_action = QIcon.fromTheme("text-x-generic", icon_file)

        try:
            # Sort: directories first, then files, all alphabetically
            sorted_items = sorted(list(dir_path.iterdir()), key=lambda p: (p.is_file(), p.name.lower()))
            for item_path in sorted_items:
                item_name = item_path.name
                item_data_role = Qt.ItemDataRole.UserRole + 2

                if item_path.is_file():
                    # Only show important files or recognized extensions
                    show_file = (
                        item_name in important_files or
                        item_path.suffix in recognized_exts
                    )
                    if not show_file:
                        continue
                    # Icon selection
                    if item_name == "package.xml":
                        current_icon = icon_xml
                    elif item_name == "CMakeLists.txt":
                        current_icon = icon_cmake
                    elif item_name == "setup.py" or item_path.suffix == ".py":
                        current_icon = icon_python
                    elif item_path.suffix in {".yaml", ".yml"}:
                        current_icon = icon_yaml
                    elif item_path.suffix == ".msg":
                        current_icon = icon_msg
                    elif item_path.suffix == ".srv":
                        current_icon = icon_srv
                    elif item_path.suffix == ".action":
                        current_icon = icon_action
                    else:
                        current_icon = icon_file
                    file_item = QStandardItem(current_icon, item_name)
                    file_item.setEditable(False)
                    file_item.setData(str(item_path.resolve()), item_data_role)
                    parent_item.appendRow(file_item)

                elif item_path.is_dir():
                    # Only show important directories
                    if item_name not in important_dirs:
                        continue
                    dir_item = QStandardItem(icon_folder, item_name)
                    dir_item.setEditable(False)
                    dir_item.setData(str(item_path.resolve()), item_data_role)
                    parent_item.appendRow(dir_item)
                    # Recurse into important directories if within max_depth
                    if depth < max_depth:
                        self._populate_directory_item(dir_item, item_path, depth + 1, max_depth)
        except PermissionError:
            logger.warning(f"Permission denied for {dir_path}")
            parent_item.appendRow(QStandardItem(f"Permission Denied: {dir_path.name}"))
        except Exception as e:
            logger.error(f"Error populating directory {dir_path}: {e}", exc_info=True)
            parent_item.appendRow(QStandardItem(f"Error listing: {dir_path.name}"))

    def update(self):
        """Update the workspace explorer tree view with the active workspace and its packages."""
        self.model.clear()
        active_ws_path = self.workspace_manager.get_active_workspace_path()
        if not active_ws_path:
            root_item = QStandardItem("No Active Workspace")
            root_item.setEditable(False)
            self.model.appendRow(root_item)
            self.view.header().setVisible(False)
            return
        
        ws_name = active_ws_path.name
        ws_root_item = QStandardItem(f"Workspace: {ws_name}")
        ws_root_item.setEditable(False)
        self.model.appendRow(ws_root_item)
        try:
            discovered_packages = self.package_discovery.find_packages_in_active_workspace()
            if discovered_packages:
                packages_parent_item = QStandardItem("Packages")
                packages_parent_item.setEditable(False)
                ws_root_item.appendRow(packages_parent_item)
                for pkg_info in discovered_packages:
                    package_item = QStandardItem(pkg_info.name)
                    package_item.setEditable(False)
                    package_item.setData(pkg_info, Qt.ItemDataRole.UserRole + 1)
                    # Set a package icon
                    package_item.setIcon(QIcon.fromTheme("package-x-generic", self.style().standardIcon(QStyle.StandardPixmap.SP_DriveNetIcon)))
                    packages_parent_item.appendRow(package_item)
                    # Populate this package item with its files and important directories
                    self._populate_directory_item(package_item, pkg_info.path, max_depth=1)
                self.view.expand(packages_parent_item.index())
            else:
                no_packages_item = QStandardItem("No packages found in src/")
                no_packages_item.setEditable(False)
                ws_root_item.appendRow(no_packages_item)
            self.view.expand(ws_root_item.index())
        except Exception as e:
            error_msg = f"Error during package discovery or populating tree: {e}"
            logger.error(error_msg, exc_info=True)
            error_item = QStandardItem("Error loading packages")
            error_item.setEditable(False)
            ws_root_item.appendRow(error_item)
        self.view.header().setVisible(False)
