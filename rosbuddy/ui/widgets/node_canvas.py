from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QGraphicsView, QGraphicsScene,
                           QGraphicsItem, QMenu, QInputDialog, QDialog, QFormLayout,
                           QComboBox, QPushButton, QLabel, QSpinBox, QTreeWidget,
                           QTreeWidgetItem, QDialogButtonBox, QLineEdit, QTableWidget,
                           QTableWidgetItem, QHeaderView, QHBoxLayout, QMessageBox)
from PyQt6.QtCore import Qt, QPointF, QRectF, QLineF, pyqtSignal
from PyQt6.QtGui import QPainter, QPen, QBrush, QColor, QPainterPath, QFont
from typing import Dict, Any

class ConnectionItem(QGraphicsItem):
    """A visual connection between nodes."""
    
    def __init__(self, source: 'NodeItem', target: 'NodeItem'):
        super().__init__()
        self.source = source
        self.target = target
        self.setZValue(-1)  # Draw below nodes
        
        # Visual properties
        self.color = QColor("#666666")
        self.width = 2
        
        # Add to scene
        if source.scene():
            source.scene().addItem(self)
    
    def boundingRect(self) -> QRectF:
        """Define the bounding rectangle for the connection."""
        return QRectF(self.source.scenePos(), self.target.scenePos()).normalized()
    
    def paint(self, painter: QPainter, option, widget=None):
        """Paint the connection."""
        if not self.source.scene() or not self.target.scene():
            return
        
        # Get connection points
        source_pos = self.source.scenePos() + QPointF(self.source.width, self.source.height/2)
        target_pos = self.target.scenePos() + QPointF(0, self.target.height/2)
        
        # Draw arrow
        painter.setPen(QPen(self.color, self.width))
        painter.drawLine(QLineF(source_pos, target_pos))
        
        # Draw arrowhead
        angle = QLineF(target_pos, source_pos).angle()
        arrow_size = 10
        arrow_p1 = target_pos + QPointF(
            arrow_size * qCos(angle + 145), -arrow_size * qSin(angle + 145))
        arrow_p2 = target_pos + QPointF(
            arrow_size * qCos(angle - 145), -arrow_size * qSin(angle - 145))
        painter.drawLine(QLineF(target_pos, arrow_p1))
        painter.drawLine(QLineF(target_pos, arrow_p2))

class QosProfileDialog(QDialog):
    """Dialog for configuring QoS profile."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Configure QoS Profile")
        self.init_ui()
    
    def init_ui(self):
        """Initialize the dialog UI."""
        layout = QFormLayout(self)
        
        # Reliability
        self.reliability = QComboBox()
        self.reliability.addItems(["Reliable", "Best Effort"])
        layout.addRow("Reliability:", self.reliability)
        
        # Durability
        self.durability = QComboBox()
        self.durability.addItems(["Volatile", "Transient Local"])
        layout.addRow("Durability:", self.durability)
        
        # History
        self.history = QComboBox()
        self.history.addItems(["Keep Last", "Keep All"])
        layout.addRow("History:", self.history)
        
        # History depth
        self.depth = QSpinBox()
        self.depth.setRange(1, 1000)
        self.depth.setValue(10)
        layout.addRow("History Depth:", self.depth)
        
        # Buttons
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addRow(buttons)
    
    def get_profile(self) -> dict:
        """Get the QoS profile configuration."""
        return {
            "reliability": self.reliability.currentText(),
            "durability": self.durability.currentText(),
            "history": {
                "kind": self.history.currentText(),
                "depth": self.depth.value()
            }
        }

class MessageTypeDialog(QDialog):
    """Dialog for selecting ROS 2 message types."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Select Message Type")
        self.setMinimumWidth(400)
        self.init_ui()
    
    def init_ui(self):
        """Initialize the dialog UI."""
        layout = QVBoxLayout(self)
        
        # Tree widget for message types
        self.tree = QTreeWidget()
        self.tree.setHeaderLabels(["Package/Type"])
        layout.addWidget(self.tree)
        
        # Add common message types
        self.add_common_messages()
        
        # Buttons
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
    
    def add_common_messages(self):
        """Add common ROS 2 message types to the tree."""
        packages = {
            "std_msgs": ["Bool", "String", "Int32", "Float32", "Float64"],
            "geometry_msgs": ["Point", "Pose", "Twist", "Vector3"],
            "sensor_msgs": ["Image", "LaserScan", "PointCloud2", "JointState"],
            "nav_msgs": ["Odometry", "Path", "OccupancyGrid"],
            "action_msgs": ["GoalStatus"],
            "diagnostic_msgs": ["DiagnosticStatus"]
        }
        
        for pkg, types in packages.items():
            pkg_item = QTreeWidgetItem([pkg])
            self.tree.addTopLevelItem(pkg_item)
            for msg_type in types:
                type_item = QTreeWidgetItem([msg_type])
                pkg_item.addChild(type_item)
        
        self.tree.expandAll()
    
    def get_message_type(self) -> str:
        """Get the selected message type."""
        item = self.tree.currentItem()
        if item and item.parent():
            return f"{item.parent().text(0)}/msg/{item.text(0)}"
        return ""

