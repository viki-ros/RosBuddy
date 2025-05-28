import rclpy
from rclpy.node import Node
# from std_msgs.msg import String # Would be needed for actual publishing

class HelloWorldNode(Node):
    def __init__(self):
        super().__init__('my_detailed_py_pkg_for_cmake_test_hello_world_node')
        # self.publisher_ = self.create_publisher(String, 'topic', 10) # Actual publisher
        timer_period = 0.5  # seconds
        self.timer = self.create_timer(timer_period, self.timer_callback)
        self.i = 0
        self.get_logger().info('Hello world Python node started! (Prototype version)')

    def timer_callback(self):
        # msg = String() # Actual message
        # msg.data = f'Hello World Python: {self.i}'
        # self.publisher_.publish(msg)
        log_msg = f'Hello World Python: {self.i} (Prototype: not publishing to ROS topic)'
        self.get_logger().info(log_msg)
        self.i += 1

def main(args=None):
    rclpy.init(args=args)
    node = HelloWorldNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        if node: # Check if node exists before logging
            node.get_logger().info('Keyboard interrupt, shutting down.') 
    finally:
        if node: # Check if node exists before destroying
            node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()
