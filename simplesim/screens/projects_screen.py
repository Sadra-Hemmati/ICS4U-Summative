"""
Projects screen for SimpleSim.

Displays a list of existing projects and allows creating new ones.
"""

import tkinter as tk
from tkinter import ttk, simpledialog
from typing import TYPE_CHECKING, List

from .base_screen import BaseScreen
from simplesim.theming import Colors
from simplesim.widgets import ProjectCard

if TYPE_CHECKING:
    from simplesim.app import SimpleSimApp
    from simplesim.project import Project


class ProjectsScreen(BaseScreen):
    """
    Projects list screen.

    Features:
    - Scrollable list of project cards
    - Red "+" button to add new project
    - Back button to title screen
    """

    TITLE = "Projects"
    HAS_BACK_BUTTON = True

    def __init__(self, app: 'SimpleSimApp', container: tk.Frame):
        super().__init__(app, container)
        self._project_cards: List[ProjectCard] = []

    def build(self):
        """Build the projects screen UI."""
        # Navigation bar
        self.create_nav_bar(self.frame, title="Projects")

        # Main content area
        content = tk.Frame(self.frame, bg=Colors.BG_PRIMARY)
        content.pack(fill=tk.BOTH, expand=True, padx=40, pady=20)

        # Create scrollable frame for projects
        scroll_outer, self._scroll_inner = self.create_scrollable_frame(content)
        scroll_outer.pack(fill=tk.BOTH, expand=True)

        # Load and display projects
        self._load_projects()

        # Floating "+" button (bottom right)
        self._create_add_button()

    def _load_projects(self):
        """Load projects from manager and create cards."""
        # Clear all children of scroll inner (cards and empty state)
        for child in self._scroll_inner.winfo_children():
            child.destroy()
        self._project_cards.clear()

        # Get projects
        projects = self.app.project_manager.list_projects()

        if not projects:
            # Show empty state
            self._show_empty_state()
        else:
            # Create cards for each project
            for project in projects:
                card = ProjectCard(
                    self._scroll_inner,
                    project,
                    on_click=self._on_project_click
                )
                card.pack(fill=tk.X, pady=5)
                self._project_cards.append(card)

    def _show_empty_state(self):
        """Show message when no projects exist."""
        empty_frame = tk.Frame(self._scroll_inner, bg=Colors.BG_PRIMARY)
        empty_frame.pack(expand=True, fill=tk.BOTH, pady=100)

        # Icon (folder with plus)
        icon_label = tk.Label(
            empty_frame,
            text="\U0001F4C1",  # Folder emoji
            font=("Segoe UI", 48),
            fg=Colors.TEXT_MUTED,
            bg=Colors.BG_PRIMARY
        )
        icon_label.pack()

        # Message
        message = tk.Label(
            empty_frame,
            text="No projects yet",
            font=("Segoe UI", 18),
            fg=Colors.TEXT_SECONDARY,
            bg=Colors.BG_PRIMARY
        )
        message.pack(pady=(20, 10))

        # Sub-message
        sub_message = tk.Label(
            empty_frame,
            text="Click the + button to create your first project",
            font=("Segoe UI", 12),
            fg=Colors.TEXT_MUTED,
            bg=Colors.BG_PRIMARY
        )
        sub_message.pack()

    def _create_add_button(self):
        """Create the floating add button."""
        # Create a frame to position the button
        button_frame = tk.Frame(self.frame, bg=Colors.BG_PRIMARY)
        button_frame.place(relx=0.95, rely=0.95, anchor=tk.SE)

        # The "+" button
        add_btn = tk.Button(
            button_frame,
            text="+",
            font=("Segoe UI", 24, "bold"),
            fg=Colors.TEXT_PRIMARY,
            bg=Colors.ACCENT_RED,
            activebackground=Colors.ACCENT_RED_HOVER,
            activeforeground=Colors.TEXT_PRIMARY,
            relief=tk.FLAT,
            width=2,
            height=1,
            cursor="hand2",
            command=self._on_add_click
        )
        add_btn.pack()

        # Bind hover effects
        add_btn.bind("<Enter>", lambda e: add_btn.configure(bg=Colors.ACCENT_RED_HOVER))
        add_btn.bind("<Leave>", lambda e: add_btn.configure(bg=Colors.ACCENT_RED))

    def _on_project_click(self, project: 'Project'):
        """Handle project card click."""
        self.app.set_current_project(project)
        from simplesim.screens import ProjectOverviewScreen
        self.navigate_to(ProjectOverviewScreen)

    def _on_add_click(self):
        """Handle add button click."""
        # Show dialog to get project name
        name = self._show_new_project_dialog()

        if name:
            # Create project
            project = self.app.project_manager.create_project(name)

            # Refresh the list
            self._load_projects()

            # Optionally navigate to the new project
            self.app.set_current_project(project)
            from simplesim.screens import ProjectOverviewScreen
            self.navigate_to(ProjectOverviewScreen)

    def _show_new_project_dialog(self) -> str:
        """
        Show dialog to get new project name.

        Returns:
            The project name, or empty string if cancelled
        """
        # Create custom dialog for better styling
        dialog = NewProjectDialog(self.frame, self.app.project_manager)
        return dialog.result or ""

    def on_enter(self):
        """Refresh projects when entering screen."""
        self._load_projects()


