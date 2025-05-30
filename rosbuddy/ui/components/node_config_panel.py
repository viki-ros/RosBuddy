from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QFormLayout, QLineEdit,
                           QComboBox, QSpinBox, QDoubleSpinBox, QCheckBox,
                           QGroupBox, QTabWidget, QPushButton, QLabel,
                           QScrollArea, QFrame)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont
from .message_type_selector import MessageTypeSelector

class QosProfileWidget(QGroupBox):
    """Widget for configuring QoS settings."""
    
    qos_changed = pyqtSignal(dict)
    
    # Standard ROS 2 QoS options
    RELIABILITY_OPTIONS = ["Reliable", "Best Effort"]
    DURABILITY_OPTIONS = ["Volatile", "Transient Local"]
    HISTORY_KIND_OPTIONS = ["Keep Last", "Keep All"]
    HISTORY_DEPTH_OPTIONS = [1, 5, 10, 20, 50, 100, 1000]
    LIVELINESS_KIND_OPTIONS = ["Automatic", "Manual By Topic"]
    DEADLINE_OPTIONS = [0.0, 0.1, 0.25, 0.5, 1.0, 2.0, 5.0]
    LEASE_DURATION_OPTIONS = [0.0, 0.1, 0.25, 0.5, 1.0, 2.0, 5.0]
    
    def __init__(self, parent=None):
        super().__init__("QoS Profile", parent)
        self.init_ui()
        
    def init_ui(self):
        layout = QFormLayout(self)
        layout.setSpacing(10)
        
        # Reliability
        self.reliability = QComboBox()
        self.reliability.addItems(self.RELIABILITY_OPTIONS)
        layout.addRow("Reliability:", self.reliability)
        
        # Durability
        self.durability = QComboBox()
        self.durability.addItems(self.DURABILITY_OPTIONS)
        layout.addRow("Durability:", self.durability)
        
        # History
        history_group = QGroupBox("History")
        history_layout = QFormLayout(history_group)
        
        self.history_kind = QComboBox()
        self.history_kind.addItems(self.HISTORY_KIND_OPTIONS)
        history_layout.addRow("Kind:", self.history_kind)
        
        self.history_depth = QComboBox()
        self.history_depth.addItems([str(x) for x in self.HISTORY_DEPTH_OPTIONS])
        self.history_depth.setCurrentText("10")
        history_layout.addRow("Depth:", self.history_depth)
        
        layout.addRow(history_group)
        
        # Deadline
        deadline_group = QGroupBox("Deadline")
        deadline_layout = QFormLayout(deadline_group)
        
        self.deadline_sec = QComboBox()
        self.deadline_sec.addItems([str(x) for x in self.DEADLINE_OPTIONS])
        deadline_layout.addRow("Seconds:", self.deadline_sec)
        
        layout.addRow(deadline_group)
        
        # Liveliness
        liveliness_group = QGroupBox("Liveliness")
        liveliness_layout = QFormLayout(liveliness_group)
        
        self.liveliness_kind = QComboBox()
        self.liveliness_kind.addItems(self.LIVELINESS_KIND_OPTIONS)
        liveliness_layout.addRow("Kind:", self.liveliness_kind)
        
        self.lease_duration = QComboBox()
        self.lease_duration.addItems([str(x) for x in self.LEASE_DURATION_OPTIONS])
        liveliness_layout.addRow("Lease Duration (s):", self.lease_duration)
        
        layout.addRow(liveliness_group)
        
        # Connect signals
        for widget in [self.reliability, self.durability, self.history_kind,
                      self.history_depth, self.deadline_sec, self.liveliness_kind,
                      self.lease_duration]:
            widget.currentTextChanged.connect(self._emit_qos_changed)
    
    def _emit_qos_changed(self):
        """Emit QoS configuration as a dictionary."""
        qos_config = {
            "reliability": self.reliability.currentText(),
            "durability": self.durability.currentText(),
            "history": {
                "kind": self.history_kind.currentText(),
                "depth": int(self.history_depth.currentText())
            },
            "deadline": float(self.deadline_sec.currentText()),
            "liveliness": {
                "kind": self.liveliness_kind.currentText(),
                "lease_duration": float(self.lease_duration.currentText())
            }
        }
        self.qos_changed.emit(qos_config)
    
    def load_config(self, config):
        """Load QoS configuration."""
        if not config:
            return
            
        # Block signals temporarily
        for widget in [self.reliability, self.durability, self.history_kind,
                      self.history_depth, self.deadline_sec, self.liveliness_kind,
                      self.lease_duration]:
            widget.blockSignals(True)
        
        try:
            # Set values from config
            self.reliability.setCurrentText(config.get("reliability", "Reliable"))
            self.durability.setCurrentText(config.get("durability", "Volatile"))
            
            history = config.get("history", {})
            self.history_kind.setCurrentText(history.get("kind", "Keep Last"))
            self.history_depth.setCurrentText(str(history.get("depth", 10)))
            
            self.deadline_sec.setCurrentText(str(config.get("deadline", 0.0)))
            
            liveliness = config.get("liveliness", {})
            self.liveliness_kind.setCurrentText(liveliness.get("kind", "Automatic"))
            self.lease_duration.setCurrentText(str(liveliness.get("lease_duration", 0.0)))
        
        finally:
            # Unblock signals
            for widget in [self.reliability, self.durability, self.history_kind,
                         self.history_depth, self.deadline_sec, self.liveliness_kind,
                         self.lease_duration]:
                widget.blockSignals(False)
        
        # Emit the loaded configuration
        self._emit_qos_changed()

    @property
    def qos_config(self):
        """Get current QoS configuration."""
        return {
            "reliability": self.reliability.currentText(),
            "durability": self.durability.currentText(),
            "history": {
                "kind": self.history_kind.currentText(),
                "depth": int(self.history_depth.currentText())
            },
            "deadline": float(self.deadline_sec.currentText()),
            "liveliness": {
                "kind": self.liveliness_kind.currentText(),
                "lease_duration": float(self.lease_duration.currentText())
            }
        }

