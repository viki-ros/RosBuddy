# Workspace Explorer component for ROSBuddy UI

from PyQt6.QtWidgets import QTreeView, QVBoxLayout, QWidget, QLabel
from PyQt6.QtGui import QStandardItemModel, QStandardItem
from PyQt6.QtCore import Qt
import logging

logger = logging.getLogger(__name__)

class WorkspaceExplorer(QWidget):
    def __init__(self, package_discovery, workspace_manager, parent=None):
        super().__init__(parent)
        self.package_discovery = package_discovery
        self.workspace_manager = workspace_manager
        self.model = QStandardItemModel(self)
        self.view = QTreeView(self)
        self.view.setModel(self.model)
        self.view.setHeaderHidden(True)
        self.view.setObjectName("workspaceExplorerView")

        self.header = QLabel("Workspace Explorer")
        self.header.setStyleSheet("color: #b0b0b0; font-size: 15px; font-weight: bold; padding: 8px 0 4px 8px;")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(self.header)
        layout.addWidget(self.view)
        self.setLayout(layout)

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
                    packages_parent_item.appendRow(package_item)
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
