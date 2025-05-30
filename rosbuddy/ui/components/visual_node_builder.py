from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QGraphicsView, QGraphicsScene,
                               QToolBar, QPushButton, QLabel, QDialog, QLineEdit,
                               QGraphicsItem, QHBoxLayout, QFormLayout, QGraphicsDropShadowEffect,
                               QSplitter, QComboBox)
from PyQt6.QtCore import Qt, pyqtSignal, QRectF, QPointF, QTimer
from PyQt6.QtGui import (QPen, QBrush, QColor, QPainter, QPainterPath, QFont, 
                        QLinearGradient, QRadialGradient, QPainterPathStroker)
import math
from .node_config_panel import NodeConfigPanel

class NodeBlock(QGraphicsItem):
    # Dark matte node colors
    NODE_COLORS = {
        "Publisher": {
            "main": "#FF6B5C",  # Matte Red-Orange
            "border": "#CC5549",
            "text": "#E4E4E4",
            "gradient_start": "#2A2A2A",
            "gradient_end": "#252525",
            "shadow": "#00000055",
            "pattern": "#FF6B5C15"
        },
        "Subscriber": {
            "main": "#5CBA9C",  # Matte Teal
            "border": "#4A9580",
            "text": "#E4E4E4",
            "gradient_start": "#2A2A2A",
            "gradient_end": "#252525",
            "shadow": "#00000055",
            "pattern": "#5CBA9C15"
        },
        "Service": {
            "main": "#FFB05C",  # Matte Amber
            "border": "#CC8D4A",
            "text": "#E4E4E4",
            "gradient_start": "#2A2A2A",
            "gradient_end": "#252525",
            "shadow": "#00000055",
            "pattern": "#FFB05C15"
        },
        "Action": {
            "main": "#B75CFF",  # Matte Purple
            "border": "#924ACC",
            "text": "#E4E4E4",
            "gradient_start": "#2A2A2A",
            "gradient_end": "#252525",
            "shadow": "#00000055",
            "pattern": "#B75CFF15"
        }
    }
    
    # Node type options
    NODE_TYPES = ["Publisher", "Subscriber", "Service", "Action"]
    
    # Common namespace prefixes
    NAMESPACE_PREFIXES = [
        "/",
        "/robot/",
        "/sensors/",
        "/actuators/",
        "/navigation/",
        "/perception/",
        "/control/"
    ]

    def __init__(self, node_type, name):
        super().__init__()
        self.node_type = node_type if node_type in self.NODE_TYPES else "Publisher"
        self.name = name
        self.namespace = ""
        self.message_type = ""
        self.qos_config = {
            "reliability": "Reliable",
            "durability": "Volatile",
            "history": {
                "kind": "Keep Last",
                "depth": 10
            },
            "deadline": 0.0,
            "liveliness": {
                "kind": "Automatic",
                "lease_duration": 0.0
            }
        }
        self.parameters = {}
        self.inputs = []
        self.outputs = []
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable)
        self.setAcceptHoverEvents(True)
        self._hover = False
        
        # Add subtle dark matte shadow
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(12)
        shadow.setColor(QColor("#00000088"))
        shadow.setOffset(2, 2)
        self.setGraphicsEffect(shadow)

    def boundingRect(self):
        return QRectF(-2, -2, 204, 124)  # Slightly larger for border

    def create_matte_texture(self, painter, rect, color):
        """Create a subtle dark matte texture pattern."""
        # Create micro noise pattern for matte effect
        for i in range(0, int(rect.width()), 2):
            for j in range(0, int(rect.height()), 2):
                if (i + j) % 4 == 0:
                    opacity = (i * j) % 4  # Creates varying levels of opacity
                    color = QColor(color)
                    color.setAlpha(opacity)
                    painter.fillRect(
                        rect.x() + i, rect.y() + j, 1, 1,
                        color
                    )

    def paint(self, painter, option, widget):
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Get colors for node type
        colors = self.NODE_COLORS.get(self.node_type, self.NODE_COLORS["Publisher"])
        
        # Create main background with dark matte finish
        path = QPainterPath()
        path.addRoundedRect(0, 0, 200, 120, 6, 6)
        
        # Draw main background with subtle gradient
        gradient = QLinearGradient(0, 0, 0, 120)
        gradient.setColorAt(0, QColor(colors["gradient_start"]))
        gradient.setColorAt(1, QColor(colors["gradient_end"]))
        
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(gradient)
        painter.drawPath(path)
        
        # Add matte texture
        self.create_matte_texture(painter, path.boundingRect(), colors["pattern"])
        
        # Draw border
        if self._hover or self.isSelected():
            painter.setPen(QPen(QColor(colors["main"]), 2))
        else:
            painter.setPen(QPen(QColor(colors["border"]), 1))
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawPath(path)
        
        # Draw header bar with dark matte finish
        header_path = QPainterPath()
        header_path.addRoundedRect(8, 8, 184, 24, 4, 4)
        
        # Create matte gradient for header
        header_gradient = QLinearGradient(8, 8, 8, 32)
        header_gradient.setColorAt(0, QColor(colors["main"]))
        header_gradient.setColorAt(1, QColor(colors["border"]))
        
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(header_gradient)
        painter.drawPath(header_path)
        
        # Add matte texture to header
        self.create_matte_texture(painter, header_path.boundingRect(), colors["pattern"])
        
        # Draw connection points with dark matte finish
        point_gradient = QRadialGradient(0, 60, 5)
        point_gradient.setColorAt(0, QColor(colors["main"]))
        point_gradient.setColorAt(1, QColor(colors["border"]))
        
        # Input point (left)
        painter.setBrush(point_gradient)
        painter.setPen(QPen(QColor(colors["border"]), 1))
        painter.drawEllipse(QPointF(0, 60), 4, 4)
        
        # Output point (right)
        point_gradient.setCenter(200, 60)
        painter.setBrush(point_gradient)
        painter.drawEllipse(QPointF(200, 60), 4, 4)
        
        # Draw text with matte appearance
        font = QFont("Segoe UI", 10)
        painter.setPen(QColor(colors["text"]))
        
        # Node name
        font.setBold(True)
        painter.setFont(font)
        painter.drawText(QRectF(12, 8, 176, 24), 
                        Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter, 
                        self.name)
        
        # Node type and message type
        font.setBold(False)
        painter.setFont(font)
        
        type_text = self.node_type
        if self.message_type:
            msg_type = self.message_type.split('/')[-1]  # Get just the type name
            type_text = f"{type_text} ({msg_type})"
        
        painter.drawText(QRectF(12, 40, 176, 24), 
                        Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter, 
                        type_text)
        
        # Draw namespace if set
        if self.namespace:
            font.setPointSize(8)
            painter.setFont(font)
            painter.drawText(QRectF(12, 70, 176, 20),
                           Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter,
                           f"ns: {self.namespace}")

    def hoverEnterEvent(self, event):
        self._hover = True
        if self.graphicsEffect():
            self.graphicsEffect().setBlurRadius(15)
            self.graphicsEffect().setOffset(3, 3)
        self.update()

    def hoverLeaveEvent(self, event):
        self._hover = False
        if self.graphicsEffect():
            self.graphicsEffect().setBlurRadius(10)
            self.graphicsEffect().setOffset(2, 2)
        self.update()

    def mousePressEvent(self, event):
        if self.graphicsEffect():
            self.graphicsEffect().setBlurRadius(20)
            self.graphicsEffect().setOffset(4, 4)
        super().mousePressEvent(event)

    def mouseReleaseEvent(self, event):
        if self.graphicsEffect():
            self.graphicsEffect().setBlurRadius(10)
            self.graphicsEffect().setOffset(2, 2)
        super().mouseReleaseEvent(event)

    def set_namespace(self, namespace):
        """Set the namespace from predefined options."""
        if namespace in self.NAMESPACE_PREFIXES:
            self.namespace = namespace
        elif namespace.startswith("/"):  # Custom namespace
            self.namespace = namespace
        else:
            self.namespace = "/" + namespace  # Ensure leading slash
        self.update()

    def get_namespace_options(self):
        """Get list of available namespace options."""
        return self.NAMESPACE_PREFIXES

