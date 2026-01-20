"""
Project data model for SimpleSim.

Represents a simulation project with all its associated files and metadata.
"""

from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Optional, List
import json


@dataclass
class Project:
    """
    Represents a SimpleSim project.

    A project contains:
    - Metadata (name, dates, etc.)
    - Mesh files (STL/OBJ)
    - Configuration file (config.json)
    - Reference to robot code folder
    """

    id: str
    name: str
    created_at: datetime = field(default_factory=datetime.now)
    modified_at: datetime = field(default_factory=datetime.now)
    robot_code_path: Optional[str] = None

    # === Computed Properties ===

    @property
    def path(self) -> Path:
        """Get the project directory path."""
        return Path("projects_data") / self.id

    @property
    def metadata_path(self) -> Path:
        """Get the path to project.json metadata file."""
        return self.path / "project.json"

    @property
    def config_path(self) -> Path:
        """Get the path to the subsystem config file."""
        return self.path / "config.json"

    @property
    def meshes_path(self) -> Path:
        """Get the path to the meshes directory."""
        return self.path / "meshes"

    @property
    def has_config(self) -> bool:
        """Check if the project has a config file."""
        return self.config_path.exists()

    @property
    def has_meshes(self) -> bool:
        """Check if the project has any mesh files."""
        if not self.meshes_path.exists():
            return False
        mesh_extensions = {'.stl', '.obj', '.STL', '.OBJ'}
        for f in self.meshes_path.iterdir():
            if f.suffix in mesh_extensions:
                return True
        return False

    @property
    def has_robot_code(self) -> bool:
        """Check if the project has a valid robot code path."""
        if not self.robot_code_path:
            return False
        path = Path(self.robot_code_path)
        return path.exists() and path.is_dir()

    @property
    def mesh_files(self) -> List[Path]:
        """Get list of mesh files in the project."""
        if not self.meshes_path.exists():
            return []
        mesh_extensions = {'.stl', '.obj', '.STL', '.OBJ'}
        return [f for f in self.meshes_path.iterdir() if f.suffix in mesh_extensions]

    @property
    def is_ready_to_simulate(self) -> bool:
        """Check if the project has all required files to run simulation."""
        return self.has_config and self.has_meshes and self.has_robot_code

    # === Serialization ===

    def to_dict(self) -> dict:
        """Convert project to dictionary for JSON serialization."""
        return {
            "id": self.id,
            "name": self.name,
            "created_at": self.created_at.isoformat(),
            "modified_at": self.modified_at.isoformat(),
            "robot_code_path": self.robot_code_path
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'Project':
        """Create project from dictionary."""
        return cls(
            id=data["id"],
            name=data["name"],
            created_at=datetime.fromisoformat(data["created_at"]),
            modified_at=datetime.fromisoformat(data["modified_at"]),
            robot_code_path=data.get("robot_code_path")
        )

    def save(self):
        """Save project metadata to disk."""
        self.modified_at = datetime.now()
        self.path.mkdir(parents=True, exist_ok=True)
        self.meshes_path.mkdir(parents=True, exist_ok=True)

        with open(self.metadata_path, 'w') as f:
            json.dump(self.to_dict(), f, indent=2)

    @classmethod
    def load(cls, project_id: str) -> 'Project':
        """Load project from disk by ID."""
        metadata_path = Path("projects_data") / project_id / "project.json"
        if not metadata_path.exists():
            raise FileNotFoundError(f"Project not found: {project_id}")

        with open(metadata_path, 'r') as f:
            data = json.load(f)

        return cls.from_dict(data)

    # === String Representation ===

    def __str__(self) -> str:
        status = []
        if self.has_meshes:
            status.append("meshes")
        if self.has_config:
            status.append("config")
        if self.has_robot_code:
            status.append("robot")
        status_str = ", ".join(status) if status else "empty"
        return f"Project({self.name}, {status_str})"
