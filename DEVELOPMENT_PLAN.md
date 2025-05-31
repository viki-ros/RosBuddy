# ROSBuddy Detailed Development Plan
**Post-Foundation, Core ROS 2 Focus**

## Overarching Goal
Deliver a robust, user-friendly, and wizard-driven IDE for core ROS 2 development workflows, maximizing automation and minimizing manual configuration for the user. AI features are deferred.

---

## Phase 1: Solidify Core Workflows & Creation Wizards (Immediate Focus)

**Objective**: Ensure all fundamental ROS entity creation tasks are handled by polished, guided wizards, and that core actions like build, clean, run, and launch are seamlessly integrated into the new UI.

### 1.1. Implement Core ROS Actions in MainWindow (Integrate ToolInvoker)
**Priority**: Critical (Unblocks core development cycle)  
**Status**: Backend exists (ToolInvoker), UI methods are placeholders  

#### Tasks:
- [ ] **Fully implement MainWindow.on_build_workspace()**
  - Connect relevant UI buttons (ROS Tools Overview, WorkspaceExplorer context menu, main toolbar)
  - Use ToolInvoker.colcon_build via Worker thread
  - Stream stdout/stderr to a dedicated "Build Output" tab in the Bottom Panel
  - Update Status Bar with build progress/status
  - Handle success/failure messages and update UI button states

- [ ] **Fully implement MainWindow.on_clean_workspace()**
  - Similar integration for ToolInvoker.colcon_clean
  - Stream output to "Build Output" or a general "Output" tab

- [ ] **Fully implement MainWindow.on_run_executable()**
  - Launch SelectRosItemDialog (mode="run") to choose package/executable
  - Use ToolInvoker.ros2_run via Worker
  - Store subprocess.Popen object in MainWindow.running_ros_process
  - Stream output to a "Run/Launch Output" tab in the Bottom Panel
  - Update Status Bar and UI button states

- [ ] **Fully implement MainWindow.on_launch_file()**
  - Launch SelectRosItemDialog (mode="launch") to choose package/launch file
  - Use ToolInvoker.ros2_launch via Worker
  - Store subprocess.Popen object in MainWindow.running_ros_process
  - Stream output to "Run/Launch Output" tab
  - Update Status Bar and UI button states

- [ ] **Fully implement MainWindow.on_stop_task()**
  - Reliably terminate MainWindow.running_ros_process
  - Update UI and Status Bar

**Verification**: User can build, clean, run executables, launch files, and stop running tasks reliably from the UI. Output is clearly displayed. UI state reflects ongoing operations.

### 1.2. Complete "Create New Node" Wizard Integration (NodeWizardView)
**Priority**: High (Core ROS entity creation)  
**Status**: Backend logic exists, NodeWizardView is a placeholder  

#### Tasks:
- [ ] **Design and implement multi-step NodeWizardView UI**
  - QWidget for Main Area tab, using QStackedWidget for steps
  - Key Steps: Target Package/Name/Language, Node Role & Interface Definition (using MessageTypeSelector), Code Gen Options, Dependencies, Summary & Generate

- [ ] **Connect wizard's "Generate" action to backend logic**
  - Connect to existing backend logic in MainWindow (on_new_python_node, on_new_cpp_node)
  - Pass structured data collected by the wizard
  - Ensure setup.py/CMakeLists.txt/package.xml are correctly updated

- [ ] **Refresh WorkspaceExplorer on completion**

**Verification**: Wizard is highly guided. Generates buildable/runnable Python and C++ nodes (standalone executables for C++) with correct boilerplate and build system integration.

### 1.3. Implement "Create New Launch File" Wizard (CreateLaunchWizard)
**Priority**: High (Core ROS entity creation)  
**Status**: Basic file generation exists, visual UI missing  

#### Tasks:
- [ ] **Design and implement multi-step CreateLaunchWizard UI**
  - Main Area tab with key steps: Location/Name/Type, Initial Setup (imports), Compose Launch Elements, Global Config, Preview & Generate

- [ ] **Implement "Compose Launch Elements" step**
  - Palette of actions, composition area, config panel for selected element parameters
  - For "Node" action: package/executable selection using QComboBoxes from PackageDiscovery
  - Parameter configuration with key-value table or YAML file selection

- [ ] **Connect wizard to backend logic**
  - Use launch_file_generator.py (construct LaunchConfiguration and NodeAction objects)
  - Ensure launch files placed in launch/ directory and are installable

- [ ] **Refresh WorkspaceExplorer**

**Verification**: Wizard allows creation of basic Python launch files with Node actions. Generated launch files are valid, installable, and runnable via ros2 launch.

### 1.4. Implement "Create New Parameter File (YAML)" Wizard/Editor
**Priority**: Medium (Supports launch files and node configuration)  
**Status**: Not Implemented  

#### Tasks:
- [ ] **Design and implement CreateParameterFileWizard**
  - Select package/location/name
  - UI to define parameters under node namespaces (name, value input with type awareness)

- [ ] **Real-time preview of generated YAML**
- [ ] **Save file to package (typically config/ subdir)**
- [ ] **Refresh WorkspaceExplorer**

**Verification**: Wizard allows creation of valid YAML parameter files loadable by ROS 2.

### 1.5. Enhance CodeEditorView (Basic Syntax Highlighting & Line Numbers)
**Priority**: Medium (Improves usability of opened files)  
**Status**: Basic editor exists  

