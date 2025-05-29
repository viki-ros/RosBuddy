# rosbuddy/ui/views/__init__.py
from .base_view import BaseView
from .settings_view import SettingsView
from .ai_assistant_view import AIAssistantView
from .code_editor_view import CodeEditorView
# Import new placeholder views
from .welcome_view import WelcomeView
from .node_wizard_view import NodeWizardView
from .launch_runner_view import LaunchRunnerView
from .debug_view import DebugView
from .ros_graph_inspector_view import RosGraphInspectorView
from .ros_doctor_view import RosDoctorView
from .ai_agent_action_view import AIAgentActionView

__all__ = [
    "BaseView",
    "SettingsView",
    "AIAssistantView",
    "CodeEditorView",
    "WelcomeView",
    "NodeWizardView",
    "LaunchRunnerView",
    "DebugView",
    "RosGraphInspectorView",
    "RosDoctorView",
    "AIAgentActionView",
]