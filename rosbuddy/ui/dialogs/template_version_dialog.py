from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QTableWidget,
                           QTableWidgetItem, QPushButton, QLabel, QFileDialog,
                           QMessageBox, QHeaderView)
from PyQt6.QtCore import Qt, pyqtSignal
from datetime import datetime
from pathlib import Path
from typing import Dict, Any

from ..widgets.template_manager import TemplateManager

class TemplateVersionDialog(QDialog):
    """Dialog for managing template versions and team synchronization."""
    
    version_selected = pyqtSignal(int)  # Emits selected version number
    
    def __init__(self, template: Dict[str, Any], category: str, parent=None):
        super().__init__(parent)
        self.template = template
        self.category = category
        self.template_manager = TemplateManager()
        
        self.setWindowTitle(f"Template Versions - {template['name']}")
        self.setMinimumWidth(800)
        self.setMinimumHeight(500)
        
        self.init_ui()
        
        # Connect template manager signals
        self.template_manager.sync_status_changed.connect(self.update_sync_status)
    
    def init_ui(self):
        """Initialize the dialog UI."""
        layout = QVBoxLayout(self)
        
        # Template info
        info_layout = QHBoxLayout()
        
        # Left side info
        left_info = QVBoxLayout()
        left_info.addWidget(QLabel(f"<b>Name:</b> {self.template['name']}"))
        left_info.addWidget(QLabel(f"<b>Type:</b> {self.template['type']}"))
        left_info.addWidget(QLabel(f"<b>Topic:</b> {self.template['topic']}"))
        info_layout.addLayout(left_info)
        
        # Right side info
        right_info = QVBoxLayout()
        metadata = self.template.get("metadata", {})
        right_info.addWidget(QLabel(f"<b>Current Version:</b> {metadata.get('version', 1)}"))
        right_info.addWidget(QLabel(f"<b>Author:</b> {metadata.get('author', 'unknown')}"))
        right_info.addWidget(QLabel(f"<b>Last Modified:</b> {self._format_date(metadata.get('modified', ''))}"))
        info_layout.addLayout(right_info)
        
        layout.addLayout(info_layout)
        
        # Version history table
        self.version_table = QTableWidget()
        self.version_table.setColumnCount(5)
        self.version_table.setHorizontalHeaderLabels([
            "Version", "Modified", "Author", "Changes", "Actions"
        ])
        self.version_table.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.ResizeToContents)
        layout.addWidget(self.version_table)
        
        # Load versions
        self.load_versions()
        
        # Team sync section
        sync_layout = QVBoxLayout()
        sync_layout.addWidget(QLabel("<b>Team Synchronization</b>"))
        
        # Sync status
        self.sync_status = QLabel("Not synchronized with team")
        sync_layout.addWidget(self.sync_status)
        
        # Sync buttons
        sync_buttons = QHBoxLayout()
        
        self.set_team_dir_btn = QPushButton("Set Team Directory...")
        self.set_team_dir_btn.clicked.connect(self.set_team_directory)
        
        self.sync_btn = QPushButton("Sync with Team")
        self.sync_btn.clicked.connect(self.template_manager.sync_with_team)
        
        self.publish_btn = QPushButton("Publish to Team")
        self.publish_btn.clicked.connect(self.publish_template)
        
        for btn in [self.set_team_dir_btn, self.sync_btn, self.publish_btn]:
            sync_buttons.addWidget(btn)
        
        sync_layout.addLayout(sync_buttons)
        layout.addLayout(sync_layout)
        
        # Dialog buttons
        button_layout = QHBoxLayout()
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.accept)
        button_layout.addStretch()
        button_layout.addWidget(close_btn)
        layout.addLayout(button_layout)
    
    def load_versions(self):
        """Load version history into the table."""
        if "metadata" not in self.template:
            return
        
        template_id = self.template["metadata"]["template_id"]
        versions = self.template_manager.get_template_versions(template_id)
        
        self.version_table.setRowCount(len(versions))
        
        for i, version in enumerate(versions):
            metadata = version.get("metadata", {})
            
            # Version number
            version_item = QTableWidgetItem(str(metadata.get("version", "?")))
            version_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.version_table.setItem(i, 0, version_item)
            
            # Modified date
            modified = self._format_date(metadata.get("modified", ""))
            modified_item = QTableWidgetItem(modified)
            self.version_table.setItem(i, 1, modified_item)
            
            # Author
            author_item = QTableWidgetItem(metadata.get("author", "unknown"))
            self.version_table.setItem(i, 2, author_item)
            
            # Changes
            changes = "Initial version"
            if "reverted_from" in metadata:
                changes = f"Reverted from v{metadata['reverted_from']}"
            changes_item = QTableWidgetItem(changes)
            self.version_table.setItem(i, 3, changes_item)
            
            # Action buttons
            if i < len(versions) - 1:  # Not the oldest version
                revert_btn = QPushButton("Revert to This")
                revert_btn.clicked.connect(
                    lambda checked, v=metadata.get("version", 0):
                    self.revert_to_version(v))
                self.version_table.setCellWidget(i, 4, revert_btn)
    
    def revert_to_version(self, version: int):
        """Revert template to a specific version."""
        reply = QMessageBox.question(
            self,
            "Revert Template",
            f"Are you sure you want to revert to version {version}?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            if self.template_manager.revert_to_version(
                self.category, self.template["name"], version):
                QMessageBox.information(
                    self,
                    "Revert Successful",
                    f"Template reverted to version {version}"
                )
                self.accept()
            else:
                QMessageBox.critical(
                    self,
                    "Revert Failed",
                    "Failed to revert template version"
                )
    
    def set_team_directory(self):
        """Set the team synchronization directory."""
        directory = QFileDialog.getExistingDirectory(
            self,
            "Select Team Directory",
            str(Path.home())
        )
        
        if directory:
            self.template_manager.set_team_sync_dir(Path(directory))
    
    def publish_template(self):
        """Publish the template to the team directory."""
        reply = QMessageBox.question(
            self,
            "Publish Template",
            "Are you sure you want to publish this template to the team?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            if self.template_manager.publish_to_team(self.template):
                QMessageBox.information(
                    self,
                    "Publish Successful",
                    "Template published to team directory"
                )
            else:
                QMessageBox.critical(
                    self,
                    "Publish Failed",
                    "Failed to publish template"
                )
    
    def update_sync_status(self, status: str):
        """Update the sync status label."""
        self.sync_status.setText(status)
    
    def _format_date(self, date_str: str) -> str:
        """Format ISO date string to human-readable format."""
        if not date_str:
            return "Unknown"
        try:
            dt = datetime.fromisoformat(date_str)
            return dt.strftime("%Y-%m-%d %H:%M:%S")
        except ValueError:
            return date_str 