from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QFormLayout, QLineEdit,
                           QComboBox, QPushButton, QLabel, QFileDialog,
                           QGroupBox, QTextEdit, QMessageBox)
from PyQt6.QtCore import Qt
import os
from ...code_generation.code_generator import CodeGenerator

class CodeGenerationDialog(QDialog):
    """Dialog for configuring and generating ROS 2 packages."""
    
    # Common licenses for ROS packages
    LICENSES = [
        "Apache-2.0",
        "MIT",
        "BSD-3-Clause",
        "GPL-3.0",
        "LGPL-3.0"
    ]
    
    def __init__(self, nodes, parent=None):
        super().__init__(parent)
        self.nodes = nodes
        self.code_generator = CodeGenerator()
        self.init_ui()
    
    def init_ui(self):
        """Initialize the dialog UI."""
        self.setWindowTitle("Generate ROS 2 Package")
        self.setMinimumWidth(600)
        
        layout = QVBoxLayout(self)
        layout.setSpacing(20)
        
        # Package information
        pkg_group = QGroupBox("Package Information")
        pkg_layout = QFormLayout(pkg_group)
        
        # Package name
        self.pkg_name = QLineEdit()
        self.pkg_name.setPlaceholderText("my_ros_package")
        pkg_layout.addRow("Package Name:", self.pkg_name)
        
        # Package description
        self.description = QTextEdit()
        self.description.setPlaceholderText("A brief description of your package...")
        self.description.setMaximumHeight(60)
        pkg_layout.addRow("Description:", self.description)
        
        # Maintainer info
        self.maintainer = QLineEdit()
        self.maintainer.setPlaceholderText("Your Name")
        pkg_layout.addRow("Maintainer:", self.maintainer)
        
        self.email = QLineEdit()
        self.email.setPlaceholderText("your.email@example.com")
        pkg_layout.addRow("Email:", self.email)
        
        # License selection
        self.license = QComboBox()
        self.license.addItems(self.LICENSES)
        self.license.setCurrentText("Apache-2.0")
        pkg_layout.addRow("License:", self.license)
        
        layout.addWidget(pkg_group)
        
        # Output directory selection
        out_group = QGroupBox("Output Location")
        out_layout = QFormLayout(out_group)
        
        self.out_dir = QLineEdit()
        self.out_dir.setReadOnly(True)
        
        browse_btn = QPushButton("Browse...")
        browse_btn.clicked.connect(self._browse_output)
        
        out_layout.addRow("Output Directory:", self.out_dir)
        out_layout.addRow("", browse_btn)
        
        layout.addWidget(out_group)
        
        # Node summary
        summary_group = QGroupBox("Node Summary")
        summary_layout = QVBoxLayout(summary_group)
        
        summary_text = []
        for node in self.nodes:
            summary_text.append(
                f"• {node['name']} ({node['type']})\n"
                f"  Topic: {node['topic']}\n"
                f"  Type: {node['msg_type']}"
            )
        
        summary = QLabel("\n\n".join(summary_text))
        summary.setWordWrap(True)
        summary_layout.addWidget(summary)
        
        layout.addWidget(summary_group)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        
        generate_btn = QPushButton("Generate Package")
        generate_btn.setDefault(True)
        generate_btn.clicked.connect(self._generate_package)
        
        button_layout.addWidget(cancel_btn)
        button_layout.addWidget(generate_btn)
        
        layout.addLayout(button_layout)
    
    def _browse_output(self):
        """Open directory selection dialog."""
        directory = QFileDialog.getExistingDirectory(
            self,
            "Select Output Directory",
            os.path.expanduser("~"),
            QFileDialog.Option.ShowDirsOnly
        )
        if directory:
            self.out_dir.setText(directory)
    
    def _validate_inputs(self) -> list:
        """Validate user inputs."""
        errors = []
        
        # Check package name
        pkg_name = self.pkg_name.text().strip()
        if not self.code_generator.validate_package_name(pkg_name):
            errors.append(
                "Invalid package name. Use only lowercase letters, "
                "numbers, and underscores. Must start with a letter."
            )
        
        # Check maintainer info
        if not self.maintainer.text().strip():
            errors.append("Maintainer name is required.")
        
        if not self.email.text().strip():
            errors.append("Maintainer email is required.")
        elif "@" not in self.email.text():
            errors.append("Invalid email address.")
        
        # Check output directory
        if not self.out_dir.text():
            errors.append("Output directory is required.")
        elif not os.path.isdir(self.out_dir.text()):
            errors.append("Invalid output directory.")
        
        # Validate node configurations
        for node in self.nodes:
            node_errors = self.code_generator.validate_node_config(node)
            if node_errors:
                errors.extend([
                    f"Node '{node['name']}': {error}"
                    for error in node_errors
                ])
        
        return errors
    
    def _generate_package(self):
        """Generate the ROS 2 package."""
        # Validate inputs
        errors = self._validate_inputs()
        if errors:
            QMessageBox.warning(
                self,
                "Validation Error",
                "Please correct the following errors:\n\n" + 
                "\n".join(f"• {error}" for error in errors)
            )
            return
        
        try:
            # Generate package
            self.code_generator.generate_package(
                package_name=self.pkg_name.text().strip(),
                nodes=self.nodes,
                output_dir=self.out_dir.text(),
                maintainer=self.maintainer.text().strip(),
                maintainer_email=self.email.text().strip(),
                description=self.description.toPlainText().strip(),
                license=self.license.currentText()
            )
            
            QMessageBox.information(
                self,
                "Success",
                f"Package '{self.pkg_name.text()}' has been generated successfully!"
            )
            
            self.accept()
            
        except Exception as e:
            QMessageBox.critical(
                self,
                "Error",
                f"Failed to generate package:\n\n{str(e)}"
            ) 