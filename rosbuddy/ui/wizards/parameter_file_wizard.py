# rosbuddy/ui/wizards/parameter_file_wizard.py
import pathlib
import logging
import yaml
from typing import Dict, Any, List, Optional, Union

from PyQt6.QtWidgets import (
    QWizard, QWizardPage, QVBoxLayout, QHBoxLayout, QFormLayout, QGridLayout,
    QLabel, QLineEdit, QPushButton, QComboBox, QTextEdit, QSplitter,
    QTreeWidget, QTreeWidgetItem, QGroupBox, QSpinBox, QDoubleSpinBox,
    QCheckBox, QMessageBox, QFileDialog, QScrollArea, QFrame, QDialog,
    QDialogButtonBox, QInputDialog, QWidget
)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer
from PyQt6.QtGui import QFont, QSyntaxHighlighter, QTextCharFormat, QColor

logger = logging.getLogger(__name__)

class YamlPreviewHighlighter(QSyntaxHighlighter):
    """Simple YAML syntax highlighter for the preview pane."""
    
    def __init__(self, document):
        super().__init__(document)
        self.setup_formats()
        
    def setup_formats(self):
        # Key format
        self.key_format = QTextCharFormat()
        self.key_format.setForeground(QColor("#9CDCFE"))
        self.key_format.setFontWeight(QFont.Weight.Bold)
        
        # String format
        self.string_format = QTextCharFormat()
        self.string_format.setForeground(QColor("#CE9178"))
        
        # Number format
        self.number_format = QTextCharFormat()
        self.number_format.setForeground(QColor("#B5CEA8"))
        
        # Boolean format
        self.bool_format = QTextCharFormat()
        self.bool_format.setForeground(QColor("#569CD6"))
        
        # Comment format
        self.comment_format = QTextCharFormat()
        self.comment_format.setForeground(QColor("#6A9955"))
        
    def highlightBlock(self, text):
        import re
        
        # Comments
        comment_match = re.search(r'#.*$', text)
        if comment_match:
            self.setFormat(comment_match.start(), len(comment_match.group()), self.comment_format)
        
        # Keys (word followed by colon)
        key_matches = re.finditer(r'^\s*([a-zA-Z_][a-zA-Z0-9_]*)\s*:', text)
        for match in key_matches:
            self.setFormat(match.start(1), len(match.group(1)), self.key_format)
        
        # Strings
        string_matches = re.finditer(r'"[^"]*"|\'[^\']*\'', text)
        for match in string_matches:
            self.setFormat(match.start(), len(match.group()), self.string_format)
        
        # Numbers
        number_matches = re.finditer(r'\b\d+\.?\d*\b', text)
        for match in number_matches:
            self.setFormat(match.start(), len(match.group()), self.number_format)
        
        # Booleans
        bool_matches = re.finditer(r'\b(true|false|True|False|yes|no|Yes|No)\b', text)
        for match in bool_matches:
            self.setFormat(match.start(), len(match.group()), self.bool_format)