#### Tasks:
- [ ] **Implement QSyntaxHighlighter subclasses**
  - Python, C++, XML, CMake, YAML, Launch.py, msg/srv/action

- [ ] **Implement line number area**

**Verification**: Syntax highlighting and line numbers work for supported file types.

---

## Phase 2: Core Introspection Tools & UI Polish

**Objective**: Provide essential ROS 2 introspection capabilities through user-friendly GUIs and continue overall UI refinement.

### 2.1. Implement "ROS Graph Visualizer" (Polish)
**Priority**: High  
**Status**: Implemented with auto-refresh  

#### Tasks:
- [ ] **Ensure UI/UX is polished**
  - Interaction, filtering, details panel
  - Follow UI/UX Design Specification Section 5.2

**Verification**: Stable, interactive, and informative graph visualization.

### 2.2. Implement "Topic Monitor" (Polish)
**Priority**: High  
**Status**: Implemented with real-time updates  

#### Tasks:
- [ ] **Ensure UI/UX is polished**
  - Dynamic form for publishing messages (start with simple types)
  - Structured tree view for echoing complex messages

**Verification**: Can list, echo (with good formatting), and publish messages to topics.

### 2.3. Implement "Parameter Browser" (ParameterBrowserView)
**Priority**: Medium  
**Status**: Placeholder/Not Implemented  

#### Tasks:
- [ ] **Design and implement ParameterBrowserView**
  - UI: Node list, parameter table (name, type, value), editable values
  - Backend: ros2 param list/get/set via ToolInvoker
  - Features: Dump to YAML, Load from YAML

**Verification**: Can view and modify parameters of running nodes. Dump/load works.

### 2.4. Implement "Service Explorer" (ServiceExplorerView)
**Priority**: Medium  
**Status**: Not Implemented  

#### Tasks:
- [ ] **Design and implement ServiceExplorerView**
  - UI: Service list, display service type, dynamic form for request, display response
  - Backend: ros2 service list/type/call via ToolInvoker

**Verification**: Can list services, inspect types, and call services with user-provided requests.

### 2.5. Implement "Action Explorer" (ActionExplorerView)
**Priority**: Medium  
**Status**: Not Implemented  

#### Tasks:
- [ ] **Design and implement ActionExplorerView**
  - UI: Action list, display type, dynamic form for goal, display feedback/result, cancel button
  - Backend: ros2 action list/info/send_goal via ToolInvoker

**Verification**: Can list actions, inspect types, send goals, and view feedback/results.

### 2.6. Implement "Problems" Tab in Bottom Panel (Functional)
**Priority**: Medium  

#### Tasks:
- [ ] **Parse output from "Build Output" tab**
  - Parse colcon output for error/warning patterns
  - Display in structured list (Message, File, Line)
  - Make items clickable to open file in CodeEditorView at specified line

**Verification**: Build errors are clearly listed and navigable.

### 2.7. UI Polish & Minor Enhancements
#### Tasks:
- [ ] **Address Technical Debt**
  - Refactor large UI files
  - Improve error handling messages
  - Add more logging

- [ ] **Advanced QSS styling**
  - Subtle animations/transitions

---

## Phase 3: Advanced Features & Ecosystem

**Objective**: Broaden ROSBuddy's capabilities with advanced developer tools and ecosystem support.

### 3.1. Advanced Visualizers
- [ ] Implement "TF Tree Visualizer"
- [ ] Implement "ROS Doctor Dashboard"

### 3.2. Settings System
- [ ] Implement full "Settings" View
- [ ] Configuration of themes, paths, default wizard values
- [ ] Persist settings

### 3.3. Run & Debug Activity Enhancements
- [ ] UI for managing multiple, named launch configurations
- [ ] Integrated Debugger UI for Python (pdb/debugpy) and C++ (gdb)

### 3.4. Advanced CodeEditorView Features
- [ ] Autocompletion (basic for ROS types)
- [ ] Linting integration (flake8, cppcheck/clang-tidy in "Problems" panel)

### 3.5. Advanced Dependency Management
- [ ] "Manage Dependencies" View (Full Implementation)
- [ ] Rich UI for viewing/editing package.xml dependencies

### 3.6. Command Palette
- [ ] Implement Command Palette (Ctrl+Shift+P)

### 3.7. Future Integrations
- [ ] Simulation Integration (Gazebo/RViz launch & config)
- [ ] Template Manager deep integration

---

## Explicitly Deferred (Out of Scope)

- **All AI-specific features** (code explanation, intelligent suggestions, AI documentation generation, AI code completion)
- **Plugin System / Extension Management**

---

## Current Implementation Status

**Phase 1 Progress:**
- ✅ Core Infrastructure (70-75% complete)
- ⚠️ Task 1.1: UI methods are placeholders - **IMMEDIATE PRIORITY**
- ⚠️ Task 1.2: NodeWizardView is placeholder - **HIGH PRIORITY**
- ⚠️ Task 1.3: CreateLaunchWizard missing - **HIGH PRIORITY**
- ❌ Task 1.4: CreateParameterFileWizard not implemented
- ⚠️ Task 1.5: Basic CodeEditorView exists

**Next Steps:**
1. Start with Task 1.1 - Implement Core ROS Actions in MainWindow
2. Move to Task 1.2 - Complete Node Creation Wizard
3. Continue sequentially through Phase 1 tasks
