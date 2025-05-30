import json
import os
import hashlib
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from PyQt6.QtCore import QObject, pyqtSignal
import shutil

class TemplateManager(QObject):
    """Manages user-defined node templates with versioning and team sync support."""
    
    # Signals
    templates_changed = pyqtSignal()
    sync_status_changed = pyqtSignal(str)  # Emits sync status messages
    
    def __init__(self):
        super().__init__()
        self.user_templates_file = Path.home() / ".rosbuddy" / "templates.json"
        self.team_templates_dir = Path.home() / ".rosbuddy" / "team_templates"
        self.version_history_dir = Path.home() / ".rosbuddy" / "template_versions"
        self.user_templates: Dict[str, List[Dict[str, Any]]] = {}
        
        # Create necessary directories
        for directory in [self.team_templates_dir, self.version_history_dir]:
            directory.mkdir(parents=True, exist_ok=True)
        
        self.load_templates()
    
    def load_templates(self):
        """Load user-defined templates from file."""
        if self.user_templates_file.exists():
            try:
                with open(self.user_templates_file, 'r') as f:
                    self.user_templates = json.load(f)
            except json.JSONDecodeError:
                self.user_templates = {}
        else:
            # Create default template categories
            self.user_templates = {
                "Custom": [],
                "Favorites": [],
                "Team": []
            }
            self.save_templates()
    
    def save_templates(self):
        """Save user-defined templates to file."""
        # Ensure directory exists
        self.user_templates_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(self.user_templates_file, 'w') as f:
            json.dump(self.user_templates, f, indent=2)
        
        self.templates_changed.emit()
    
    def add_template(self, category: str, template: Dict[str, Any], author: str = ""):
        """Add a new template to a category with versioning."""
        if category not in self.user_templates:
            self.user_templates[category] = []
        
        # Add metadata
        timestamp = datetime.now().isoformat()
        template["metadata"] = {
            "created": timestamp,
            "modified": timestamp,
            "version": 1,
            "author": author or os.getenv("USER", "unknown"),
            "template_id": self._generate_template_id(template)
        }
        
        # Save initial version
        self._save_template_version(template)
        
        self.user_templates[category].append(template)
        self.save_templates()
    
    def update_template(self, category: str, template_name: str, 
                       updated_template: Dict[str, Any]):
        """Update an existing template with version tracking."""
        if category not in self.user_templates:
            return
        
        for i, template in enumerate(self.user_templates[category]):
            if template["name"] == template_name:
                # Update metadata
                metadata = template.get("metadata", {}).copy()
                metadata["version"] = metadata.get("version", 0) + 1
                metadata["modified"] = datetime.now().isoformat()
                
                # Update template
                updated_template["metadata"] = metadata
                self._save_template_version(updated_template)
                self.user_templates[category][i] = updated_template
                self.save_templates()
                break
    
    def get_template_versions(self, template_id: str) -> List[Dict[str, Any]]:
        """Get version history of a template."""
        versions_dir = self.version_history_dir / template_id
        if not versions_dir.exists():
            return []
        
        versions = []
        for version_file in sorted(versions_dir.glob("*.json")):
            with open(version_file, 'r') as f:
                versions.append(json.load(f))
        
        return versions
    
    def revert_to_version(self, category: str, template_name: str, 
                         version_number: int) -> bool:
        """Revert a template to a specific version."""
        template = self.find_template(category, template_name)
        if not template or "metadata" not in template:
            return False
        
        template_id = template["metadata"]["template_id"]
        versions = self.get_template_versions(template_id)
        
        for version in versions:
            if version["metadata"]["version"] == version_number:
                # Create new version with reverted content
                reverted = version.copy()
                reverted["metadata"] = template["metadata"].copy()
                reverted["metadata"]["version"] += 1
                reverted["metadata"]["modified"] = datetime.now().isoformat()
                reverted["metadata"]["reverted_from"] = version_number
                
                self.update_template(category, template_name, reverted)
                return True
        
        return False
    
    def set_team_sync_dir(self, directory: Path):
        """Set the team synchronization directory."""
        if directory.exists() and directory.is_dir():
            # Copy existing templates to new location
            if self.team_templates_dir.exists():
                shutil.rmtree(self.team_templates_dir)
            shutil.copytree(directory, self.team_templates_dir)
            self.sync_status_changed.emit(f"Team sync directory set to: {directory}")
            self.sync_with_team()
    
    def sync_with_team(self):
        """Synchronize templates with team directory."""
        if not self.team_templates_dir.exists():
            self.sync_status_changed.emit("Team sync directory not configured")
            return
        
        # Load team templates
        team_templates = []
        for template_file in self.team_templates_dir.glob("*.json"):
            try:
                with open(template_file, 'r') as f:
                    template = json.load(f)
                    team_templates.append(template)
            except json.JSONDecodeError:
                continue
        
        # Update team category
        self.user_templates["Team"] = team_templates
        self.save_templates()
        
        self.sync_status_changed.emit(
            f"Synchronized {len(team_templates)} team templates"
        )
    
    def publish_to_team(self, template: Dict[str, Any]):
        """Publish a template to the team directory."""
        if not self.team_templates_dir.exists():
            self.sync_status_changed.emit("Team sync directory not configured")
            return False
        
        template_id = template["metadata"]["template_id"]
        filepath = self.team_templates_dir / f"{template_id}.json"
        
        try:
            with open(filepath, 'w') as f:
                json.dump(template, f, indent=2)
            self.sync_status_changed.emit(f"Published template: {template['name']}")
            return True
        except Exception as e:
            self.sync_status_changed.emit(f"Error publishing template: {str(e)}")
            return False
    
    def _generate_template_id(self, template: Dict[str, Any]) -> str:
        """Generate a unique template ID."""
        # Create a unique hash based on name and creation time
        unique_string = f"{template['name']}_{datetime.now().isoformat()}"
        return hashlib.sha256(unique_string.encode()).hexdigest()[:12]
    
    def _save_template_version(self, template: Dict[str, Any]):
        """Save a version of a template."""
        if "metadata" not in template:
            return
        
        template_id = template["metadata"]["template_id"]
        version = template["metadata"]["version"]
        
        # Create version directory
        version_dir = self.version_history_dir / template_id
        version_dir.mkdir(exist_ok=True)
        
        # Save version file
        version_file = version_dir / f"v{version}.json"
        with open(version_file, 'w') as f:
            json.dump(template, f, indent=2)
    
    def find_template(self, category: str, template_name: str) -> Optional[Dict[str, Any]]:
        """Find a template by category and name."""
        if category in self.user_templates:
            for template in self.user_templates[category]:
                if template["name"] == template_name:
                    return template
        return None
    
    def remove_template(self, category: str, template_name: str):
        """Remove a template from a category."""
        if category in self.user_templates:
            self.user_templates[category] = [
                t for t in self.user_templates[category]
                if t["name"] != template_name
            ]
            self.save_templates()
    
    def add_category(self, category: str):
        """Add a new template category."""
        if category not in self.user_templates:
            self.user_templates[category] = []
            self.save_templates()
    
    def remove_category(self, category: str):
        """Remove a template category and all its templates."""
        if category in self.user_templates:
            del self.user_templates[category]
            self.save_templates()
    
    def get_categories(self) -> List[str]:
        """Get list of user-defined template categories."""
        return list(self.user_templates.keys())
    
    def get_templates_in_category(self, category: str) -> List[Dict[str, Any]]:
        """Get list of templates in a category."""
        return self.user_templates.get(category, [])
    
    def export_templates(self, filepath: str, categories: Optional[List[str]] = None):
        """Export templates to a JSON file."""
        if categories:
            # Export only specified categories
            export_data = {
                cat: self.user_templates[cat]
                for cat in categories
                if cat in self.user_templates
            }
        else:
            # Export all templates
            export_data = self.user_templates
        
        with open(filepath, 'w') as f:
            json.dump(export_data, f, indent=2)
    
    def import_templates(self, filepath: str, merge: bool = True):
        """Import templates from a JSON file."""
        with open(filepath, 'r') as f:
            imported = json.load(f)
        
        if merge:
            # Merge with existing templates
            for category, templates in imported.items():
                if category not in self.user_templates:
                    self.user_templates[category] = []
                self.user_templates[category].extend(templates)
        else:
            # Replace existing templates
            self.user_templates = imported
        
        self.save_templates()
    
    def add_to_favorites(self, template: Dict[str, Any]):
        """Add a template to favorites."""
        if "Favorites" not in self.user_templates:
            self.user_templates["Favorites"] = []
        
        # Check if already in favorites
        if not any(t["name"] == template["name"] 
                  for t in self.user_templates["Favorites"]):
            self.user_templates["Favorites"].append(template)
            self.save_templates()
    
    def remove_from_favorites(self, template_name: str):
        """Remove a template from favorites."""
        if "Favorites" in self.user_templates:
            self.user_templates["Favorites"] = [
                t for t in self.user_templates["Favorites"]
                if t["name"] != template_name
            ]
            self.save_templates()
    
    def search_templates(self, query: str) -> List[Dict[str, Any]]:
        """Search for templates across all categories."""
        results = []
        query = query.lower()
        
        for category, templates in self.user_templates.items():
            for template in templates:
                # Search in name, description, and topic
                if (query in template["name"].lower() or
                    query in template.get("description", "").lower() or
                    query in template["topic"].lower()):
                    # Add category info to template
                    template_with_category = template.copy()
                    template_with_category["category"] = category
                    results.append(template_with_category)
        
        return results 