class LocationNamePage(QWizardPage):
    """First page: Select location and file name."""
    
    def __init__(self, workspace_manager, parent=None):
        super().__init__(parent)
        self.workspace_manager = workspace_manager
        self.setTitle("Parameter File Location & Name")
        self.setSubTitle("Choose where to create the parameter file and give it a name.")
        
        layout = QVBoxLayout()
        
        # Location selection
        location_group = QGroupBox("Location")
        location_layout = QFormLayout()
        
        self.location_combo = QComboBox()
        self.populate_locations()
        location_layout.addRow("Package:", self.location_combo)
        
        self.custom_path_edit = QLineEdit()
        self.custom_path_edit.setPlaceholderText("Or enter custom path...")
        browse_btn = QPushButton("Browse...")
        browse_btn.clicked.connect(self.browse_location)
        
        custom_layout = QHBoxLayout()
        custom_layout.addWidget(self.custom_path_edit)
        custom_layout.addWidget(browse_btn)
        location_layout.addRow("Custom:", custom_layout)
        
        location_group.setLayout(location_layout)
        layout.addWidget(location_group)
        
        # File name
        name_group = QGroupBox("File Name")
        name_layout = QFormLayout()
        
        self.filename_edit = QLineEdit("params.yaml")
        name_layout.addRow("File Name:", self.filename_edit)
        
        self.description_edit = QLineEdit()
        self.description_edit.setPlaceholderText("Optional description for the parameter file")
        name_layout.addRow("Description:", self.description_edit)
        
        name_group.setLayout(name_layout)
        layout.addWidget(name_group)
        
        layout.addStretch()
        self.setLayout(layout)
        
        # Register fields
        self.registerField("location", self.location_combo, "currentText")
        self.registerField("custom_path", self.custom_path_edit)
        self.registerField("filename*", self.filename_edit)
        self.registerField("description", self.description_edit)
        
    def populate_locations(self):
        """Populate location combo with available packages."""
        self.location_combo.addItem("workspace/config", "workspace")
        
        # Add packages if workspace is available
        try:
            from ...core_logic.package_discovery import PackageDiscovery
            package_discovery = PackageDiscovery(self.workspace_manager)
            packages = package_discovery.find_packages_in_active_workspace()
            
            for pkg in packages:
                self.location_combo.addItem(f"{pkg.name}/config", pkg.path)
        except Exception as e:
            logger.warning(f"Could not load packages: {e}")
            
    def browse_location(self):
        """Browse for custom location."""
        workspace_path = self.workspace_manager.get_active_workspace_path()
        start_dir = str(workspace_path) if workspace_path else str(pathlib.Path.home())
        
        directory = QFileDialog.getExistingDirectory(
            self, "Select Directory", start_dir
        )
        if directory:
            self.custom_path_edit.setText(directory)
            
    def get_target_path(self):
        """Get the target directory path."""
        if self.custom_path_edit.text():
            return pathlib.Path(self.custom_path_edit.text())
        
        location_data = self.location_combo.currentData()
        if location_data == "workspace":
            workspace_path = self.workspace_manager.get_active_workspace_path()
            return workspace_path / "config" if workspace_path else None
        else:
            return pathlib.Path(location_data) / "config"

