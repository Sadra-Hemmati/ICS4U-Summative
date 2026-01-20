"""
Project overview screen for SimpleSim.

Displays project actions: Import Mesh, Import Config, Select Robot Code,
Generate From STEP, and Run Simulation.
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import subprocess
import sys
from pathlib import Path
from typing import TYPE_CHECKING

from .base_screen import BaseScreen
from simplesim.theming import Colors

if TYPE_CHECKING:
    from simplesim.app import SimpleSimApp


class ProjectOverviewScreen(BaseScreen):
    """
    Project overview screen with action buttons.

    Displays:
    - Project name
    - Status indicators for each resource
    - Action buttons for importing/generating/running
    """

    TITLE = "Project"
    HAS_BACK_BUTTON = True

    def build(self):
        """Build the project overview UI."""
        project = self.app.current_project
        if not project:
            return

        # Navigation bar with project name
        self.create_nav_bar(self.frame, title=project.name)

        # Main content area with padding
        content = tk.Frame(self.frame, bg=Colors.BG_PRIMARY)
        content.pack(fill=tk.BOTH, expand=True, padx=60, pady=30)

        # Section title
        section_title = ttk.Label(
            content,
            text="Project Setup",
            style="Header.TLabel"
        )
        section_title.pack(anchor=tk.W, pady=(0, 20))

        # Action buttons container (2x3 grid style)
        actions_frame = tk.Frame(content, bg=Colors.BG_PRIMARY)
        actions_frame.pack(fill=tk.BOTH, expand=True)

        # Row 1: Import actions
        row1 = tk.Frame(actions_frame, bg=Colors.BG_PRIMARY)
        row1.pack(fill=tk.X, pady=10)

        self._create_action_card(
            row1,
            title="Import Mesh Files",
            description="Import STL or OBJ mesh files",
            icon="\U0001F4E6",  # Package emoji
            status_key="meshes",
            command=self._import_meshes
        ).pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))

        self._create_action_card(
            row1,
            title="Import Config File",
            description="Import subsystem configuration JSON",
            icon="\u2699",  # Gear emoji
            status_key="config",
            command=self._import_config
        ).pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10)

        self._create_action_card(
            row1,
            title="Select Robot Code",
            description="Select robot code project folder",
            icon="\U0001F4BB",  # Computer emoji
            status_key="robot",
            command=self._select_robot_code
        ).pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(10, 0))

        # Row 2: Generate and Run
        row2 = tk.Frame(actions_frame, bg=Colors.BG_PRIMARY)
        row2.pack(fill=tk.X, pady=10)

        self._create_action_card(
            row2,
            title="Generate From STEP",
            description="Open CAD editor to define subsystem from STEP file",
            icon="\U0001F527",  # Wrench emoji
            status_key=None,  # No status for this action
            command=self._generate_from_step,
            accent=False
        ).pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))

        # Run simulation (accent style)
        self._run_card = self._create_action_card(
            row2,
            title="Run Simulation",
            description="Launch physics simulation with robot code",
            icon="\u25B6",  # Play button
            status_key=None,
            command=self._run_simulation,
            accent=True
        )
        self._run_card.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(10, 0))

        # Status summary at bottom
        self._create_status_summary(content)

    def _create_action_card(self, parent, title: str, description: str,
                            icon: str, status_key: str, command,
                            accent: bool = False) -> tk.Frame:
        """
        Create an action card widget.

        Args:
            parent: Parent widget
            title: Card title
            description: Card description
            icon: Icon character
            status_key: Key for status check ('meshes', 'config', 'robot', or None)
            command: Callback when clicked
            accent: If True, use accent color for button

        Returns:
            The card frame
        """
        project = self.app.current_project

        # Determine status
        has_item = False
        if status_key == "meshes":
            has_item = project.has_meshes
        elif status_key == "config":
            has_item = project.has_config
        elif status_key == "robot":
            has_item = project.has_robot_code

        # Card frame
        card = tk.Frame(
            parent,
            bg=Colors.BG_SECONDARY,
            cursor="hand2"
        )

        # Inner padding
        inner = tk.Frame(card, bg=Colors.BG_SECONDARY)
        inner.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

        # Top row: icon and status
        top_row = tk.Frame(inner, bg=Colors.BG_SECONDARY)
        top_row.pack(fill=tk.X)

        # Icon
        icon_label = tk.Label(
            top_row,
            text=icon,
            font=("Segoe UI", 24),
            fg=Colors.ACCENT_RED if accent else Colors.TEXT_PRIMARY,
            bg=Colors.BG_SECONDARY
        )
        icon_label.pack(side=tk.LEFT)

        # Status indicator (if applicable)
        if status_key:
            status_text = "\u2713" if has_item else "\u25CB"  # ✓ or ○
            status_color = Colors.SUCCESS if has_item else Colors.TEXT_MUTED
            status_label = tk.Label(
                top_row,
                text=status_text,
                font=("Segoe UI", 14),
                fg=status_color,
                bg=Colors.BG_SECONDARY
            )
            status_label.pack(side=tk.RIGHT)

        # Title
        title_label = tk.Label(
            inner,
            text=title,
            font=("Segoe UI", 12, "bold"),
            fg=Colors.ACCENT_RED if accent else Colors.TEXT_PRIMARY,
            bg=Colors.BG_SECONDARY,
            anchor=tk.W
        )
        title_label.pack(fill=tk.X, pady=(10, 5))

        # Description
        desc_label = tk.Label(
            inner,
            text=description,
            font=("Segoe UI", 10),
            fg=Colors.TEXT_MUTED,
            bg=Colors.BG_SECONDARY,
            anchor=tk.W,
            wraplength=200
        )
        desc_label.pack(fill=tk.X)

        # Bind click events to all elements
        for widget in [card, inner, icon_label, title_label, desc_label]:
            widget.bind("<Button-1>", lambda e, cmd=command: cmd())
            widget.bind("<Enter>", lambda e, c=card, i=inner: self._on_card_enter(c, i))
            widget.bind("<Leave>", lambda e, c=card, i=inner: self._on_card_leave(c, i))

        if status_key:
            status_label.bind("<Button-1>", lambda e, cmd=command: cmd())
            status_label.bind("<Enter>", lambda e, c=card, i=inner: self._on_card_enter(c, i))
            status_label.bind("<Leave>", lambda e, c=card, i=inner: self._on_card_leave(c, i))

        return card

    def _on_card_enter(self, card, inner):
        """Handle mouse enter on card."""
        card.configure(bg=Colors.BG_TERTIARY)
        inner.configure(bg=Colors.BG_TERTIARY)
        for child in inner.winfo_children():
            self._set_bg_recursive(child, Colors.BG_TERTIARY)

    def _on_card_leave(self, card, inner):
        """Handle mouse leave on card."""
        card.configure(bg=Colors.BG_SECONDARY)
        inner.configure(bg=Colors.BG_SECONDARY)
        for child in inner.winfo_children():
            self._set_bg_recursive(child, Colors.BG_SECONDARY)

    def _set_bg_recursive(self, widget, color):
        """Recursively set background color."""
        try:
            widget.configure(bg=color)
        except tk.TclError:
            pass
        for child in widget.winfo_children():
            self._set_bg_recursive(child, color)

    def _create_status_summary(self, parent):
        """Create status summary at bottom of screen."""
        project = self.app.current_project

        summary_frame = tk.Frame(parent, bg=Colors.BG_PRIMARY)
        summary_frame.pack(fill=tk.X, pady=(30, 0))

        # Check if ready to simulate
        if project.is_ready_to_simulate:
            status_text = "\u2713 Ready to simulate"
            status_color = Colors.SUCCESS
        else:
            missing = []
            if not project.has_meshes:
                missing.append("meshes")
            if not project.has_config:
                missing.append("config")
            if not project.has_robot_code:
                missing.append("robot code")
            status_text = f"Missing: {', '.join(missing)}"
            status_color = Colors.WARNING

        status_label = tk.Label(
            summary_frame,
            text=status_text,
            font=("Segoe UI", 11),
            fg=status_color,
            bg=Colors.BG_PRIMARY
        )
        status_label.pack(side=tk.LEFT)

        # Delete project button (right side, danger style)
        delete_btn = tk.Button(
            summary_frame,
            text="\U0001F5D1 Delete Project",  # Wastebasket emoji
            font=("Segoe UI", 10),
            fg=Colors.TEXT_PRIMARY,
            bg=Colors.ERROR_DARK,
            activebackground=Colors.ERROR,
            activeforeground=Colors.TEXT_PRIMARY,
            relief=tk.FLAT,
            padx=15,
            pady=5,
            cursor="hand2",
            command=self._delete_project
        )
        delete_btn.pack(side=tk.RIGHT)

        # Hover effects for delete button
        delete_btn.bind("<Enter>", lambda e: delete_btn.configure(bg=Colors.ERROR))
        delete_btn.bind("<Leave>", lambda e: delete_btn.configure(bg=Colors.ERROR_DARK))

    # === Action Handlers ===

    def _import_meshes(self):
        """Handle Import Mesh Files action."""
        files = filedialog.askopenfilenames(
            title="Select Mesh Files",
            filetypes=[
                ("Mesh files", "*.stl *.obj *.STL *.OBJ"),
                ("STL files", "*.stl *.STL"),
                ("OBJ files", "*.obj *.OBJ"),
                ("All files", "*.*")
            ]
        )

        if files:
            project = self.app.current_project
            paths = [Path(f) for f in files]
            count = self.app.project_manager.import_mesh_files(project, paths)

            if count > 0:
                messagebox.showinfo(
                    "Import Complete",
                    f"Imported {count} mesh file(s)"
                )
                # Refresh screen
                self._refresh()

    def _import_config(self):
        """Handle Import Config File action."""
        file = filedialog.askopenfilename(
            title="Select Config File",
            filetypes=[
                ("JSON files", "*.json"),
                ("All files", "*.*")
            ]
        )

        if file:
            project = self.app.current_project
            success = self.app.project_manager.import_config(project, Path(file))

            if success:
                messagebox.showinfo(
                    "Import Complete",
                    "Configuration file imported successfully"
                )
                self._refresh()
            else:
                messagebox.showerror(
                    "Import Failed",
                    "Could not import configuration file"
                )

    def _select_robot_code(self):
        """Handle Select Robot Code action."""
        folder = filedialog.askdirectory(
            title="Select Robot Code Folder"
        )

        if folder:
            project = self.app.current_project
            success = self.app.project_manager.set_robot_code_path(project, Path(folder))

            if success:
                messagebox.showinfo(
                    "Robot Code Selected",
                    f"Robot code path set to:\n{folder}"
                )
                self._refresh()
            else:
                messagebox.showerror(
                    "Invalid Folder",
                    "The selected folder does not exist or is invalid"
                )

    def _generate_from_step(self):
        """Handle Generate From STEP action."""
        # First, select STEP file
        step_file = filedialog.askopenfilename(
            title="Select STEP File",
            filetypes=[
                ("STEP files", "*.step *.stp *.STEP *.STP"),
                ("All files", "*.*")
            ]
        )

        if not step_file:
            return

        project = self.app.current_project

        # Launch CAD editor as subprocess (no console window)
        try:
            cmd = [
                sys.executable,
                "-m", "subsystemsim.cad.cad_editor",
                step_file,
                "--output", str(project.path)
            ]

            # Use CREATE_NO_WINDOW on Windows to hide console
            if sys.platform == 'win32':
                CREATE_NO_WINDOW = 0x08000000
                subprocess.Popen(cmd, creationflags=CREATE_NO_WINDOW)
            else:
                subprocess.Popen(cmd)

            messagebox.showinfo(
                "CAD Editor Launched",
                "The CAD editor has been opened in a new window.\n\n"
                "Define your links, joints, motors, and sensors,\n"
                "then use File > Generate Output to create the config.\n\n"
                "The editor will close automatically after generation."
            )

        except Exception as e:
            messagebox.showerror(
                "Launch Failed",
                f"Could not launch CAD editor:\n{e}"
            )

    def _run_simulation(self):
        """Handle Run Simulation action."""
        project = self.app.current_project

        if not project.is_ready_to_simulate:
            missing = []
            if not project.has_meshes:
                missing.append("mesh files")
            if not project.has_config:
                missing.append("configuration file")
            if not project.has_robot_code:
                missing.append("robot code path")

            messagebox.showwarning(
                "Cannot Run Simulation",
                f"Missing required items:\n\n" + "\n".join(f"- {m}" for m in missing)
            )
            return

        # Navigate to simulation screen
        from simplesim.screens import SimulationScreen
        self.navigate_to(SimulationScreen)

    def _delete_project(self):
        """Handle Delete Project action."""
        project = self.app.current_project
        if not project:
            return

        # Confirm deletion
        result = messagebox.askyesno(
            "Delete Project",
            f"Are you sure you want to delete '{project.name}'?\n\n"
            "This will permanently delete all project files including:\n"
            "- Mesh files\n"
            "- Configuration\n"
            "- Generated URDF\n\n"
            "This action cannot be undone.",
            icon='warning'
        )

        if not result:
            return

        # Delete the project
        try:
            self.app.project_manager.delete_project(project.id)
            self.app.set_current_project(None)

            messagebox.showinfo(
                "Project Deleted",
                f"Project '{project.name}' has been deleted."
            )

            # Navigate back to projects screen
            from simplesim.screens import ProjectsScreen
            # Clear the navigation stack and go to projects screen
            self.app.navigate_back()

        except Exception as e:
            messagebox.showerror(
                "Delete Failed",
                f"Could not delete project:\n{e}"
            )

    def _refresh(self):
        """Refresh the screen to show updated status."""
        # Destroy all children and rebuild content (keep same frame)
        for child in self.frame.winfo_children():
            child.destroy()
        # Rebuild content directly without creating new frame
        self.build()
