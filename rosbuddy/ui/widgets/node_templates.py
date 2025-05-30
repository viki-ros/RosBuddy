from typing import Dict, List, Any

class NodeTemplates:
    """Manages predefined node templates for common ROS 2 patterns."""
    
    # Common message types
    STD_MSGS = {
        "Bool": "std_msgs/msg/Bool",
        "String": "std_msgs/msg/String",
        "Int32": "std_msgs/msg/Int32",
        "Float32": "std_msgs/msg/Float32",
        "Float64": "std_msgs/msg/Float64"
    }
    
    GEOMETRY_MSGS = {
        "Point": "geometry_msgs/msg/Point",
        "Pose": "geometry_msgs/msg/Pose",
        "Twist": "geometry_msgs/msg/Twist",
        "Vector3": "geometry_msgs/msg/Vector3",
        "PoseStamped": "geometry_msgs/msg/PoseStamped",
        "TransformStamped": "geometry_msgs/msg/TransformStamped"
    }
    
    SENSOR_MSGS = {
        "Image": "sensor_msgs/msg/Image",
        "LaserScan": "sensor_msgs/msg/LaserScan",
        "PointCloud2": "sensor_msgs/msg/PointCloud2",
        "JointState": "sensor_msgs/msg/JointState",
        "CameraInfo": "sensor_msgs/msg/CameraInfo",
        "Imu": "sensor_msgs/msg/Imu"
    }
    
    # Template categories
    TEMPLATES = {
        "Sensor Data": [
            {
                "name": "Camera Node",
                "type": "Publisher",
                "topic": "/camera/image_raw",
                "msg_type": "sensor_msgs/msg/Image",
                "description": "Publishes raw camera images with optimized QoS for real-time streaming",
                "qos": {
                    "reliability": "Best Effort",
                    "durability": "Volatile",
                    "history": {"kind": "Keep Last", "depth": 1}
                },
                "parameters": {
                    "frame_rate": {"type": "double", "value": 30.0},
                    "image_width": {"type": "int", "value": 640},
                    "image_height": {"type": "int", "value": 480},
                    "encoding": {"type": "string", "value": "rgb8"}
                }
            },
            {
                "name": "Lidar Node",
                "type": "Publisher",
                "topic": "/scan",
                "msg_type": "sensor_msgs/msg/LaserScan",
                "description": "Publishes 2D laser scan data with real-time QoS settings",
                "qos": {
                    "reliability": "Best Effort",
                    "durability": "Volatile",
                    "history": {"kind": "Keep Last", "depth": 1}
                },
                "parameters": {
                    "scan_rate": {"type": "double", "value": 10.0},
                    "angle_min": {"type": "double", "value": -3.14},
                    "angle_max": {"type": "double", "value": 3.14},
                    "range_min": {"type": "double", "value": 0.1},
                    "range_max": {"type": "double", "value": 30.0}
                }
            },
            {
                "name": "IMU Node",
                "type": "Publisher",
                "topic": "/imu/data",
                "msg_type": "sensor_msgs/msg/Imu",
                "description": "Publishes inertial measurement data with high-frequency updates",
                "qos": {
                    "reliability": "Best Effort",
                    "durability": "Volatile",
                    "history": {"kind": "Keep Last", "depth": 1}
                },
                "parameters": {
                    "update_rate": {"type": "double", "value": 100.0},
                    "frame_id": {"type": "string", "value": "imu_link"}
                }
            }
        ],
        "Robot Control": [
            {
                "name": "Velocity Controller",
                "type": "Subscriber",
                "topic": "/cmd_vel",
                "msg_type": "geometry_msgs/msg/Twist",
                "description": "Subscribes to velocity commands for robot motion control",
                "qos": {
                    "reliability": "Reliable",
                    "durability": "Volatile",
                    "history": {"kind": "Keep Last", "depth": 1}
                },
                "parameters": {
                    "max_linear_speed": {"type": "double", "value": 1.0},
                    "max_angular_speed": {"type": "double", "value": 1.57},
                    "acceleration_limit": {"type": "double", "value": 0.5}
                }
            },
            {
                "name": "Joint State Publisher",
                "type": "Publisher",
                "topic": "/joint_states",
                "msg_type": "sensor_msgs/msg/JointState",
                "description": "Publishes robot joint states with reliable delivery",
                "qos": {
                    "reliability": "Reliable",
                    "durability": "Transient Local",
                    "history": {"kind": "Keep Last", "depth": 10}
                },
                "parameters": {
                    "publish_rate": {"type": "double", "value": 50.0},
                    "joint_names": {"type": "string", "value": "[]"}
                }
            }
        ],
        "Navigation": [
            {
                "name": "Path Planner",
                "type": "Action",
                "topic": "/navigate_to_pose",
                "msg_type": "nav2_msgs/action/NavigateToPose",
                "description": "Handles navigation action requests with path planning",
                "parameters": {
                    "max_velocity": {"type": "double", "value": 0.5},
                    "min_obstacle_distance": {"type": "double", "value": 0.3},
                    "planning_algorithm": {"type": "string", "value": "a_star"},
                    "control_frequency": {"type": "double", "value": 20.0}
                }
            },
            {
                "name": "Pose Subscriber",
                "type": "Subscriber",
                "topic": "/robot_pose",
                "msg_type": "geometry_msgs/msg/PoseStamped",
                "description": "Subscribes to robot pose updates for localization",
                "qos": {
                    "reliability": "Reliable",
                    "durability": "Volatile",
                    "history": {"kind": "Keep Last", "depth": 1}
                }
            },
            {
                "name": "Map Server",
                "type": "Publisher",
                "topic": "/map",
                "msg_type": "nav_msgs/msg/OccupancyGrid",
                "description": "Publishes occupancy grid map for navigation",
                "qos": {
                    "reliability": "Reliable",
                    "durability": "Transient Local",
                    "history": {"kind": "Keep Last", "depth": 1}
                },
                "parameters": {
                    "map_file": {"type": "string", "value": "map.yaml"},
                    "update_rate": {"type": "double", "value": 1.0}
                }
            }
        ],
        "Perception": [
            {
                "name": "Object Detector",
                "type": "Publisher",
                "topic": "/detected_objects",
                "msg_type": "vision_msgs/msg/Detection2DArray",
                "description": "Publishes 2D object detection results from camera input",
                "qos": {
                    "reliability": "Best Effort",
                    "durability": "Volatile",
                    "history": {"kind": "Keep Last", "depth": 1}
                },
                "parameters": {
                    "confidence_threshold": {"type": "double", "value": 0.5},
                    "model_path": {"type": "string", "value": "model.pth"},
                    "device": {"type": "string", "value": "cuda"}
                }
            },
            {
                "name": "Point Cloud Processor",
                "type": "Subscriber",
                "topic": "/points_raw",
                "msg_type": "sensor_msgs/msg/PointCloud2",
                "description": "Processes raw point cloud data for obstacle detection",
                "qos": {
                    "reliability": "Best Effort",
                    "durability": "Volatile",
                    "history": {"kind": "Keep Last", "depth": 1}
                },
                "parameters": {
                    "voxel_size": {"type": "double", "value": 0.1},
                    "min_height": {"type": "double", "value": -2.0},
                    "max_height": {"type": "double", "value": 2.0}
                }
            },
            {
                "name": "Pose Estimator",
                "type": "Service",
                "topic": "/estimate_pose",
                "msg_type": "geometry_msgs/srv/PoseEstimation",
                "description": "Provides pose estimation service from sensor data",
                "parameters": {
                    "algorithm": {"type": "string", "value": "solvepnp"},
                    "ransac_iterations": {"type": "int", "value": 100},
                    "confidence": {"type": "double", "value": 0.99}
                }
            }
        ],
        "Diagnostics": [
            {
                "name": "System Monitor",
                "type": "Publisher",
                "topic": "/diagnostics",
                "msg_type": "diagnostic_msgs/msg/DiagnosticArray",
                "description": "Monitors system health and publishes diagnostic information",
                "qos": {
                    "reliability": "Reliable",
                    "durability": "Transient Local",
                    "history": {"kind": "Keep Last", "depth": 5}
                },
                "parameters": {
                    "update_rate": {"type": "double", "value": 1.0},
                    "system_ok_threshold": {"type": "double", "value": 0.8},
                    "check_cpu": {"type": "bool", "value": True},
                    "check_memory": {"type": "bool", "value": True},
                    "check_disk": {"type": "bool", "value": True}
                }
            },
            {
                "name": "Error Handler",
                "type": "Subscriber",
                "topic": "/errors",
                "msg_type": "diagnostic_msgs/msg/DiagnosticStatus",
                "description": "Handles and logs system error messages",
                "qos": {
                    "reliability": "Reliable",
                    "durability": "Transient Local",
                    "history": {"kind": "Keep Last", "depth": 10}
                },
                "parameters": {
                    "log_file": {"type": "string", "value": "errors.log"},
                    "max_log_size": {"type": "int", "value": 1048576}
                }
            }
        ]
    }
    
    @classmethod
    def get_categories(cls) -> List[str]:
        """Get list of template categories."""
        return list(cls.TEMPLATES.keys())
    
    @classmethod
    def get_templates_in_category(cls, category: str) -> List[Dict[str, Any]]:
        """Get list of templates in a category."""
        return cls.TEMPLATES.get(category, [])
    
    @classmethod
    def get_all_templates(cls) -> Dict[str, List[Dict[str, Any]]]:
        """Get all templates organized by category."""
        return cls.TEMPLATES
    
    @classmethod
    def get_common_message_types(cls) -> Dict[str, Dict[str, str]]:
        """Get all common message types organized by package."""
        return {
            "std_msgs": cls.STD_MSGS,
            "geometry_msgs": cls.GEOMETRY_MSGS,
            "sensor_msgs": cls.SENSOR_MSGS
        } 