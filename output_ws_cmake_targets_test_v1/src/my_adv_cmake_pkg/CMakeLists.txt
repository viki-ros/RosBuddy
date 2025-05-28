cmake_minimum_required(VERSION 3.8)
project(my_adv_cmake_pkg)

if(NOT CMAKE_CXX_STANDARD)
  set(CMAKE_CXX_STANDARD 17)
endif()

if(CMAKE_COMPILER_IS_GNUCXX OR CMAKE_CXX_COMPILER_ID MATCHES "Clang")
  add_compile_options(-Wall -Wextra -Wpedantic)
endif()

find_package(ament_cmake REQUIRED)

# Find direct dependencies (usually other ROS 2 packages)
find_package(rclcpp REQUIRED)
find_package(std_msgs REQUIRED)

# Library: utils_lib
add_library(utils_lib src/utils.cpp src/another_util.cpp)

# Executable: main_node
add_executable(main_node src/main_node.cpp)
ament_target_dependencies(main_node rclcpp std_msgs)
target_link_libraries(main_node PRIVATE utils_lib)

# Executable: talker_node
add_executable(talker_node src/talker_node.cpp)
ament_target_dependencies(talker_node rclcpp std_msgs)

# TODO: Add rules for generating messages, services, actions (rosidl_generate_interfaces)

# Install rules
install(TARGETS
  utils_lib
  main_node
  talker_node
  ARCHIVE DESTINATION lib
  LIBRARY DESTINATION lib
  RUNTIME DESTINATION lib/${PROJECT_NAME} # For executables
)

# Install launch files
install(DIRECTORY
  launch
  DESTINATION share/${PROJECT_NAME}
)

# Install config files
install(DIRECTORY
  config
  DESTINATION share/${PROJECT_NAME}
)

if(BUILD_TESTING)
  find_package(ament_lint_auto REQUIRED)
  ament_lint_auto_find_test_dependencies()
endif()

ament_package()