class ParameterDefinitionPage(QWizardPage):
    """Second page: Define parameters with UI."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setTitle("Define Parameters")
        self.setSubTitle("Add and configure parameters for your ROS 2 nodes.")
        
        self.parameters = {}  # Store parameter definitions
        
        main_layout = QHBoxLayout()
        
        # Left side: Parameter definition UI
        left_widget = QFrame()
        left_layout = QVBoxLayout(left_widget)
        
        # Node namespace selection
        namespace_group = QGroupBox("Node Namespace")
        namespace_layout = QFormLayout()
        
        self.namespace_edit = QLineEdit("/")
        self.namespace_edit.setPlaceholderText("e.g., /robot1, /sensors")
        namespace_layout.addRow("Namespace:", self.namespace_edit)
        
        namespace_group.setLayout(namespace_layout)
        left_layout.addWidget(namespace_group)
        
        # Parameter tree
        tree_group = QGroupBox("Parameters")
        tree_layout = QVBoxLayout()
        
        # Toolbar
        toolbar_layout = QHBoxLayout()
        self.add_param_btn = QPushButton("Add Parameter")
        self.add_group_btn = QPushButton("Add Group")
        self.remove_btn = QPushButton("Remove")
        self.remove_btn.setEnabled(False)
        
        self.add_param_btn.clicked.connect(self.add_parameter)
        self.add_group_btn.clicked.connect(self.add_group)
        self.remove_btn.clicked.connect(self.remove_selected)
        
        toolbar_layout.addWidget(self.add_param_btn)
        toolbar_layout.addWidget(self.add_group_btn)
        toolbar_layout.addWidget(self.remove_btn)
        toolbar_layout.addStretch()
        
        tree_layout.addLayout(toolbar_layout)
        
        # Parameter tree
        self.param_tree = QTreeWidget()
        self.param_tree.setHeaderLabels(["Name", "Type", "Value"])
        self.param_tree.itemSelectionChanged.connect(self.on_selection_changed)
        self.param_tree.itemDoubleClicked.connect(self.edit_parameter)
        tree_layout.addWidget(self.param_tree)
        
        tree_group.setLayout(tree_layout)
        left_layout.addWidget(tree_group)
        
        # Right side: YAML preview
        right_widget = QFrame()
        right_layout = QVBoxLayout(right_widget)
        
        preview_group = QGroupBox("YAML Preview")
        preview_layout = QVBoxLayout()
        
        self.preview_text = QTextEdit()
        self.preview_text.setReadOnly(True)
        self.preview_text.setFont(QFont("Consolas", 10))
        
        # Add syntax highlighting
        self.highlighter = YamlPreviewHighlighter(self.preview_text.document())
        
        preview_layout.addWidget(self.preview_text)
        preview_group.setLayout(preview_layout)
        right_layout.addWidget(preview_group)
        
        # Splitter
        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.addWidget(left_widget)
        splitter.addWidget(right_widget)
        splitter.setSizes([500, 400])
        
        main_layout.addWidget(splitter)
        self.setLayout(main_layout)
        
        # Update preview timer
        self.update_timer = QTimer()
        self.update_timer.setSingleShot(True)
        self.update_timer.timeout.connect(self.update_preview)
        
        # Initial update
        self.update_preview()
        
    def on_selection_changed(self):
        """Handle selection changes."""
        selected = self.param_tree.selectedItems()
        self.remove_btn.setEnabled(len(selected) > 0)
        
    def add_parameter(self):
        """Add a new parameter."""
        dialog = ParameterEditDialog(self)
        if dialog.exec() == dialog.DialogCode.Accepted:
            param_data = dialog.get_parameter_data()
            
            # Add to tree
            item = QTreeWidgetItem([
                param_data['name'],
                param_data['type'],
                str(param_data['value'])
            ])
            item.setData(0, Qt.ItemDataRole.UserRole, param_data)
            
            selected = self.param_tree.selectedItems()
            if selected and selected[0].data(0, Qt.ItemDataRole.UserRole) is None:
                # Add to group
                selected[0].addChild(item)
            else:
                # Add to root
                self.param_tree.addTopLevelItem(item)
                
            self.update_preview()
            
    def add_group(self):
        """Add a parameter group."""
        group_name, ok = QInputDialog.getText(self, "New Group", "Group name:")
        if ok and group_name:
            item = QTreeWidgetItem([group_name, "group", ""])
            item.setData(0, Qt.ItemDataRole.UserRole, None)  # Mark as group
            self.param_tree.addTopLevelItem(item)
            self.update_preview()
            
    def remove_selected(self):
        """Remove selected parameter or group."""
        selected = self.param_tree.selectedItems()
        for item in selected:
            parent = item.parent()
            if parent:
                parent.removeChild(item)
            else:
                self.param_tree.takeTopLevelItem(
                    self.param_tree.indexOfTopLevelItem(item)
                )
        self.update_preview()
        
    def edit_parameter(self, item, column):
        """Edit parameter on double-click."""
        param_data = item.data(0, Qt.ItemDataRole.UserRole)
        if param_data is not None:  # Not a group
            dialog = ParameterEditDialog(self, param_data)
            if dialog.exec() == dialog.DialogCode.Accepted:
                new_data = dialog.get_parameter_data()
                item.setText(0, new_data['name'])
                item.setText(1, new_data['type'])
                item.setText(2, str(new_data['value']))
                item.setData(0, Qt.ItemDataRole.UserRole, new_data)
                self.update_preview()
                
    def update_preview(self):
        """Update the YAML preview."""
        try:
            yaml_data = self.build_yaml_structure()
            yaml_text = yaml.dump(yaml_data, default_flow_style=False, sort_keys=False)
            self.preview_text.setPlainText(yaml_text)
        except Exception as e:
            self.preview_text.setPlainText(f"Error generating YAML: {e}")
            
    def build_yaml_structure(self):
        """Build YAML structure from parameter tree."""
        namespace = self.namespace_edit.text().strip() or "/"
        if not namespace.startswith("/"):
            namespace = "/" + namespace
        if not namespace.endswith("/"):
            namespace += "/"
            
        yaml_data = {namespace + "**": {"ros__parameters": {}}}
        params = yaml_data[namespace + "**"]["ros__parameters"]
        
        def process_item(item, target_dict):
            param_data = item.data(0, Qt.ItemDataRole.UserRole)
            if param_data is None:  # Group
                group_name = item.text(0)
                target_dict[group_name] = {}
                for i in range(item.childCount()):
                    process_item(item.child(i), target_dict[group_name])
            else:  # Parameter
                target_dict[param_data['name']] = param_data['value']
        
        for i in range(self.param_tree.topLevelItemCount()):
            process_item(self.param_tree.topLevelItem(i), params)
            
        return yaml_data
        
    def get_yaml_content(self):
        """Get the final YAML content."""
        yaml_data = self.build_yaml_structure()
        return yaml.dump(yaml_data, default_flow_style=False, sort_keys=False)

class ParameterEditDialog(QDialog):
    """Dialog for editing a single parameter."""
    
    def __init__(self, parent=None, param_data=None):
        super().__init__(parent)
        self.setWindowTitle("Edit Parameter")
        self.setModal(True)
        self.resize(400, 300)
        
        layout = QVBoxLayout()
        
        # Parameter details
        form_layout = QFormLayout()
        
        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("parameter_name")
        form_layout.addRow("Name:", self.name_edit)
        
        self.type_combo = QComboBox()
        self.type_combo.addItems(["string", "int", "double", "bool", "string_array", "int_array", "double_array"])
        self.type_combo.currentTextChanged.connect(self.on_type_changed)
        form_layout.addRow("Type:", self.type_combo)
        
        # Value editors (will be switched based on type)
        self.value_widget = QWidget()
        self.value_layout = QVBoxLayout(self.value_widget)
        
        self.string_edit = QLineEdit()
        self.int_spin = QSpinBox()
        self.int_spin.setRange(-2147483648, 2147483647)
        self.double_spin = QDoubleSpinBox()
        self.double_spin.setRange(float('-inf'), float('inf'))
        self.double_spin.setDecimals(6)
        self.bool_check = QCheckBox("True")
        self.array_edit = QTextEdit()
        self.array_edit.setMaximumHeight(100)
        
        form_layout.addRow("Value:", self.value_widget)
        
        layout.addLayout(form_layout)
        
        # Description
        self.desc_edit = QTextEdit()
        self.desc_edit.setMaximumHeight(80)
        self.desc_edit.setPlaceholderText("Optional parameter description...")
        layout.addWidget(QLabel("Description:"))
        layout.addWidget(self.desc_edit)
        
        # Buttons
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)
        
        self.setLayout(layout)
        
        # Initialize with data if provided
        if param_data:
            self.name_edit.setText(param_data['name'])
            self.type_combo.setCurrentText(param_data['type'])
            self.set_value(param_data['value'])
            if 'description' in param_data:
                self.desc_edit.setPlainText(param_data['description'])
        
        self.on_type_changed(self.type_combo.currentText())
        
    def on_type_changed(self, type_name):
        """Handle type selection change."""
        # Clear layout
        while self.value_layout.count():
            child = self.value_layout.takeAt(0)
            if child.widget():
                child.widget().hide()
        
        # Add appropriate widget
        if type_name == "string":
            self.value_layout.addWidget(self.string_edit)
            self.string_edit.show()
        elif type_name == "int":
            self.value_layout.addWidget(self.int_spin)
            self.int_spin.show()
        elif type_name == "double":
            self.value_layout.addWidget(self.double_spin)
            self.double_spin.show()
        elif type_name == "bool":
            self.value_layout.addWidget(self.bool_check)
            self.bool_check.show()
        elif type_name.endswith("_array"):
            self.array_edit.setPlaceholderText(f"Enter {type_name} values, one per line")
            self.value_layout.addWidget(self.array_edit)
            self.array_edit.show()
            
    def set_value(self, value):
        """Set the value in the appropriate widget."""
        type_name = self.type_combo.currentText()
        
        if type_name == "string":
            self.string_edit.setText(str(value))
        elif type_name == "int":
            self.int_spin.setValue(int(value))
        elif type_name == "double":
            self.double_spin.setValue(float(value))
        elif type_name == "bool":
            self.bool_check.setChecked(bool(value))
        elif type_name.endswith("_array"):
            if isinstance(value, list):
                self.array_edit.setPlainText('\n'.join(map(str, value)))
            else:
                self.array_edit.setPlainText(str(value))
                
    def get_parameter_data(self):
        """Get the parameter data from the dialog."""
        type_name = self.type_combo.currentText()
        
        # Get value based on type
        if type_name == "string":
            value = self.string_edit.text()
        elif type_name == "int":
            value = self.int_spin.value()
        elif type_name == "double":
            value = self.double_spin.value()
        elif type_name == "bool":
            value = self.bool_check.isChecked()
        elif type_name == "string_array":
            lines = self.array_edit.toPlainText().strip().split('\n')
            value = [line.strip() for line in lines if line.strip()]
        elif type_name == "int_array":
            lines = self.array_edit.toPlainText().strip().split('\n')
            value = [int(line.strip()) for line in lines if line.strip()]
        elif type_name == "double_array":
            lines = self.array_edit.toPlainText().strip().split('\n')
            value = [float(line.strip()) for line in lines if line.strip()]
        else:
            value = None
            
        return {
            'name': self.name_edit.text(),
            'type': type_name,
            'value': value,
            'description': self.desc_edit.toPlainText().strip()
        }

class SummaryPage(QWizardPage):
    """Final page: Summary and generate."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setTitle("Summary & Generate")
        self.setSubTitle("Review your parameter file configuration and generate.")
        
        layout = QVBoxLayout()
        
        # Summary
        self.summary_text = QTextEdit()
        self.summary_text.setReadOnly(True)
        self.summary_text.setMaximumHeight(200)
        layout.addWidget(QLabel("Summary:"))
        layout.addWidget(self.summary_text)
        
        # Full YAML preview
        self.yaml_preview = QTextEdit()
        self.yaml_preview.setReadOnly(True)
        self.yaml_preview.setFont(QFont("Consolas", 10))
        layout.addWidget(QLabel("Generated YAML:"))
        layout.addWidget(self.yaml_preview)
        
        self.setLayout(layout)
        
    def initializePage(self):
        """Initialize the page with data from previous pages."""
        wizard = self.wizard()
        
        # Get data from previous pages
        location_page = wizard.page(0)
        param_page = wizard.page(1)
        
        target_path = location_page.get_target_path()
        filename = wizard.field("filename")
        
        # Update summary
        summary = f"""
Target Directory: {target_path}
File Name: {filename}
Description: {wizard.field("description") or "None"}
"""
        self.summary_text.setPlainText(summary.strip())
        
        # Update YAML preview
        yaml_content = param_page.get_yaml_content()
        self.yaml_preview.setPlainText(yaml_content)