class ParameterWidget(QGroupBox):
    """Widget for configuring ROS 2 parameters."""
    
    parameters_changed = pyqtSignal(dict)
    
    # Define standard ROS 2 parameter types
    PARAMETER_TYPES = [
        "bool",
        "int",
        "double",
        "string",
        "bool[]",
        "int[]",
        "double[]",
        "string[]"
    ]
    
    # Define common boolean options
    BOOL_OPTIONS = ["true", "false"]
    
    def __init__(self, parent=None):
        super().__init__("Parameters", parent)
        self.init_ui()
        
    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        
        # Parameter list
        self.param_list = QFrame()
        self.param_layout = QVBoxLayout(self.param_list)
        self.param_layout.setSpacing(5)
        
        # Scroll area for parameters
        scroll = QScrollArea()
        scroll.setWidget(self.param_list)
        scroll.setWidgetResizable(True)
        layout.addWidget(scroll)
        
        # Add parameter button
        add_btn = QPushButton("Add Parameter")
        add_btn.clicked.connect(self.add_parameter_row)
        layout.addWidget(add_btn)
    
    def add_parameter_row(self, name="", param_type="string", value=""):
        """Add a new parameter configuration row."""
        row = QFrame()
        row_layout = QFormLayout(row)
        row_layout.setSpacing(5)
        
        # Parameter name
        name_input = QLineEdit()
        name_input.setPlaceholderText("Parameter name")
        name_input.setText(name)
        row_layout.addRow("Name:", name_input)
        
        # Parameter type
        type_combo = QComboBox()
        type_combo.addItems(self.PARAMETER_TYPES)
        type_combo.setCurrentText(param_type)
        row_layout.addRow("Type:", type_combo)
        
        # Create appropriate value widget based on type
        value_widget = self._create_value_widget(param_type, value)
        row_layout.addRow("Value:", value_widget)
        
        # Delete button
        delete_btn = QPushButton("×")
        delete_btn.setFixedWidth(30)
        delete_btn.clicked.connect(lambda: self.delete_parameter_row(row))
        row_layout.addRow("", delete_btn)
        
        self.param_layout.addWidget(row)
        
        # Connect signals
        name_input.textChanged.connect(self._emit_parameters_changed)
        type_combo.currentTextChanged.connect(
            lambda t: self._update_value_widget(row_layout, t))
        self._connect_value_widget_signal(value_widget)
    
    def _create_value_widget(self, param_type, value=""):
        """Create an appropriate widget for the parameter type."""
        if param_type == "bool":
            widget = QComboBox()
            widget.addItems(self.BOOL_OPTIONS)
            widget.setCurrentText(str(value).lower())
        elif param_type == "int":
            widget = QSpinBox()
            widget.setRange(-1000000, 1000000)
            try:
                widget.setValue(int(value))
            except (ValueError, TypeError):
                widget.setValue(0)
        elif param_type == "double":
            widget = QDoubleSpinBox()
            widget.setRange(-1000000, 1000000)
            widget.setDecimals(6)
            try:
                widget.setValue(float(value))
            except (ValueError, TypeError):
                widget.setValue(0.0)
        elif param_type.endswith("[]"):
            # For arrays, use a line edit with comma-separated values
            widget = QLineEdit()
            if isinstance(value, (list, tuple)):
                widget.setText(", ".join(str(v) for v in value))
            else:
                widget.setText(str(value))
            widget.setPlaceholderText("Comma-separated values")
        else:  # string
            widget = QLineEdit()
            widget.setText(str(value))
        
        return widget
    
    def _update_value_widget(self, layout, new_type):
        """Update the value widget when type changes."""
        # Get current value if possible
        old_widget = layout.itemAt(5).widget()
        current_value = self._get_widget_value(old_widget)
        
        # Create new widget
        new_widget = self._create_value_widget(new_type, current_value)
        
        # Replace widget in layout
        layout.removeWidget(old_widget)
        old_widget.deleteLater()
        layout.addRow("Value:", new_widget)
        
        # Connect signal
        self._connect_value_widget_signal(new_widget)
        
        # Emit change
        self._emit_parameters_changed()
    
    def _connect_value_widget_signal(self, widget):
        """Connect appropriate signal for the value widget."""
        if isinstance(widget, QComboBox):
            widget.currentTextChanged.connect(self._emit_parameters_changed)
        elif isinstance(widget, (QSpinBox, QDoubleSpinBox)):
            widget.valueChanged.connect(self._emit_parameters_changed)
        else:  # QLineEdit
            widget.textChanged.connect(self._emit_parameters_changed)
    
    def _get_widget_value(self, widget):
        """Get the current value from a widget."""
        if isinstance(widget, QComboBox):
            return widget.currentText()
        elif isinstance(widget, (QSpinBox, QDoubleSpinBox)):
            return widget.value()
        else:  # QLineEdit
            return widget.text()
    
    def _parse_array_value(self, text, base_type):
        """Parse comma-separated values into an array."""
        if not text.strip():
            return []
            
        values = [v.strip() for v in text.split(",")]
        try:
            if base_type == "bool":
                return [v.lower() == "true" for v in values]
            elif base_type == "int":
                return [int(v) for v in values]
            elif base_type == "double":
                return [float(v) for v in values]
            else:  # string
                return values
        except (ValueError, TypeError):
            return []
    
    def delete_parameter_row(self, row):
        """Delete a parameter row."""
        self.param_layout.removeWidget(row)
        row.deleteLater()
        self._emit_parameters_changed()
    
    def clear_parameters(self):
        """Remove all parameter rows."""
        while self.param_layout.count():
            item = self.param_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
    
    def load_parameters(self, parameters):
        """Load parameters configuration."""
        if not parameters:
            return
        
        # Clear existing parameters
        self.clear_parameters()
        
        # Add parameter rows
        for name, config in parameters.items():
            self.add_parameter_row(
                name=name,
                param_type=config.get("type", "string"),
                value=config.get("value", "")
            )
    
    @property
    def parameters(self):
        """Get current parameters configuration."""
        parameters = {}
        for i in range(self.param_layout.count()):
            row = self.param_layout.itemAt(i).widget()
            if row:
                layout = row.layout()
                name = layout.itemAt(1).widget().text()
                if name:  # Only include if name is not empty
                    type_widget = layout.itemAt(3).widget()
                    value_widget = layout.itemAt(5).widget()
                    
                    param_type = type_widget.currentText()
                    value = self._get_widget_value(value_widget)
                    
                    # Handle array types
                    if param_type.endswith("[]"):
                        base_type = param_type[:-2]
                        value = self._parse_array_value(value, base_type)
                    elif param_type == "bool":
                        value = value.lower() == "true"
                    elif param_type == "int":
                        value = int(value)
                    elif param_type == "double":
                        value = float(value)
                    
                    parameters[name] = {
                        "type": param_type,
                        "value": value
                    }
        
        return parameters

