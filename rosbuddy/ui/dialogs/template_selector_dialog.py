from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QTreeWidget, QTreeWidgetItem,
                           QPushButton, QDialogButtonBox, QLabel, QTextEdit)
from PyQt6.QtCore import Qt
from typing import Optional, Dict, Any

from ..widgets.node_templates import NodeTemplates

class TemplateSelectorDialog(QDialog):
    """Dialog for selecting a node template."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Select Node Template")
        self.setMinimumWidth(800)
        self.setMinimumHeight(600)
        self.selected_template = None
        self.init_ui()
    
    def init_ui(self):
        """Initialize the dialog UI."""
        layout = QVBoxLayout(self)
        
        # Add description label
        description = QLabel(
            "Select a template to quickly create a pre-configured node with "
            "common settings and parameters."
        )
        description.setWordWrap(True)
        layout.addWidget(description)
        
        # Create split layout for tree and details
        tree_layout = QVBoxLayout()
        
        # Create tree widget
        self.tree = QTreeWidget()
        self.tree.setHeaderLabels(["Template", "Type", "Topic"])
        self.tree.setColumnWidth(0, 250)  # Template name column
        self.tree.setColumnWidth(1, 100)  # Node type column
        self.tree.setColumnWidth(2, 200)  # Topic column
        tree_layout.addWidget(self.tree)
        
        # Add details view
        self.details = QTextEdit()
        self.details.setReadOnly(True)
        self.details.setMinimumHeight(150)
        self.details.setStyleSheet("""
            QTextEdit {
                background-color: #f5f5f5;
                border: 1px solid #ddd;
                border-radius: 4px;
                padding: 8px;
            }
        """)
        tree_layout.addWidget(self.details)
        
        layout.addLayout(tree_layout)
        
        # Populate tree with templates
        self.populate_tree()
        
        # Connect selection changed signal
        self.tree.itemSelectionChanged.connect(self.update_details)
        
        # Add buttons
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
        
        # Connect double-click to accept
        self.tree.itemDoubleClicked.connect(self.accept)
    
    def populate_tree(self):
        """Populate the tree with templates."""
        templates = NodeTemplates.get_all_templates()
        
        for category, items in templates.items():
            # Create category item
            category_item = QTreeWidgetItem([category])
            category_item.setFlags(category_item.flags() & ~Qt.ItemFlag.ItemIsSelectable)
            self.tree.addTopLevelItem(category_item)
            
            # Add templates in this category
            for template in items:
                template_item = QTreeWidgetItem([
                    template["name"],
                    template["type"],
                    template["topic"]
                ])
                template_item.setData(0, Qt.ItemDataRole.UserRole, template)
                
                # Set tooltip with description if available
                if "description" in template:
                    template_item.setToolTip(0, template["description"])
                
                category_item.addChild(template_item)
        
        self.tree.expandAll()
    
    def update_details(self):
        """Update the details view with selected template information."""
        items = self.tree.selectedItems()
        if not items:
            self.details.clear()
            return
        
        template = items[0].data(0, Qt.ItemDataRole.UserRole)
        if not template:
            self.details.clear()
            return
        
        # Build detailed description
        details = f"""<h3>{template['name']}</h3>
<p><b>Type:</b> {template['type']}<br>
<b>Topic:</b> {template['topic']}<br>
<b>Message Type:</b> {template['msg_type']}</p>"""
        
        if "description" in template:
            details += f"<p>{template['description']}</p>"
        
        if "qos" in template:
            qos = template["qos"]
            details += f"""<p><b>QoS Profile:</b><br>
• Reliability: {qos['reliability']}<br>
• Durability: {qos['durability']}<br>
• History: {qos['history']['kind']} (depth: {qos['history']['depth']})</p>"""
        
        if "parameters" in template:
            details += "<p><b>Parameters:</b></p><ul>"
            for name, param in template["parameters"].items():
                details += f"<li>{name}: {param['value']} ({param['type']})</li>"
            details += "</ul>"
        
        self.details.setHtml(details)
    
    def get_selected_template(self) -> Optional[Dict[str, Any]]:
        """Get the selected template configuration."""
        items = self.tree.selectedItems()
        if items:
            return items[0].data(0, Qt.ItemDataRole.UserRole)
        return None 