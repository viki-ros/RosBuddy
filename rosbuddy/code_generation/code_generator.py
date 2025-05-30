from typing import Dict, Any, List
import os
from pathlib import Path
from .node_generator import NodeGenerator
from .package_generator import PackageGenerator

class CodeGenerator:
    """Main code generator for ROSBuddy."""
    
    def __init__(self):
        self.node_generator = NodeGenerator()
        self.package_generator = PackageGenerator()
    
    def generate_package(self, package_name: str, nodes: List[Dict[str, Any]], 
                        output_dir: str, **package_info) -> None:
        """Generate a complete ROS 2 package."""
        # Create output directory structure
        pkg_dir = Path(output_dir) / package_name
        pkg_dir.mkdir(parents=True, exist_ok=True)
        
        # Create package subdirectories
        (pkg_dir / package_name).mkdir(exist_ok=True)
        (pkg_dir / "launch").mkdir(exist_ok=True)
        (pkg_dir / "resource").mkdir(exist_ok=True)
        
        # Generate package files
        package_files = self.package_generator.generate_package(
            package_name, nodes, **package_info
        )
        
        # Write package files
        for rel_path, content in package_files.items():
            file_path = pkg_dir / rel_path
            file_path.parent.mkdir(parents=True, exist_ok=True)
            file_path.write_text(content)
        
        # Generate node files
        for node in nodes:
            node_name = node["name"]
            node_code = self.node_generator.generate_node(node)
            
            # Add main function
            node_code += f"""

def main(args=None):
    rclpy.init(args=args)
    node = {self.node_generator._generate_class_name(node_name)}()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()
"""
            
            # Write node file
            node_file = pkg_dir / package_name / f"{node_name}.py"
            node_file.write_text(node_code)
        
        # Create __init__.py
        init_file = pkg_dir / package_name / "__init__.py"
        init_file.touch()
    
    def validate_package_name(self, name: str) -> bool:
        """Validate ROS 2 package name."""
        if not name:
            return False
        
        # Check for valid characters (lowercase letters, numbers, underscores)
        if not all(c.islower() or c.isdigit() or c == '_' for c in name):
            return False
        
        # Must start with letter
        if not name[0].isalpha():
            return False
        
        return True
    
    def validate_node_config(self, config: Dict[str, Any]) -> List[str]:
        """Validate node configuration."""
        errors = []
        
        required_fields = ["type", "name", "msg_type", "topic"]
        for field in required_fields:
            if field not in config:
                errors.append(f"Missing required field: {field}")
        
        if "type" in config and config["type"] not in ["Publisher", "Subscriber", "Service", "Action"]:
            errors.append(f"Invalid node type: {config['type']}")
        
        if "msg_type" in config:
            try:
                pkg, category, name = config["msg_type"].split("/")
                if category not in ["msg", "srv", "action"]:
                    errors.append(f"Invalid message category: {category}")
            except ValueError:
                errors.append("Invalid message type format (should be package/category/type)")
        
        if "topic" in config and not config["topic"].startswith("/"):
            errors.append("Topic should start with /")
        
        if "parameters" in config:
            for name, param in config["parameters"].items():
                if "type" not in param:
                    errors.append(f"Missing type for parameter: {name}")
                if "value" not in param:
                    errors.append(f"Missing value for parameter: {name}")
        
        return errors 