class ParameterFileWizard(QWizard):
    """Main wizard for creating parameter files."""
    
    parameter_file_created = pyqtSignal(str)  # Emit file path when created
    
    def __init__(self, workspace_manager, parent=None):
        super().__init__(parent)
        self.workspace_manager = workspace_manager
        
        self.setWindowTitle("Create Parameter File")
        self.setWizardStyle(QWizard.WizardStyle.ModernStyle)
        self.setOption(QWizard.WizardOption.HaveHelpButton, False)
        self.setMinimumSize(800, 600)
        
        # Add pages
        self.location_page = LocationNamePage(workspace_manager, self)
        self.param_page = ParameterDefinitionPage(self)
        self.summary_page = SummaryPage(self)
        
        self.addPage(self.location_page)
        self.addPage(self.param_page)
        self.addPage(self.summary_page)
        
        # Connect finish button
        self.finished.connect(self.on_finished)
        
    def on_finished(self, result):
        """Handle wizard completion."""
        if result == QWizard.DialogCode.Accepted:
            try:
                self.create_parameter_file()
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to create parameter file:\n{e}")
                logger.error(f"Parameter file creation failed: {e}")
                
    def create_parameter_file(self):
        """Create the parameter file."""
        # Get target path
        target_path = self.location_page.get_target_path()
        filename = self.field("filename")
        
        if not target_path:
            raise ValueError("No target path specified")
            
        # Ensure target directory exists
        target_path.mkdir(parents=True, exist_ok=True)
        
        # Get YAML content
        yaml_content = self.param_page.get_yaml_content()
        
        # Add description as comment if provided
        description = self.field("description")
        if description:
            yaml_content = f"# {description}\n\n{yaml_content}"
        
        # Write file
        file_path = target_path / filename
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(yaml_content)
        
        logger.info(f"Parameter file created: {file_path}")
        self.parameter_file_created.emit(str(file_path))
        
        QMessageBox.information(
            self, "Success", 
            f"Parameter file created successfully:\n{file_path}"
        )

# Remove the duplicate import at the end