class NodeConfigPanel(QWidget):
    """Main panel for configuring ROS 2 nodes."""
    
    config_changed = pyqtSignal(dict)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.node_type = None
        self.init_ui()
    
    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        
        # Node info section
        info_group = QGroupBox("Node Information")
        info_layout = QFormLayout(info_group)
        
        self.node_name = QLineEdit()
        info_layout.addRow("Node Name:", self.node_name)
        
        self.node_namespace = QLineEdit()
        info_layout.addRow("Namespace:", self.node_namespace)
        
        # Message type selector (will be created when node type is set)
        self.type_selector = None
        self.type_selector_container = QWidget()
        self.type_selector_layout = QVBoxLayout(self.type_selector_container)
        info_layout.addRow(self.type_selector_container)
        
        layout.addWidget(info_group)
        
        # Tabs for different configuration aspects
        tabs = QTabWidget()
        
        # QoS tab
        self.qos_widget = QosProfileWidget()
        tabs.addTab(self.qos_widget, "QoS Settings")
        
        # Parameters tab
        self.param_widget = ParameterWidget()
        tabs.addTab(self.param_widget, "Parameters")
        
        layout.addWidget(tabs)
        
        # Connect signals
        self.node_name.textChanged.connect(self._emit_config_changed)
        self.node_namespace.textChanged.connect(self._emit_config_changed)
        self.qos_widget.qos_changed.connect(self._emit_config_changed)
        self.param_widget.parameters_changed.connect(self._emit_config_changed)
    
    def _emit_config_changed(self):
        """Emit complete node configuration."""
        config = {
            "name": self.node_name.text(),
            "namespace": self.node_namespace.text(),
            "qos": self.qos_widget.qos_config,
            "parameters": self.param_widget.parameters
        }
        
        # Add message type if available
        if self.type_selector:
            config["message_type"] = self.type_selector.get_selected_type()
        
        self.config_changed.emit(config)
    
    def set_node(self, node_block):
        """Set the node to configure."""
        # Block signals temporarily
        self.node_name.blockSignals(True)
        self.node_namespace.blockSignals(True)
        
        try:
            # Update basic info
            self.node_name.setText(node_block.name)
            self.node_namespace.setText(getattr(node_block, 'namespace', ''))
            
            # Update node type and message type selector
            if self.node_type != node_block.node_type:
                self.node_type = node_block.node_type
                
                # Clear existing type selector
                if self.type_selector:
                    self.type_selector_layout.removeWidget(self.type_selector)
                    self.type_selector.deleteLater()
                
                # Create new type selector
                self.type_selector = MessageTypeSelector(self.node_type)
                self.type_selector.type_selected.connect(self._emit_config_changed)
                self.type_selector_layout.addWidget(self.type_selector)
            
            # Set message type if available
            if hasattr(node_block, 'message_type'):
                self.type_selector.set_selected_type(node_block.message_type)
            
            # Load QoS configuration
            if hasattr(node_block, 'qos_config'):
                self.qos_widget.load_config(node_block.qos_config)
            
            # Load parameters
            if hasattr(node_block, 'parameters'):
                self.param_widget.load_parameters(node_block.parameters)
            
        finally:
            # Unblock signals
            self.node_name.blockSignals(False)
            self.node_namespace.blockSignals(False)
            
            # Emit initial configuration
            self._emit_config_changed()
            
            # Show the panel
            self.show() 