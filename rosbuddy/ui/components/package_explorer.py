from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QTreeView, QToolBar,
                               QPushButton, QFileDialog, QMenu, QInputDialog,
                               QMessageBox)
from PyQt6.QtCore import Qt, pyqtSignal, QModelIndex
from PyQt6.QtGui import QStandardItemModel, QStandardItem

import os
import xml.etree.ElementTree as ET

class PackageExplorer(QWidget):
    package_selected = pyqtSignal(str)  # Emits package path
    file_selected = pyqtSignal(str)     # Emits file path

    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_workspace = None
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)

        # Toolbar
        toolbar = QToolBar()
        
        self.refresh_btn = QPushButton("Refresh")
        self.refresh_btn.clicked.connect(self.refresh_workspace)
        toolbar.addWidget(self.refresh_btn)
        
        self.new_pkg_btn = QPushButton("New Package")
        self.new_pkg_btn.clicked.connect(self.create_new_package)
        toolbar.addWidget(self.new_pkg_btn)
        
        layout.addWidget(toolbar)

        # Package tree
        self.tree_view = QTreeView()
        self.tree_model = QStandardItemModel()
        self.tree_model.setHorizontalHeaderLabels(["Name", "Type"])
        self.tree_view.setModel(self.tree_model)
        self.tree_view.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.tree_view.customContextMenuRequested.connect(self.show_context_menu)
        self.tree_view.clicked.connect(self.handle_item_clicked)
        
        layout.addWidget(self.tree_view)

    def set_workspace(self, workspace_path):
        """Set and load a ROS 2 workspace."""
        self.current_workspace = workspace_path
        self.refresh_workspace()

    def refresh_workspace(self):
        """Refresh the workspace tree view."""
        if not self.current_workspace:
            return

        self.tree_model.clear()
        self.tree_model.setHorizontalHeaderLabels(["Name", "Type"])
        
        src_dir = os.path.join(self.current_workspace, "src")
        if not os.path.exists(src_dir):
            return

        for pkg_dir in os.listdir(src_dir):
            pkg_path = os.path.join(src_dir, pkg_dir)
            if os.path.isdir(pkg_path):
                pkg_xml = os.path.join(pkg_path, "package.xml")
                if os.path.exists(pkg_xml):
                    self.add_package_to_tree(pkg_path)

    def add_package_to_tree(self, pkg_path):
        """Add a package to the tree view."""
        try:
            tree = ET.parse(os.path.join(pkg_path, "package.xml"))
            root = tree.getroot()
            
            pkg_name = root.find("name").text
            pkg_item = QStandardItem(pkg_name)
            pkg_item.setData(pkg_path, Qt.ItemDataRole.UserRole)
            
            type_item = QStandardItem("Package")
            
            self.tree_model.appendRow([pkg_item, type_item])
            
            # Add package contents
            self.add_package_contents(pkg_item, pkg_path)
            
        except Exception as e:
            print(f"Error adding package {pkg_path}: {e}")

    def add_package_contents(self, parent_item, pkg_path):
        """Add package contents to the tree."""
        # Add src directory
        src_dir = os.path.join(pkg_path, "src")
        if os.path.exists(src_dir):
            src_item = QStandardItem("src")
            src_item.setData(src_dir, Qt.ItemDataRole.UserRole)
            type_item = QStandardItem("Directory")
            parent_item.appendRow([src_item, type_item])
            self.add_directory_contents(src_item, src_dir)

        # Add launch directory
        launch_dir = os.path.join(pkg_path, "launch")
        if os.path.exists(launch_dir):
            launch_item = QStandardItem("launch")
            launch_item.setData(launch_dir, Qt.ItemDataRole.UserRole)
            type_item = QStandardItem("Directory")
            parent_item.appendRow([launch_item, type_item])
            self.add_directory_contents(launch_item, launch_dir)

        # Add config directory
        config_dir = os.path.join(pkg_path, "config")
        if os.path.exists(config_dir):
            config_item = QStandardItem("config")
            config_item.setData(config_dir, Qt.ItemDataRole.UserRole)
            type_item = QStandardItem("Directory")
            parent_item.appendRow([config_item, type_item])
            self.add_directory_contents(config_item, config_dir)

    def add_directory_contents(self, parent_item, dir_path):
        """Add directory contents to the tree."""
        for item in os.listdir(dir_path):
            item_path = os.path.join(dir_path, item)
            item_node = QStandardItem(item)
            item_node.setData(item_path, Qt.ItemDataRole.UserRole)
            
            if os.path.isdir(item_path):
                type_item = QStandardItem("Directory")
                parent_item.appendRow([item_node, type_item])
                self.add_directory_contents(item_node, item_path)
            else:
                type_item = QStandardItem("File")
                parent_item.appendRow([item_node, type_item])

    def show_context_menu(self, position):
        """Show context menu for tree items."""
        index = self.tree_view.indexAt(position)
        if not index.isValid():
            return

        item = self.tree_model.itemFromIndex(index)
        item_path = item.data(Qt.ItemDataRole.UserRole)
        item_type = self.tree_model.item(index.row(), 1).text()

        menu = QMenu()
        
        if item_type == "Package":
            build_action = menu.addAction("Build Package")
            clean_action = menu.addAction("Clean Package")
            menu.addSeparator()
            new_node_action = menu.addAction("New Node")
            new_launch_action = menu.addAction("New Launch File")
            
        elif item_type == "Directory":
            new_file_action = menu.addAction("New File")
            new_dir_action = menu.addAction("New Directory")
            
        elif item_type == "File":
            open_action = menu.addAction("Open")
            delete_action = menu.addAction("Delete")

        action = menu.exec(self.tree_view.viewport().mapToGlobal(position))
        
        if action:
            self.handle_context_action(action, item_path, item_type)

    def handle_context_action(self, action, item_path, item_type):
        """Handle context menu actions."""
        if action.text() == "Build Package":
            self.build_package(item_path)
        elif action.text() == "Clean Package":
            self.clean_package(item_path)
        elif action.text() == "New Node":
            self.create_new_node(item_path)
        elif action.text() == "New Launch File":
            self.create_new_launch_file(item_path)
        elif action.text() == "New File":
            self.create_new_file(item_path)
        elif action.text() == "New Directory":
            self.create_new_directory(item_path)
        elif action.text() == "Open":
            self.open_file(item_path)
        elif action.text() == "Delete":
            self.delete_item(item_path)

    def handle_item_clicked(self, index):
        """Handle item click in tree view."""
        item = self.tree_model.itemFromIndex(index)
        item_path = item.data(Qt.ItemDataRole.UserRole)
        item_type = self.tree_model.item(index.row(), 1).text()

        if item_type == "Package":
            self.package_selected.emit(item_path)
        elif item_type == "File":
            self.file_selected.emit(item_path)

    def create_new_package(self):
        """Create a new ROS 2 package."""
        if not self.current_workspace:
            QMessageBox.warning(self, "Error", "No workspace selected")
            return

        name, ok = QInputDialog.getText(self, "New Package", "Package name:")
        if ok and name:
            # This will be connected to the package creation logic
            pass

    def build_package(self, pkg_path):
        """Build a ROS 2 package."""
        # This will be connected to the build system
        pass

    def clean_package(self, pkg_path):
        """Clean a ROS 2 package."""
        # This will be connected to the build system
        pass

    def create_new_node(self, pkg_path):
        """Create a new ROS 2 node."""
        # This will be connected to the node creation system
        pass

    def create_new_launch_file(self, pkg_path):
        """Create a new launch file."""
        # This will be connected to the launch file creation system
        pass

    def create_new_file(self, dir_path):
        """Create a new file."""
        name, ok = QInputDialog.getText(self, "New File", "File name:")
        if ok and name:
            file_path = os.path.join(dir_path, name)
            try:
                with open(file_path, 'w') as f:
                    pass
                self.refresh_workspace()
            except Exception as e:
                QMessageBox.warning(self, "Error", f"Failed to create file: {e}")

    def create_new_directory(self, parent_path):
        """Create a new directory."""
        name, ok = QInputDialog.getText(self, "New Directory", "Directory name:")
        if ok and name:
            dir_path = os.path.join(parent_path, name)
            try:
                os.makedirs(dir_path)
                self.refresh_workspace()
            except Exception as e:
                QMessageBox.warning(self, "Error", f"Failed to create directory: {e}")

    def open_file(self, file_path):
        """Open a file."""
        self.file_selected.emit(file_path)

    def delete_item(self, item_path):
        """Delete a file or directory."""
        msg = f"Are you sure you want to delete {os.path.basename(item_path)}?"
        reply = QMessageBox.question(self, "Confirm Delete", msg,
                                   QMessageBox.StandardButton.Yes | 
                                   QMessageBox.StandardButton.No)
        
        if reply == QMessageBox.StandardButton.Yes:
            try:
                if os.path.isdir(item_path):
                    os.rmdir(item_path)
                else:
                    os.remove(item_path)
                self.refresh_workspace()
            except Exception as e:
                QMessageBox.warning(self, "Error", f"Failed to delete: {e}") 