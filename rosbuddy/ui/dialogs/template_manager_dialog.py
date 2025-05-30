"""Template manager dialog with version management."""

from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QTreeWidget,
                           QTreeWidgetItem, QPushButton, QLabel, QLineEdit,
                           QFileDialog, QMessageBox, QMenu, QInputDialog)
from PyQt6.QtCore import Qt, pyqtSignal
from typing import Dict, Any, Optional

from ..widgets.template_manager import TemplateManager
from .template_version_dialog import TemplateVersionDialog

class TemplateManagerDialog(QDialog):
    """Dialog for managing node templates."""
    
    template_selected = pyqtSignal(dict)  # Emits selected template
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Manage Templates")
        self.setMinimumWidth(900)
        self.setMinimumHeight(600)
        
        self.template_manager = TemplateManager()
        self.init_ui()
        
        # Connect template manager signals
        self.template_manager.templates_changed.connect(self.refresh_tree)
        self.template_manager.sync_status_changed.connect(self.show_sync_status)
    
    def init_ui(self):
        """Initialize the dialog UI."""
        layout = QVBoxLayout(self)
        
        # Search bar
        search_layout = QHBoxLayout()
        search_label = QLabel("Search:")
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search templates...")
        self.search_input.textChanged.connect(self.filter_templates)
        search_layout.addWidget(search_label)
        search_layout.addWidget(self.search_input)
        layout.addLayout(search_layout)
        
        # Template tree
        self.tree = QTreeWidget()
        self.tree.setHeaderLabels(["Name", "Type", "Topic", "Category", "Version"])
        self.tree.setColumnWidth(0, 250)  # Name column
        self.tree.setColumnWidth(1, 100)  # Type column
        self.tree.setColumnWidth(2, 200)  # Topic column
        self.tree.setColumnWidth(3, 100)  # Category column
        self.tree.setColumnWidth(4, 70)   # Version column
        self.tree.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.tree.customContextMenuRequested.connect(self.show_context_menu)
        layout.addWidget(self.tree)
        
        # Sync status
        self.sync_status_label = QLabel()
        layout.addWidget(self.sync_status_label)
        
        # Buttons layout
        button_layout = QHBoxLayout()
        
        # Left side buttons
        left_buttons = QHBoxLayout()
        self.add_category_btn = QPushButton("Add Category")
        self.add_category_btn.clicked.connect(self.add_category)
        left_buttons.addWidget(self.add_category_btn)
        
        # Center buttons
        center_buttons = QHBoxLayout()
        self.sync_btn = QPushButton("Sync with Team")
        self.sync_btn.clicked.connect(self.template_manager.sync_with_team)
        center_buttons.addWidget(self.sync_btn)
        
        # Right side buttons
        right_buttons = QHBoxLayout()
        self.import_btn = QPushButton("Import...")
        self.import_btn.clicked.connect(self.import_templates)
        self.export_btn = QPushButton("Export...")
        self.export_btn.clicked.connect(self.export_templates)
        right_buttons.addWidget(self.import_btn)
        right_buttons.addWidget(self.export_btn)
        
        # Add button layouts with stretch
        button_layout.addLayout(left_buttons)
        button_layout.addStretch()
        button_layout.addLayout(center_buttons)
        button_layout.addStretch()
        button_layout.addLayout(right_buttons)
        
        layout.addLayout(button_layout)
        
        # Initial population
        self.refresh_tree()
    
    def refresh_tree(self):
        """Refresh the template tree."""
        self.tree.clear()
        
        # Add user template categories
        for category in self.template_manager.get_categories():
            category_item = QTreeWidgetItem([category])
            category_item.setFlags(category_item.flags() & ~Qt.ItemFlag.ItemIsSelectable)
            self.tree.addTopLevelItem(category_item)
            
            # Add templates in this category
            for template in self.template_manager.get_templates_in_category(category):
                template_item = QTreeWidgetItem([
                    template["name"],
                    template["type"],
                    template["topic"],
                    category,
                    str(template.get("metadata", {}).get("version", 1))
                ])
                template_item.setData(0, Qt.ItemDataRole.UserRole, template)
                
                # Set tooltip with description and metadata
                tooltip = self._build_template_tooltip(template)
                template_item.setToolTip(0, tooltip)
                
                category_item.addChild(template_item)
        
        self.tree.expandAll()
    
    def _build_template_tooltip(self, template: Dict[str, Any]) -> str:
        """Build detailed tooltip for a template."""
        tooltip = f"""<b>{template['name']}</b> ({template['type']})
Topic: {template['topic']}
Type: {template['msg_type']}"""
        
        metadata = template.get("metadata", {})
        if metadata:
            tooltip += f"""
Version: {metadata.get('version', 1)}
Author: {metadata.get('author', 'unknown')}
Modified: {metadata.get('modified', 'unknown')}"""
        
        if "description" in template:
            tooltip += f"\n\n{template['description']}"
        
        return tooltip
    
    def filter_templates(self):
        """Filter templates based on search text."""
        search_text = self.search_input.text().lower()
        
        if not search_text:
            self.refresh_tree()
            return
        
        # Search for matching templates
        results = self.template_manager.search_templates(search_text)
        
        # Clear and show results
        self.tree.clear()
        
        # Group results by category
        by_category = {}
        for template in results:
            category = template["category"]
            if category not in by_category:
                by_category[category] = []
            by_category[category].append(template)
        
        # Add results to tree
        for category, templates in by_category.items():
            category_item = QTreeWidgetItem([category])
            category_item.setFlags(category_item.flags() & ~Qt.ItemFlag.ItemIsSelectable)
            self.tree.addTopLevelItem(category_item)
            
            for template in templates:
                template_item = QTreeWidgetItem([
                    template["name"],
                    template["type"],
                    template["topic"],
                    category,
                    str(template.get("metadata", {}).get("version", 1))
                ])
                template_item.setData(0, Qt.ItemDataRole.UserRole, template)
                
                tooltip = self._build_template_tooltip(template)
                template_item.setToolTip(0, tooltip)
                
                category_item.addChild(template_item)
        
        self.tree.expandAll()
    
    def show_context_menu(self, position):
        """Show context menu for template/category management."""
        item = self.tree.itemAt(position)
        if not item:
            return
        
        menu = QMenu()
        
        if item.parent() is None:
            # Category item
            category = item.text(0)
            if category not in ["Custom", "Favorites", "Team"]:  # Protect default categories
                remove_category = menu.addAction("Remove Category")
                remove_category.triggered.connect(
                    lambda: self.remove_category(category))
        else:
            # Template item
            template = item.data(0, Qt.ItemDataRole.UserRole)
            category = item.parent().text(0)
            
            use_template = menu.addAction("Use Template")
            use_template.triggered.connect(
                lambda: self.use_template(template))
            
            # Version management
            version_action = menu.addAction("Manage Versions...")
            version_action.triggered.connect(
                lambda: self.show_version_dialog(template, category))
            
            if category != "Favorites":
                add_to_favorites = menu.addAction("Add to Favorites")
                add_to_favorites.triggered.connect(
                    lambda: self.add_to_favorites(template))
            else:
                remove_from_favorites = menu.addAction("Remove from Favorites")
                remove_from_favorites.triggered.connect(
                    lambda: self.remove_from_favorites(template["name"]))
            
            if category == "Custom":
                remove_template = menu.addAction("Remove Template")
                remove_template.triggered.connect(
                    lambda: self.remove_template(category, template["name"]))
            
            if category != "Team":
                publish_action = menu.addAction("Publish to Team")
                publish_action.triggered.connect(
                    lambda: self.publish_template(template))
        
        if menu.actions():
            menu.exec(self.tree.viewport().mapToGlobal(position))
    
    def show_version_dialog(self, template: Dict[str, Any], category: str):
        """Show the template version management dialog."""
        dialog = TemplateVersionDialog(template, category, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.refresh_tree()
    
    def publish_template(self, template: Dict[str, Any]):
        """Publish a template to the team directory."""
        if self.template_manager.publish_to_team(template):
            QMessageBox.information(
                self,
                "Publish Successful",
                f"Template '{template['name']}' published to team directory"
            )
        else:
            QMessageBox.warning(
                self,
                "Publish Failed",
                "Failed to publish template. Please check team directory configuration."
            )
    
    def show_sync_status(self, status: str):
        """Show sync status message."""
        self.sync_status_label.setText(status)
    
    def add_category(self):
        """Add a new template category."""
        category, ok = QInputDialog.getText(
            self, "Add Category", "Enter category name:")
        
        if ok and category:
            if category in self.template_manager.get_categories():
                QMessageBox.warning(
                    self,
                    "Category Exists",
                    f"Category '{category}' already exists."
                )
                return
            
            self.template_manager.add_category(category)
    
    def remove_category(self, category: str):
        """Remove a template category."""
        reply = QMessageBox.question(
            self,
            "Remove Category",
            f"Are you sure you want to remove the category '{category}' "
            "and all its templates?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self.template_manager.remove_category(category)
    
    def remove_template(self, category: str, template_name: str):
        """Remove a template."""
        reply = QMessageBox.question(
            self,
            "Remove Template",
            f"Are you sure you want to remove the template '{template_name}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self.template_manager.remove_template(category, template_name)
    
    def add_to_favorites(self, template: Dict[str, Any]):
        """Add a template to favorites."""
        self.template_manager.add_to_favorites(template)
    
    def remove_from_favorites(self, template_name: str):
        """Remove a template from favorites."""
        self.template_manager.remove_from_favorites(template_name)
    
    def use_template(self, template: Dict[str, Any]):
        """Use the selected template."""
        self.template_selected.emit(template)
        self.accept()
    
    def import_templates(self):
        """Import templates from a JSON file."""
        filepath, _ = QFileDialog.getOpenFileName(
            self,
            "Import Templates",
            "",
            "JSON Files (*.json)"
        )
        
        if filepath:
            try:
                self.template_manager.import_templates(filepath)
                QMessageBox.information(
                    self,
                    "Import Successful",
                    "Templates imported successfully."
                )
            except Exception as e:
                QMessageBox.critical(
                    self,
                    "Import Error",
                    f"Error importing templates: {str(e)}"
                )
    
    def export_templates(self):
        """Export templates to a JSON file."""
        filepath, _ = QFileDialog.getSaveFileName(
            self,
            "Export Templates",
            "",
            "JSON Files (*.json)"
        )
        
        if filepath:
            try:
                self.template_manager.export_templates(filepath)
                QMessageBox.information(
                    self,
                    "Export Successful",
                    "Templates exported successfully."
                )
            except Exception as e:
                QMessageBox.critical(
                    self,
                    "Export Error",
                    f"Error exporting templates: {str(e)}"
                ) 