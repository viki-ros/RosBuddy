from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QTreeWidget,
                               QTreeWidgetItem, QPushButton, QMenu, QDialog,
                               QLabel, QLineEdit, QComboBox, QCheckBox)
from PyQt6.QtCore import pyqtSignal, Qt

class LaunchBuilder(QWidget):
    launch_updated = pyqtSignal(dict)  # Emits launch configuration updates

    NODE_TYPES = [
        "Node",
        "ComposableNode",
        "LifecycleNode"
    ]

    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()
        self.launch_config = {}

    def init_ui(self):
        layout = QVBoxLayout(self)

        # Toolbar
        toolbar = QHBoxLayout()
        
        add_node_btn = QPushButton("Add Node")
        add_node_btn.clicked.connect(self.show_add_node_dialog)
        toolbar.addWidget(add_node_btn)
        
        add_param_btn = QPushButton("Add Parameter")
        add_param_btn.clicked.connect(self.show_add_param_dialog)
        toolbar.addWidget(add_param_btn)
        
        add_arg_btn = QPushButton("Add Argument")
        add_arg_btn.clicked.connect(self.show_add_arg_dialog)
        toolbar.addWidget(add_arg_btn)
        
        layout.addLayout(toolbar)

        # Launch configuration tree
        self.tree = QTreeWidget()
        self.tree.setHeaderLabels(["Component", "Type", "Configuration"])
        self.tree.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.tree.customContextMenuRequested.connect(self.show_context_menu)
        layout.addWidget(self.tree)

        # Generate button
        generate_btn = QPushButton("Generate Launch File")
        generate_btn.clicked.connect(self.generate_launch_file)
        layout.addWidget(generate_btn)

    def show_add_node_dialog(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("Add Node")
        layout = QVBoxLayout(dialog)

        # Node type
        type_label = QLabel("Node Type:")
        type_combo = QComboBox()
        type_combo.addItems(self.NODE_TYPES)
        layout.addWidget(type_label)
        layout.addWidget(type_combo)

        # Package name
        pkg_label = QLabel("Package:")
        pkg_edit = QLineEdit()
        layout.addWidget(pkg_label)
        layout.addWidget(pkg_edit)

        # Executable
        exec_label = QLabel("Executable:")
        exec_edit = QLineEdit()
        layout.addWidget(exec_label)
        layout.addWidget(exec_edit)

        # Node name
        name_label = QLabel("Node Name:")
        name_edit = QLineEdit()
        layout.addWidget(name_label)
        layout.addWidget(name_edit)

        # Namespace
        ns_label = QLabel("Namespace:")
        ns_edit = QLineEdit()
        layout.addWidget(ns_label)
        layout.addWidget(ns_edit)

        # Output
        output_label = QLabel("Output:")
        output_combo = QComboBox()
        output_combo.addItems(["screen", "log"])
        layout.addWidget(output_label)
        layout.addWidget(output_combo)

        # Respawn
        respawn_check = QCheckBox("Respawn on crash")
        layout.addWidget(respawn_check)

        # Add button
        add_btn = QPushButton("Add Node")
        add_btn.clicked.connect(lambda: self.add_node(
            type_combo.currentText(),
            pkg_edit.text(),
            exec_edit.text(),
            name_edit.text(),
            ns_edit.text(),
            output_combo.currentText(),
            respawn_check.isChecked(),
            dialog
        ))
        layout.addWidget(add_btn)

        dialog.exec()

    def add_node(self, node_type, package, executable, name, namespace, output, respawn, dialog):
        node_config = {
            "type": node_type,
            "package": package,
            "executable": executable,
            "name": name,
            "namespace": namespace,
            "output": output,
            "respawn": respawn
        }

        item = QTreeWidgetItem(self.tree)
        item.setText(0, name or executable)
        item.setText(1, node_type)
        item.setText(2, f"pkg: {package}, exec: {executable}")
        item.setData(0, Qt.ItemDataRole.UserRole, node_config)

        self.update_launch_config()
        dialog.accept()

    def show_add_param_dialog(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("Add Parameter")
        layout = QVBoxLayout(dialog)

        # Parameter name
        name_label = QLabel("Parameter Name:")
        name_edit = QLineEdit()
        layout.addWidget(name_label)
        layout.addWidget(name_edit)

        # Parameter value
        value_label = QLabel("Value:")
        value_edit = QLineEdit()
        layout.addWidget(value_label)
        layout.addWidget(value_edit)

        # Add button
        add_btn = QPushButton("Add Parameter")
        add_btn.clicked.connect(lambda: self.add_parameter(
            name_edit.text(),
            value_edit.text(),
            dialog
        ))
        layout.addWidget(add_btn)

        dialog.exec()

    def add_parameter(self, name, value, dialog):
        param_config = {
            "name": name,
            "value": value
        }

        item = QTreeWidgetItem(self.tree)
        item.setText(0, name)
        item.setText(1, "Parameter")
        item.setText(2, f"value: {value}")
        item.setData(0, Qt.ItemDataRole.UserRole, param_config)

        self.update_launch_config()
        dialog.accept()

    def show_add_arg_dialog(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("Add Launch Argument")
        layout = QVBoxLayout(dialog)

        # Argument name
        name_label = QLabel("Argument Name:")
        name_edit = QLineEdit()
        layout.addWidget(name_label)
        layout.addWidget(name_edit)

        # Default value
        default_label = QLabel("Default Value:")
        default_edit = QLineEdit()
        layout.addWidget(default_label)
        layout.addWidget(default_edit)

        # Description
        desc_label = QLabel("Description:")
        desc_edit = QLineEdit()
        layout.addWidget(desc_label)
        layout.addWidget(desc_edit)

        # Add button
        add_btn = QPushButton("Add Argument")
        add_btn.clicked.connect(lambda: self.add_argument(
            name_edit.text(),
            default_edit.text(),
            desc_edit.text(),
            dialog
        ))
        layout.addWidget(add_btn)

        dialog.exec()

    def add_argument(self, name, default, description, dialog):
        arg_config = {
            "name": name,
            "default": default,
            "description": description
        }

        item = QTreeWidgetItem(self.tree)
        item.setText(0, name)
        item.setText(1, "Argument")
        item.setText(2, f"default: {default}")
        item.setData(0, Qt.ItemDataRole.UserRole, arg_config)

        self.update_launch_config()
        dialog.accept()

    def show_context_menu(self, position):
        item = self.tree.itemAt(position)
        if not item:
            return

        menu = QMenu()
        delete_action = menu.addAction("Delete")
        edit_action = menu.addAction("Edit")
        
        action = menu.exec(self.tree.viewport().mapToGlobal(position))
        
        if action == delete_action:
            self.delete_item(item)
        elif action == edit_action:
            self.edit_item(item)

    def delete_item(self, item):
        self.tree.takeTopLevelItem(self.tree.indexOfTopLevelItem(item))
        self.update_launch_config()

    def edit_item(self, item):
        item_type = item.text(1)
        if item_type == "Node":
            self.show_edit_node_dialog(item)
        elif item_type == "Parameter":
            self.show_edit_param_dialog(item)
        elif item_type == "Argument":
            self.show_edit_arg_dialog(item)

    def update_launch_config(self):
        config = {
            "nodes": [],
            "parameters": [],
            "arguments": []
        }

        for i in range(self.tree.topLevelItemCount()):
            item = self.tree.topLevelItem(i)
            item_data = item.data(0, Qt.ItemDataRole.UserRole)
            item_type = item.text(1)

            if "Node" in item_type:
                config["nodes"].append(item_data)
            elif item_type == "Parameter":
                config["parameters"].append(item_data)
            elif item_type == "Argument":
                config["arguments"].append(item_data)

        self.launch_config = config
        self.launch_updated.emit(config)

    def generate_launch_file(self):
        # This method will be connected to the launch file generator
        self.launch_updated.emit(self.launch_config) 