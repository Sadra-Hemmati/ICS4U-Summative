"""
Project card widget for SimpleSim.

Displays a project summary in a clickable card format.
"""

import tkinter as tk
from tkinter import ttk
from typing import Callable, TYPE_CHECKING
from datetime import datetime

from simplesim.theming import Colors
from simplesim.widgets.rounded_frame import RoundedFrame

if TYPE_CHECKING:
    from simplesim.project import Project


class ProjectCard(RoundedFrame):
    """
    A card widget displaying project information.

    Shows:
    - Project name
    - Last modified date
    - Status indicators (meshes, config, robot code)
    - Hover effect
    """

    def __init__(self, parent, project: 'Project', on_click: Callable[['Project'], None]):
        """
        Initialize the project card.

        Args:
            parent: Parent widget
            project: The project to display
            on_click: Callback when card is clicked
        """
        super().__init__(
            parent,
            bg=Colors.BG_SECONDARY,
            corner_radius=10
        )
        self.configure(cursor="hand2")

        self.project = project
        self.on_click = on_click

        self._build_ui()
        self._bind_events()

    def _build_ui(self):
        """Build the card UI."""
        # Add padding
        self.configure(padx=2, pady=2)

        # Inner frame for content
        inner = tk.Frame(self, bg=Colors.BG_SECONDARY)
        inner.pack(fill=tk.BOTH, expand=True, padx=15, pady=12)

        # Top row: Name and date
        top_row = tk.Frame(inner, bg=Colors.BG_SECONDARY)
        top_row.pack(fill=tk.X)

        # Project name
        name_label = tk.Label(
            top_row,
            text=self.project.name,
            font=("Segoe UI", 14, "bold"),
            fg=Colors.TEXT_PRIMARY,
            bg=Colors.BG_SECONDARY,
            anchor=tk.W
        )
        name_label.pack(side=tk.LEFT)

        # Modified date
        date_str = self._format_date(self.project.modified_at)
        date_label = tk.Label(
            top_row,
            text=date_str,
            font=("Segoe UI", 10),
            fg=Colors.TEXT_MUTED,
            bg=Colors.BG_SECONDARY
        )
        date_label.pack(side=tk.RIGHT)

        # Spacer
        tk.Frame(inner, bg=Colors.BG_SECONDARY, height=8).pack()

        # Status row
        status_row = tk.Frame(inner, bg=Colors.BG_SECONDARY)
        status_row.pack(fill=tk.X)

        # Store references for hover effect (initialize before adding status indicators)
        self._inner = inner
        self._labels = [name_label, date_label]

        # Status indicators
        self._add_status_indicator(
            status_row,
            "Meshes",
            self.project.has_meshes
        )
        self._add_status_indicator(
            status_row,
            "Config",
            self.project.has_config
        )
        self._add_status_indicator(
            status_row,
            "Robot Code",
            self.project.has_robot_code
        )

    def _add_status_indicator(self, parent: tk.Frame, label: str, is_present: bool):
        """Add a status indicator to the status row."""
        indicator_frame = tk.Frame(parent, bg=Colors.BG_SECONDARY)
        indicator_frame.pack(side=tk.LEFT, padx=(0, 15))

        # Icon (checkmark or circle)
        icon = "\u2713" if is_present else "\u25CB"  # ✓ or ○
        color = Colors.SUCCESS if is_present else Colors.TEXT_MUTED

        icon_label = tk.Label(
            indicator_frame,
            text=icon,
            font=("Segoe UI", 10),
            fg=color,
            bg=Colors.BG_SECONDARY
        )
        icon_label.pack(side=tk.LEFT)

        # Text
        text_label = tk.Label(
            indicator_frame,
            text=label,
            font=("Segoe UI", 10),
            fg=Colors.TEXT_SECONDARY,
            bg=Colors.BG_SECONDARY
        )
        text_label.pack(side=tk.LEFT, padx=(4, 0))

        # Store for hover effect
        self._labels.extend([icon_label, text_label, indicator_frame])

    def _format_date(self, dt: datetime) -> str:
        """Format datetime for display."""
        now = datetime.now()
        diff = now - dt

        if diff.days == 0:
            if diff.seconds < 3600:
                minutes = diff.seconds // 60
                return f"{minutes}m ago" if minutes > 0 else "Just now"
            else:
                hours = diff.seconds // 3600
                return f"{hours}h ago"
        elif diff.days == 1:
            return "Yesterday"
        elif diff.days < 7:
            return f"{diff.days} days ago"
        else:
            return dt.strftime("%b %d, %Y")

    def _bind_events(self):
        """Bind mouse events for hover and click."""
        # Bind to self and all children
        self.bind("<Enter>", self._on_enter)
        self.bind("<Leave>", self._on_leave)
        self.bind("<Button-1>", self._on_click)

        # Bind children
        for child in self.winfo_children():
            self._bind_recursive(child)

    def _bind_recursive(self, widget):
        """Recursively bind events to all children."""
        widget.bind("<Enter>", self._on_enter)
        widget.bind("<Leave>", self._on_leave)
        widget.bind("<Button-1>", self._on_click)

        for child in widget.winfo_children():
            self._bind_recursive(child)

    def _on_enter(self, event):
        """Handle mouse enter - show hover effect."""
        self.set_hover(True)
        self._set_all_backgrounds(Colors.BG_TERTIARY)

    def _on_leave(self, event):
        """Handle mouse leave - remove hover effect."""
        self.set_hover(False)
        self._set_all_backgrounds(Colors.BG_SECONDARY)

    def _set_all_backgrounds(self, color):
        """Recursively set background color on all children."""
        for child in self.winfo_children():
            # Skip the background canvas
            if child == self._bg_canvas:
                continue
            self._set_bg_recursive(child, color)

    def _set_bg_recursive(self, widget, color):
        """Recursively set background color."""
        try:
            widget.configure(bg=color)
        except tk.TclError:
            pass
        for child in widget.winfo_children():
            self._set_bg_recursive(child, color)

    def _on_click(self, event):
        """Handle click - trigger callback."""
        if self.on_click:
            self.on_click(self.project)
