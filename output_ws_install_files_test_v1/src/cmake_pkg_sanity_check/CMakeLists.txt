cmake_minimum_required(VERSION 3.8)
project(cmake_pkg_sanity_check)

# Default C++ standard
if(NOT CMAKE_CXX_STANDARD)
  set(CMAKE_CXX_STANDARD 17)
endif()

if(CMAKE_COMPILER_IS_GNUCXX OR CMAKE_CXX_COMPILER_ID MATCHES "Clang")
  add_compile_options(-Wall -Wextra -Wpedantic)
endif()

find_package(ament_cmake REQUIRED)

# Find other ROS 2 packages
find_package(rclcpp REQUIRED)

# TODO: Add executables, libraries, and other targets here
# Example for adding an executable:
# add_executable(${PROJECT_NAME}_node src/my_node.cpp)
# ament_target_dependencies(${PROJECT_NAME}_node rclcpp std_msgs)
# install(TARGETS ${PROJECT_NAME}_node DESTINATION lib/${PROJECT_NAME})

# TODO: Add rules for generating messages, services, actions
# Example for generating interfaces:
# find_package(rosidl_default_generators REQUIRED)
# rosidl_generate_interfaces(${PROJECT_NAME}
#   "msg/MyMessage.msg"
#   "srv/MyService.srv"
#   ACTION "action/MyAction.action"
#   DEPENDENCIES std_msgs # Or other message packages that your interfaces depend on
# )

if(BUILD_TESTING)
  find_package(ament_lint_auto REQUIRED)
  ament_lint_auto_find_test_dependencies()
endif()

ament_package()