class PortItem(QGraphicsItem):
    """A connection port on a node."""
    
    def __init__(self, parent: 'NodeItem', is_input: bool = False):
        super().__init__(parent)
        self.parent_node = parent
        self.is_input = is_input
        self.radius = 6
        self.setAcceptHoverEvents(True)
        
        # Position relative to parent node
        if is_input:
            self.setPos(0, parent.height/2)
        else:
            self.setPos(parent.width, parent.height/2)
    
    def boundingRect(self) -> QRectF:
        """Define the bounding rectangle for the port."""
        return QRectF(-self.radius, -self.radius,
                     self.radius*2, self.radius*2)
    
    def paint(self, painter: QPainter, option, widget=None):
        """Paint the port."""
        if self.isUnderMouse():
            painter.setBrush(Qt.GlobalColor.yellow)
        else:
            painter.setBrush(Qt.GlobalColor.white)
        painter.setPen(QPen(Qt.GlobalColor.black, 1))
        painter.drawEllipse(self.boundingRect())
    
    def hoverEnterEvent(self, event):
        """Handle hover enter events."""
        self.update()
        super().hoverEnterEvent(event)
    
    def hoverLeaveEvent(self, event):
        """Handle hover leave events."""
        self.update()
        super().hoverLeaveEvent(event)