class NewProjectDialog(tk.Toplevel):
    """Custom dialog for creating a new project."""

    def __init__(self, parent, project_manager):
        super().__init__(parent)

        self.project_manager = project_manager
        self.result = None

        # Configure dialog
        self.title("New Project")
        self.geometry("400x180")
        self.resizable(False, False)
        self.configure(bg=Colors.BG_SECONDARY)

        # Make modal
        self.transient(parent)
        self.grab_set()

        # Center on parent
        self.update_idletasks()
        x = parent.winfo_rootx() + (parent.winfo_width() - 400) // 2
        y = parent.winfo_rooty() + (parent.winfo_height() - 180) // 2
        self.geometry(f"+{x}+{y}")

        self._build_ui()

        # Focus entry
        self._name_entry.focus_set()

        # Wait for dialog to close
        self.wait_window()

    def _build_ui(self):
        """Build dialog UI."""
        # Content frame
        content = tk.Frame(self, bg=Colors.BG_SECONDARY, padx=30, pady=20)
        content.pack(fill=tk.BOTH, expand=True)

        # Title
        title = tk.Label(
            content,
            text="Create New Project",
            font=("Segoe UI", 14, "bold"),
            fg=Colors.TEXT_PRIMARY,
            bg=Colors.BG_SECONDARY
        )
        title.pack(anchor=tk.W)

        # Name label
        name_label = tk.Label(
            content,
            text="Project Name:",
            font=("Segoe UI", 10),
            fg=Colors.TEXT_SECONDARY,
            bg=Colors.BG_SECONDARY
        )
        name_label.pack(anchor=tk.W, pady=(15, 5))

        # Name entry
        self._name_entry = ttk.Entry(content, font=("Segoe UI", 11), width=40)
        self._name_entry.pack(fill=tk.X)
        self._name_entry.bind("<Return>", lambda e: self._on_create())
        self._name_entry.bind("<Escape>", lambda e: self._on_cancel())

        # Error label (hidden initially)
        self._error_label = tk.Label(
            content,
            text="",
            font=("Segoe UI", 9),
            fg=Colors.ERROR,
            bg=Colors.BG_SECONDARY
        )
        self._error_label.pack(anchor=tk.W, pady=(5, 0))

        # Button row
        button_row = tk.Frame(content, bg=Colors.BG_SECONDARY)
        button_row.pack(fill=tk.X, pady=(15, 0))

        # Cancel button
        cancel_btn = ttk.Button(
            button_row,
            text="Cancel",
            style="Secondary.TButton",
            command=self._on_cancel
        )
        cancel_btn.pack(side=tk.RIGHT, padx=(10, 0))

        # Create button
        create_btn = ttk.Button(
            button_row,
            text="Create",
            style="Accent.TButton",
            command=self._on_create
        )
        create_btn.pack(side=tk.RIGHT)

    def _on_create(self):
        """Handle create button click."""
        name = self._name_entry.get().strip()

        if not name:
            self._error_label.configure(text="Please enter a project name")
            return

        if len(name) > 50:
            self._error_label.configure(text="Name must be 50 characters or less")
            return

        # Check for duplicate names
        existing = self.project_manager.get_project_by_name(name)
        if existing:
            self._error_label.configure(text="A project with this name already exists")
            return

        self.result = name
        self.destroy()

    def _on_cancel(self):
        """Handle cancel button click."""
        self.result = None
        self.destroy()
