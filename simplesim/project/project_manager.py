"""
Project manager for SimpleSim.

Handles CRUD operations for projects, including file management.
"""

import shutil
import uuid
from pathlib import Path
from typing import List, Optional
from datetime import datetime

from .project_data import Project


class ProjectManager:
    """
    Manages SimpleSim projects.

    Handles:
    - Creating new projects
    - Loading existing projects
    - Saving project metadata
    - Importing files (meshes, config)
    - Deleting projects
    """

    PROJECTS_DIR = Path("projects_data")

    def __init__(self):
        """Initialize the project manager."""
        self.PROJECTS_DIR.mkdir(parents=True, exist_ok=True)

    def list_projects(self) -> List[Project]:
        """
        List all projects.

        Returns:
            List of Project objects, sorted by modified date (newest first)
        """
        projects = []

        if not self.PROJECTS_DIR.exists():
            return projects

        for project_dir in self.PROJECTS_DIR.iterdir():
            if not project_dir.is_dir():
                continue

            metadata_path = project_dir / "project.json"
            if not metadata_path.exists():
                continue

            try:
                project = Project.load(project_dir.name)
                projects.append(project)
            except Exception as e:
                print(f"Warning: Could not load project {project_dir.name}: {e}")

        # Sort by modified date, newest first
        projects.sort(key=lambda p: p.modified_at, reverse=True)
        return projects

    def create_project(self, name: str) -> Project:
        """
        Create a new project.

        Args:
            name: Name for the new project

        Returns:
            The created Project object
        """
        project_id = str(uuid.uuid4())

        project = Project(
            id=project_id,
            name=name,
            created_at=datetime.now(),
            modified_at=datetime.now()
        )

        # Create project directory structure
        project.path.mkdir(parents=True, exist_ok=True)
        project.meshes_path.mkdir(parents=True, exist_ok=True)

        # Save metadata
        project.save()

        return project

    def load_project(self, project_id: str) -> Project:
        """
        Load a project by ID.

        Args:
            project_id: The project's UUID

        Returns:
            The loaded Project object

        Raises:
            FileNotFoundError: If project doesn't exist
        """
        return Project.load(project_id)

    def save_project(self, project: Project):
        """
        Save project metadata.

        Args:
            project: The project to save
        """
        project.save()

    def delete_project(self, project_id: str):
        """
        Delete a project and all its files.

        Args:
            project_id: The project's UUID
        """
        project_path = self.PROJECTS_DIR / project_id
        if project_path.exists():
            shutil.rmtree(project_path)

    def import_mesh_files(self, project: Project, file_paths: List[Path]) -> int:
        """
        Import mesh files into a project.

        Copies the files to the project's meshes directory.

        Args:
            project: The target project
            file_paths: List of mesh file paths to import

        Returns:
            Number of files successfully imported
        """
        project.meshes_path.mkdir(parents=True, exist_ok=True)
        imported = 0

        for src_path in file_paths:
            if not src_path.exists():
                continue

            # Check if it's a valid mesh file
            valid_extensions = {'.stl', '.obj', '.STL', '.OBJ'}
            if src_path.suffix not in valid_extensions:
                continue

            # Copy to project
            dst_path = project.meshes_path / src_path.name
            shutil.copy2(src_path, dst_path)
            imported += 1

        if imported > 0:
            project.save()

        return imported

    def import_config(self, project: Project, config_path: Path) -> bool:
        """
        Import a config file into a project.

        Validates and copies the config file to the project.

        Args:
            project: The target project
            config_path: Path to the config file

        Returns:
            True if import was successful
        """
        if not config_path.exists():
            return False

        # Validate it's a JSON file
        if config_path.suffix.lower() != '.json':
            return False

        # Copy to project
        shutil.copy2(config_path, project.config_path)
        project.save()

        return True

    def set_robot_code_path(self, project: Project, robot_path: Path) -> bool:
        """
        Set the robot code path for a project.

        Stores a reference to the robot code folder (does not copy files).

        Args:
            project: The target project
            robot_path: Path to the robot code folder

        Returns:
            True if the path was valid and set
        """
        if not robot_path.exists() or not robot_path.is_dir():
            return False

        project.robot_code_path = str(robot_path.absolute())
        project.save()

        return True

    def clear_meshes(self, project: Project):
        """
        Clear all mesh files from a project.

        Args:
            project: The target project
        """
        if project.meshes_path.exists():
            for f in project.meshes_path.iterdir():
                f.unlink()
        project.save()

    def clear_config(self, project: Project):
        """
        Clear the config file from a project.

        Args:
            project: The target project
        """
        if project.config_path.exists():
            project.config_path.unlink()
        project.save()

    def duplicate_project(self, project: Project, new_name: str) -> Project:
        """
        Duplicate an existing project.

        Args:
            project: The project to duplicate
            new_name: Name for the new project

        Returns:
            The new Project object
        """
        new_project = self.create_project(new_name)

        # Copy meshes
        if project.meshes_path.exists():
            for mesh_file in project.mesh_files:
                shutil.copy2(mesh_file, new_project.meshes_path / mesh_file.name)

        # Copy config
        if project.has_config:
            shutil.copy2(project.config_path, new_project.config_path)

        # Copy robot code reference
        new_project.robot_code_path = project.robot_code_path
        new_project.save()

        return new_project

    def get_project_by_name(self, name: str) -> Optional[Project]:
        """
        Find a project by name.

        Args:
            name: The project name to search for

        Returns:
            The Project if found, None otherwise
        """
        for project in self.list_projects():
            if project.name == name:
                return project
        return None