class ParameterDialog(QDialog):
    """Dialog for configuring node parameters."""
    
    def __init__(self, parameters=None, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Configure Parameters")
        self.setMinimumWidth(500)
        self.parameters = parameters or {}
        self.init_ui()
    
    def init_ui(self):
        """Initialize the dialog UI."""
        layout = QVBoxLayout(self)
        
        # Parameter table
        self.table = QTableWidget(0, 3)
        self.table.setHorizontalHeaderLabels(["Name", "Type", "Value"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self.table)
        
        # Load existing parameters
        for name, param in self.parameters.items():
            self.add_parameter_row(name, param["type"], param["value"])
        
        # Add/Remove buttons
        btn_layout = QHBoxLayout()
        add_btn = QPushButton("Add Parameter")
        add_btn.clicked.connect(self.add_parameter_row)
        remove_btn = QPushButton("Remove Selected")
        remove_btn.clicked.connect(self.remove_selected_row)
        btn_layout.addWidget(add_btn)
        btn_layout.addWidget(remove_btn)
        layout.addLayout(btn_layout)
        
        # Dialog buttons
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
    
    def add_parameter_row(self, name="", param_type="string", value=""):
        """Add a new parameter row to the table."""
        row = self.table.rowCount()
        self.table.insertRow(row)
        
        # Name
        name_item = QTableWidgetItem(name)
        self.table.setItem(row, 0, name_item)
        
        # Type
        type_combo = QComboBox()
        type_combo.addItems(["string", "int", "double", "bool"])
        type_combo.setCurrentText(param_type)
        self.table.setCellWidget(row, 1, type_combo)
        
        # Value
        value_item = QTableWidgetItem(str(value))
        self.table.setItem(row, 2, value_item)
    
    def remove_selected_row(self):
        """Remove the selected row from the table."""
        current_row = self.table.currentRow()
        if current_row >= 0:
            self.table.removeRow(current_row)
    
    def get_parameters(self) -> dict:
        """Get the parameter configuration."""
        parameters = {}
        for row in range(self.table.rowCount()):
            name = self.table.item(row, 0).text().strip()
            if name:  # Only add if name is not empty
                param_type = self.table.cellWidget(row, 1).currentText()
                value = self.table.item(row, 2).text()
                
                # Convert value based on type
                if param_type == "int":
                    try:
                        value = int(value)
                    except ValueError:
                        value = 0
                elif param_type == "double":
                    try:
                        value = float(value)
                    except ValueError:
                        value = 0.0
                elif param_type == "bool":
                    value = value.lower() in ["true", "1", "yes"]
                
                parameters[name] = {
                    "type": param_type,
                    "value": value
                }
        return parameters

class NodeItem(QGraphicsItem):
    """A visual representation of a ROS 2 node."""
    
    def __init__(self, node_type: str, name: str, msg_type: str, topic: str):
        super().__init__()
        self.node_type = node_type
        self.name = name
        self.msg_type = msg_type
        self.topic = topic
        self.qos_profile = None
        self.parameters = {}
        self.namespace = ""
        
        # Visual properties
        self.width = 200
        self.height = 100
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable)
        self.setAcceptHoverEvents(True)
        
        # Colors based on node type
        self.colors = {
            "Publisher": QColor("#4CAF50"),  # Green
            "Subscriber": QColor("#2196F3"), # Blue
            "Service": QColor("#9C27B0"),    # Purple
            "Action": QColor("#FF9800")      # Orange
        }
        
        # Connections
        self.connections = []
        
        # Create ports
        self.input_port = PortItem(self, True) if node_type in ["Subscriber"] else None
        self.output_port = PortItem(self, False) if node_type in ["Publisher"] else None
    
    def boundingRect(self) -> QRectF:
        """Define the bounding rectangle for the node."""
        return QRectF(0, 0, self.width, self.height)
    
    def paint(self, painter: QPainter, option, widget=None):
        """Paint the node item."""
        # Draw node background
        color = self.colors.get(self.node_type, QColor("#757575"))
        if self.isSelected():
            painter.setPen(QPen(Qt.GlobalColor.yellow, 2))
        else:
            painter.setPen(QPen(color.darker(), 1))
        
        # Create gradient background
        gradient = self.create_gradient(color)
        painter.setBrush(QBrush(gradient))
        
        # Draw rounded rectangle
        path = QPainterPath()
        path.addRoundedRect(0, 0, self.width, self.height, 10, 10)
        painter.drawPath(path)
        
        # Draw text
        painter.setPen(Qt.GlobalColor.white)
        font = painter.font()
        font.setBold(True)
        painter.setFont(font)
        
        # Node name and type
        name_text = f"{self.name} ({self.node_type})"
        if self.namespace:
            name_text = f"{self.namespace}/{name_text}"
        painter.drawText(10, 25, name_text)
        
        # Topic and message type
        font.setBold(False)
        painter.setFont(font)
        painter.drawText(10, 45, f"Topic: {self.topic}")
        painter.drawText(10, 65, f"Type: {self.msg_type}")
        
        # Status indicators
        status_y = 85
        if self.qos_profile:
            painter.drawText(10, status_y, "QoS: Custom")
            status_y += 15
        if self.parameters:
            painter.drawText(10, status_y, f"Parameters: {len(self.parameters)}")
    
    def create_gradient(self, base_color: QColor):
        """Create a gradient for the node background."""
        from PyQt6.QtGui import QLinearGradient
        gradient = QLinearGradient(0, 0, 0, self.height)
        gradient.setColorAt(0, base_color.lighter(120))
        gradient.setColorAt(1, base_color)
        return gradient
    
    def get_config(self) -> dict:
        """Get the node configuration."""
        config = {
            "type": self.node_type,
            "name": self.name,
            "msg_type": self.msg_type,
            "topic": self.topic
        }
        if self.namespace:
            config["namespace"] = self.namespace
        if self.qos_profile:
            config["qos"] = self.qos_profile
        if self.parameters:
            config["parameters"] = self.parameters
        return config
    
    def mouseMoveEvent(self, event):
        """Handle mouse move events to update connections."""
        super().mouseMoveEvent(event)
        for conn in self.connections:
            conn.prepareGeometryChange()
    
    def hoverEnterEvent(self, event):
        """Show tooltip on hover."""
        tooltip = f"""<b>{self.name}</b> ({self.node_type})
Topic: {self.topic}
Type: {self.msg_type}"""
        
        if self.namespace:
            tooltip = f"Namespace: {self.namespace}\n{tooltip}"
        
        if self.qos_profile:
            qos = self.qos_profile
            tooltip += f"""
QoS Profile:
• Reliability: {qos['reliability']}
• Durability: {qos['durability']}
• History: {qos['history']['kind']} (depth: {qos['history']['depth']})"""
        
        if self.parameters:
            tooltip += "\nParameters:"
            for name, param in self.parameters.items():
                tooltip += f"\n• {name}: {param['value']} ({param['type']})"
        
        self.setToolTip(tooltip)
        super().hoverEnterEvent(event)

class NodeCanvas(QWidget):
    """Canvas for visually designing ROS 2 nodes."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()
    
    def init_ui(self):
        """Initialize the canvas UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Create graphics scene and view
        self.scene = QGraphicsScene(self)
        self.view = QGraphicsView(self.scene)
        self.view.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.view.setViewportUpdateMode(QGraphicsView.ViewportUpdateMode.FullViewportUpdate)
        self.view.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.view.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        
        layout.addWidget(self.view)
        
        # Context menu
        self.view.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.view.customContextMenuRequested.connect(self.show_context_menu)
        
        # Node types for context menu
        self.node_types = ["Publisher", "Subscriber", "Service", "Action"]
        
        # Common namespaces
        self.common_namespaces = [
            "/robot/", "/sensors/", "/navigation/", "/perception/",
            "/control/", "/hardware/", "/drivers/", "/system/"
        ]
    
    def show_context_menu(self, position):
        """Show context menu for adding nodes."""
        menu = QMenu()
        
        # Add Node submenu
        add_menu = menu.addMenu("Add Node")
        for node_type in self.node_types:
            action = add_menu.addAction(node_type)
            action.triggered.connect(lambda checked, t=node_type: self.add_node(t))
        
        # Add From Template submenu
        add_template_menu = menu.addAction("Add From Template...")
        add_template_menu.triggered.connect(self.add_from_template)
        
        # Manage Templates action
        manage_templates_action = menu.addAction("Manage Templates...")
        manage_templates_action.triggered.connect(self.manage_templates)
        
        if self.scene.selectedItems():
            node = self.scene.selectedItems()[0]
            if isinstance(node, NodeItem):
                # Save as Template action
                save_template_action = menu.addAction("Save as Template...")
                save_template_action.triggered.connect(
                    lambda: self.save_as_template(node))
                
                connect_menu = menu.addMenu("Connect To")
                for item in self.scene.items():
                    if (isinstance(item, NodeItem) and item != node and
                        self.can_connect(node, item)):
                        action = connect_menu.addAction(f"{item.name} ({item.node_type})")
                        action.triggered.connect(
                            lambda checked, s=node, t=item: self.connect_nodes(s, t))
                
                # Node configuration submenu
                config_menu = menu.addMenu("Configure")
                
                qos_action = config_menu.addAction("QoS Profile")
                qos_action.triggered.connect(lambda: self.configure_qos(node))
                
                param_action = config_menu.addAction("Parameters")
                param_action.triggered.connect(lambda: self.configure_parameters(node))
                
                namespace_menu = config_menu.addMenu("Set Namespace")
                for ns in self.common_namespaces:
                    action = namespace_menu.addAction(ns)
                    action.triggered.connect(
                        lambda checked, ns=ns: self.set_namespace(node, ns))
                custom_ns_action = namespace_menu.addAction("Custom...")
                custom_ns_action.triggered.connect(
                    lambda: self.set_custom_namespace(node))
                
                delete_action = menu.addAction("Delete Node")
                delete_action.triggered.connect(self.delete_selected_node)
        
        menu.exec(self.view.mapToGlobal(position))
    
    def add_node(self, node_type: str):
        """Add a new node to the canvas."""
        # Get node configuration from user
        name, ok = QInputDialog.getText(self, "Node Name", "Enter node name:")
        if not ok or not name:
            return
        
        topic, ok = QInputDialog.getText(self, "Topic", "Enter topic name:")
        if not ok or not topic:
            return
        
        # Show message type dialog
        msg_dialog = MessageTypeDialog(self)
        if msg_dialog.exec() == QDialog.DialogCode.Accepted:
            msg_type = msg_dialog.get_message_type()
            if not msg_type:
                return
            
            # Create and add node item
            node = NodeItem(node_type, name, msg_type, topic)
            self.scene.addItem(node)
            
            # Position at center of view
            view_center = self.view.mapToScene(self.view.viewport().rect().center())
            node.setPos(view_center - QPointF(node.width/2, node.height/2))
    
    def delete_selected_node(self):
        """Delete the selected node and its connections."""
        for item in self.scene.selectedItems():
            if isinstance(item, NodeItem):
                # Remove connections
                for conn in item.connections[:]:  # Copy list as it will be modified
                    self.scene.removeItem(conn)
                    if conn in conn.source.connections:
                        conn.source.connections.remove(conn)
                    if conn in conn.target.connections:
                        conn.target.connections.remove(conn)
                self.scene.removeItem(item)
    
    def can_connect(self, source: NodeItem, target: NodeItem) -> bool:
        """Check if two nodes can be connected."""
        # Publishers can connect to Subscribers
        if source.node_type == "Publisher" and target.node_type == "Subscriber":
            return source.msg_type == target.msg_type
        # Services can connect to clients (future)
        # Actions can connect to clients (future)
        return False
    
    def connect_nodes(self, source: NodeItem, target: NodeItem):
        """Create a connection between two nodes."""
        if self.can_connect(source, target):
            conn = ConnectionItem(source, target)
            source.connections.append(conn)
            target.connections.append(conn)
    
    def configure_qos(self, node: NodeItem):
        """Configure QoS profile for a node."""
        dialog = QosProfileDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            node.qos_profile = dialog.get_profile()
            node.update()
    
    def configure_parameters(self, node: NodeItem):
        """Configure parameters for a node."""
        dialog = ParameterDialog(node.parameters, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            node.parameters = dialog.get_parameters()
            node.update()
    
    def set_namespace(self, node: NodeItem, namespace: str):
        """Set the namespace for a node."""
        node.namespace = namespace.rstrip("/")
        node.update()
    
    def set_custom_namespace(self, node: NodeItem):
        """Set a custom namespace for a node."""
        namespace, ok = QInputDialog.getText(
            self, "Custom Namespace",
            "Enter namespace:",
            text=node.namespace
        )
        if ok:
            # Ensure namespace starts with /
            if namespace and not namespace.startswith("/"):
                namespace = "/" + namespace
            node.namespace = namespace
            node.update()
    
    def get_node_configs(self) -> list:
        """Get configurations of all nodes in the canvas."""
        configs = []
        for item in self.scene.items():
            if isinstance(item, NodeItem):
                configs.append(item.get_config())
        return configs
    
    def resizeEvent(self, event):
        """Handle resize events to keep the view fitted to the window."""
        super().resizeEvent(event)
        self.view.setSceneRect(0, 0, event.size().width(), event.size().height())
        self.view.fitInView(self.view.sceneRect(), Qt.AspectRatioMode.KeepAspectRatio)
    
    def add_from_template(self):
        """Add a node from a predefined template."""
        from ..dialogs.template_selector_dialog import TemplateSelectorDialog
        
        dialog = TemplateSelectorDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            template = dialog.get_selected_template()
            if template:
                # Create node from template
                node = NodeItem(
                    template["type"],
                    template["name"],
                    template["msg_type"],
                    template["topic"]
                )
                
                # Apply template configurations
                if "qos" in template:
                    node.qos_profile = template["qos"]
                if "parameters" in template:
                    node.parameters = template["parameters"]
                if "namespace" in template:
                    node.namespace = template["namespace"]
                
                # Add to scene
                self.scene.addItem(node)
                
                # Position at center of view
                view_center = self.view.mapToScene(self.view.viewport().rect().center())
                node.setPos(view_center - QPointF(node.width/2, node.height/2))
    
    def manage_templates(self):
        """Open the template manager dialog."""
        from ..dialogs.template_manager_dialog import TemplateManagerDialog
        
        dialog = TemplateManagerDialog(self)
        dialog.template_selected.connect(self.create_from_template)
        dialog.exec()
    
    def save_as_template(self, node: NodeItem):
        """Save the current node as a template."""
        from ..widgets.template_manager import TemplateManager
        
        # Get template name from user
        name, ok = QInputDialog.getText(
            self,
            "Save as Template",
            "Enter template name:",
            text=node.name
        )
        
        if not ok or not name:
            return
        
        # Create template configuration
        template = {
            "name": name,
            "type": node.node_type,
            "topic": node.topic,
            "msg_type": node.msg_type,
            "description": f"Template created from {node.name}"
        }
        
        if node.qos_profile:
            template["qos"] = node.qos_profile
        if node.parameters:
            template["parameters"] = node.parameters
        if node.namespace:
            template["namespace"] = node.namespace
        
        # Save template
        template_manager = TemplateManager()
        template_manager.add_template("Custom", template)
        
        QMessageBox.information(
            self,
            "Template Saved",
            f"Node configuration saved as template '{name}'."
        )
    
    def create_from_template(self, template: Dict[str, Any]):
        """Create a node from a template configuration."""
        # Create node from template
        node = NodeItem(
            template["type"],
            template["name"],
            template["msg_type"],
            template["topic"]
        )
        
        # Apply template configurations
        if "qos" in template:
            node.qos_profile = template["qos"]
        if "parameters" in template:
            node.parameters = template["parameters"]
        if "namespace" in template:
            node.namespace = template["namespace"]
        
        # Add to scene
        self.scene.addItem(node)
        
        # Position at center of view
        view_center = self.view.mapToScene(self.view.viewport().rect().center())
        node.setPos(view_center - QPointF(node.width/2, node.height/2)) 