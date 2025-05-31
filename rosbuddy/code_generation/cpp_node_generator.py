import re
from datetime import datetime

def to_camel_case(s):
    return ''.join(word.capitalize() for word in re.split(r'[_\-]', s))

def msg_type_to_cpp(msg_type):
    # "std_msgs/msg/String" -> ("std_msgs::msg::String", "std_msgs/msg/string.hpp", "std_msgs")
    pkg, cat, name = msg_type.split('/')
    cpp_type = f"{pkg}::{cat}::{name}"
    include = f"<{pkg}/{cat}/{name.lower()}.hpp>"
    return cpp_type, include, pkg

class CppNodeGenerator:
    def generate_node_files_content(self, config: dict) -> dict:
        pkg = config['package_name']
        node_name = config['node_name']
        role = config['role']
        topic = config.get('topic_name')
        msg_type = config.get('message_type')
        class_name = to_camel_case(node_name)
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        namespace = pkg
        
        msg_cpp_type, msg_include, msg_pkg = (None, None, None)
        if role in ("Publisher Node", "Subscriber Node") and msg_type:
            msg_cpp_type, msg_include, msg_pkg = msg_type_to_cpp(msg_type)
        
        # Header guard
        guard = f"{pkg.upper()}__{class_name.upper()}_HPP_"
        hpp_lines = [
            f"#ifndef {guard}",
            f"#define {guard}",
            "",
            "#include <rclcpp/rclcpp.hpp>",
        ]
        if msg_include:
            hpp_lines.append(f"#include {msg_include}")
        hpp_lines.append("")
        hpp_lines.append(f"namespace {namespace} {{")
        hpp_lines.append("")
        hpp_lines.append(f"class {class_name} : public rclcpp::Node {{")
        hpp_lines.append("public:")
        hpp_lines.append(f"  explicit {class_name}(const rclcpp::NodeOptions & options = rclcpp::NodeOptions());")
        hpp_lines.append("")
        hpp_lines.append("private:")
        if role == "Publisher Node":
            hpp_lines.append(f"  rclcpp::Publisher<{msg_cpp_type}>::SharedPtr publisher_;")
            hpp_lines.append(f"  rclcpp::TimerBase::SharedPtr timer_;")
            hpp_lines.append(f"  void timer_callback();")
        elif role == "Subscriber Node":
            hpp_lines.append(f"  rclcpp::Subscription<{msg_cpp_type}>::SharedPtr subscription_;")
            hpp_lines.append(f"  void topic_callback(const {msg_cpp_type}::SharedPtr msg) const;")
        hpp_lines.append("};\n")
        hpp_lines.append(f"}}  // namespace {namespace}")
        hpp_lines.append("")
        hpp_lines.append(f"#endif  // {guard}")
        hpp_content = '\n'.join(hpp_lines)

        # Source file
        cpp_lines = [
            f"#include \"{node_name}.hpp\"",
            "#include <chrono>",
            "using namespace std::chrono_literals;",
            "",
            f"namespace {namespace} {{",
            "",
            f"{class_name}::{class_name}(const rclcpp::NodeOptions & options) : Node(\"{node_name}\", options) {{"
        ]
        if role == "Publisher Node":
            cpp_lines.append(f"  publisher_ = this->create_publisher<{msg_cpp_type}>(\"{topic}\", 10);")
            cpp_lines.append(f"  timer_ = this->create_wall_timer(500ms, std::bind(&{class_name}::timer_callback, this));")
            cpp_lines.append(f"  RCLCPP_INFO(this->get_logger(), \"'%s' publisher started.\", this->get_name());")
        elif role == "Subscriber Node":
            cpp_lines.append(f"  subscription_ = this->create_subscription<{msg_cpp_type}>(\"{topic}\", 10, std::bind(&{class_name}::topic_callback, this, std::placeholders::_1));")
            cpp_lines.append(f"  RCLCPP_INFO(this->get_logger(), \"'%s' subscriber started.\", this->get_name());")
        else:
            cpp_lines.append(f"  RCLCPP_INFO(this->get_logger(), \"'%s' node started.\", this->get_name());")
        cpp_lines.append("}")
        cpp_lines.append("")
        if role == "Publisher Node":
            cpp_lines.append(f"void {class_name}::timer_callback() {{")
            cpp_lines.append(f"  auto msg = {msg_cpp_type}();")
            cpp_lines.append(f"  msg.data = std::string(\"Hello from {class_name}!\");")
            cpp_lines.append(f"  publisher_->publish(msg);")
            cpp_lines.append(f"  RCLCPP_INFO(this->get_logger(), \"Published: '%s'\", msg.data.c_str());")
            cpp_lines.append("}")
        elif role == "Subscriber Node":
            cpp_lines.append(f"void {class_name}::topic_callback(const {msg_cpp_type}::SharedPtr msg) const {{")
            cpp_lines.append(f"  RCLCPP_INFO(this->get_logger(), \"I heard: '%s'\", msg->data.c_str());")
            cpp_lines.append("}")
        cpp_lines.append("")
        cpp_lines.append(f"}}  // namespace {namespace}")
        cpp_lines.append("")
        # Standalone main()
        cpp_lines.append("int main(int argc, char * argv[]) {")
        cpp_lines.append("  rclcpp::init(argc, argv);")
        cpp_lines.append(f"  rclcpp::spin(std::make_shared<{namespace}::{class_name}>(rclcpp::NodeOptions()));")
        cpp_lines.append("  rclcpp::shutdown();")
        cpp_lines.append("  return 0;")
        cpp_lines.append("}")
        cpp_content = '\n'.join(cpp_lines)

        return {'hpp_content': hpp_content, 'cpp_content': cpp_content, 'msg_pkg': msg_pkg if msg_pkg else None}
