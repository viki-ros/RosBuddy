cmake_minimum_required(VERSION 3.8)
project(cmake_pkg_with_interfaces)

if(NOT CMAKE_CXX_STANDARD)
  set(CMAKE_CXX_STANDARD 17)
endif()

if(CMAKE_COMPILER_IS_GNUCXX OR CMAKE_CXX_COMPILER_ID MATCHES "Clang")
  add_compile_options(-Wall -Wextra -Wpedantic)
endif()

find_package(ament_cmake REQUIRED)

# Find direct dependencies
find_package(rosidl_default_generators REQUIRED)
find_package(std_msgs REQUIRED)

# Interface Generation
# Ensure rosidl_default_generators was found (added above)
# TODO: Uncomment and verify/complete the rosidl_generate_interfaces call:
# rosidl_generate_interfaces(${PROJECT_NAME}
#   "action/ProcessOrder.action"
#    "msg/SensorData.msg"
#   # DEPENDENCIES std_msgs # Add other msg/srv/action packages your interfaces depend on
# )
# TODO: Also ensure targets that USE these interfaces link against them, e.g.:
# ament_target_dependencies(my_node ${PROJECT_NAME}__rosidl_typesupport_cpp)

# Install rules

if(BUILD_TESTING)
  find_package(ament_lint_auto REQUIRED)
  ament_lint_auto_find_test_dependencies()
endif()

ament_package()