class VisualNodeBuilder(QWidget):
    node_created = pyqtSignal(dict)  # Emits node configuration

    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()
        self.connections = []  # Store node connections
        self.current_node = None  # Currently selected node

    def init_ui(self):
        layout = QHBoxLayout(self)  # Changed to horizontal layout
        layout.setSpacing(0)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Create splitter for canvas and config panel
        splitter = QSplitter(Qt.Orientation.Horizontal)
        layout.addWidget(splitter)
        
        # Left side - Canvas and toolbar
        canvas_widget = QWidget()
        canvas_layout = QVBoxLayout(canvas_widget)
        canvas_layout.setSpacing(10)
        canvas_layout.setContentsMargins(10, 10, 10, 10)
        
        # Toolbar with node types
        toolbar = QToolBar()
        toolbar.setStyleSheet("""
            QToolBar {
                spacing: 8px;
                padding: 5px;
            }
        """)
        
        # Create modern buttons with icons
        self.add_publisher_btn = QPushButton("Add Publisher")
        self.add_subscriber_btn = QPushButton("Add Subscriber")
        self.add_service_btn = QPushButton("Add Service")
        self.add_action_btn = QPushButton("Add Action")
        
        for btn in [self.add_publisher_btn, self.add_subscriber_btn, 
                   self.add_service_btn, self.add_action_btn]:
            toolbar.addWidget(btn)
        
        # Connect buttons to node creation
        self.add_publisher_btn.clicked.connect(lambda: self.create_node_dialog("Publisher"))
        self.add_subscriber_btn.clicked.connect(lambda: self.create_node_dialog("Subscriber"))
        self.add_service_btn.clicked.connect(lambda: self.create_node_dialog("Service"))
        self.add_action_btn.clicked.connect(lambda: self.create_node_dialog("Action"))
        
        canvas_layout.addWidget(toolbar)
        
        # Node canvas
        self.scene = QGraphicsScene(self)
        self.scene.setSceneRect(0, 0, 2000, 2000)
        
        self.view = QGraphicsView(self.scene)
        self.view.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.view.setViewportUpdateMode(QGraphicsView.ViewportUpdateMode.FullViewportUpdate)
        self.view.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.view.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.view.setBackgroundBrush(QBrush(QColor("#1E1E1E")))
        
        # Add grid pattern to the background
        self.draw_grid()
        
        canvas_layout.addWidget(self.view)
        
        # Node connection handling
        self.current_connection = None
        self.scene.selectionChanged.connect(self.handle_selection)
        
        splitter.addWidget(canvas_widget)
        
        # Right side - Configuration panel
        self.config_panel = NodeConfigPanel()
        self.config_panel.config_changed.connect(self.handle_config_changed)
        splitter.addWidget(self.config_panel)
        
        # Set initial splitter sizes (70% canvas, 30% config panel)
        splitter.setSizes([700, 300])
        
        # Hide config panel initially
        self.config_panel.hide()

    def draw_grid(self):
        # Draw a subtle grid pattern
        pen = QPen(QColor("#2A2A2A"))
        pen.setWidth(1)
        
        # Draw vertical lines
        for x in range(0, 2000, 50):
            self.scene.addLine(x, 0, x, 2000, pen)
        
        # Draw horizontal lines
        for y in range(0, 2000, 50):
            self.scene.addLine(0, y, 2000, y, pen)

    def create_node_dialog(self, node_type):
        dialog = QDialog(self)
        dialog.setWindowTitle(f"Create {node_type}")
        dialog.setMinimumWidth(400)
        
        layout = QVBoxLayout(dialog)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)
        
        form_layout = QFormLayout()
        form_layout.setSpacing(10)
        
        # Node name input with suggestions
        name_input = QComboBox()
        name_input.setEditable(True)
        name_input.addItems([
            f"{node_type.lower()}_node",
            f"{node_type.lower()}_1",
            f"{node_type.lower()}_2",
            f"{node_type.lower()}_3"
        ])
        form_layout.addRow("Node Name:", name_input)
        
        # Namespace selection
        namespace_input = QComboBox()
        namespace_input.setEditable(True)
        namespace_input.addItems(NodeBlock.NAMESPACE_PREFIXES)
        form_layout.addRow("Namespace:", namespace_input)
        
        # Topic/Service name with suggestions
        topic_input = QComboBox()
        topic_input.setEditable(True)
        
        # Add common topic/service patterns
        if node_type in ["Publisher", "Subscriber"]:
            topic_input.addItems([
                "/topic",
                "/data",
                "/sensor_data",
                "/status",
                "/command",
                "/feedback"
            ])
        else:  # Service or Action
            topic_input.addItems([
                "/service",
                "/get_data",
                "/set_data",
                "/compute",
                "/request",
                "/execute"
            ])
        
        form_layout.addRow(f"{'Topic' if node_type in ['Publisher', 'Subscriber'] else 'Service'} Name:", topic_input)
        
        # Message type selector
        type_selector = MessageTypeSelector(node_type)
        form_layout.addRow("Message Type:", type_selector)
        
        layout.addLayout(form_layout)
        
        # Buttons
        button_layout = QHBoxLayout()
        button_layout.setSpacing(10)
        
        cancel_btn = QPushButton("Cancel")
        create_btn = QPushButton("Create")
        create_btn.setDefault(True)
        
        button_layout.addWidget(cancel_btn)
        button_layout.addWidget(create_btn)
        
        layout.addLayout(button_layout)
        
        # Connect buttons
        cancel_btn.clicked.connect(dialog.reject)
        create_btn.clicked.connect(lambda: self.add_node(
            node_type,
            name_input.currentText(),
            namespace_input.currentText(),
            topic_input.currentText(),
            type_selector.get_selected_type(),
            dialog
        ))
        
        dialog.exec()

    def add_node(self, node_type, name, namespace, topic, msg_type, dialog):
        """Add a new node to the scene."""
        if not name or not topic or not msg_type:
            return
            
        node_config = {
            "type": node_type,
            "name": name,
            "namespace": namespace,
            "topic": topic,
            "msg_type": msg_type
        }
        
        node_block = NodeBlock(node_type, name)
        node_block.set_namespace(namespace)
        node_block.message_type = msg_type
        self.scene.addItem(node_block)
        
        # Position the node in the visible area
        view_center = self.view.mapToScene(
            self.view.viewport().width() // 2 - 100,
            self.view.viewport().height() // 2 - 60
        )
        node_block.setPos(view_center)
        
        self.node_created.emit(node_config)
        dialog.accept()

    def handle_selection(self):
        """Handle node selection and update configuration panel."""
        selected_items = self.scene.selectedItems()
        
        if len(selected_items) == 1 and isinstance(selected_items[0], NodeBlock):
            # Single node selected - show config panel
            self.current_node = selected_items[0]
            self.config_panel.set_node(self.current_node)
            self.config_panel.show()
        elif len(selected_items) == 2:
            # Two nodes selected - create connection
            self.create_connection(selected_items[0], selected_items[1])
            # Clear selection after creating connection
            for item in selected_items:
                item.setSelected(False)
        else:
            # No node selected or multiple nodes selected
            self.current_node = None
            self.config_panel.hide()

    def handle_config_changed(self, config):
        """Handle changes in node configuration."""
        if self.current_node:
            # Update node name
            self.current_node.name = config["name"]
            # Store other configuration in the node
            self.current_node.namespace = config["namespace"]
            self.current_node.qos_config = config["qos"]
            self.current_node.parameters = config["parameters"]
            # Update visual appearance
            self.current_node.update()
            
            # Emit updated configuration
            self.node_created.emit({
                "type": self.current_node.node_type,
                "name": self.current_node.name,
                "namespace": self.current_node.namespace,
                "qos": self.current_node.qos_config,
                "parameters": self.current_node.parameters
            })

    def create_connection(self, node1, node2):
        # Create a curved connection line
        path = QPainterPath()
        start = node1.pos() + QPointF(200, 60)
        end = node2.pos() + QPointF(0, 60)
        
        # Calculate control points for the curve
        ctrl1 = QPointF(start.x() + 50, start.y())
        ctrl2 = QPointF(end.x() - 50, end.y())
        
        path.moveTo(start)
        path.cubicTo(ctrl1, ctrl2, end)
        
        # Create the connection with a gradient effect
        pen = QPen(QColor("#4A90E2"), 2)
        pen.setStyle(Qt.PenStyle.SolidLine)
        
        connection = self.scene.addPath(path, pen)
        self.connections.append((node1, node2, connection)) 