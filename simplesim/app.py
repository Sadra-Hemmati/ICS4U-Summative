"""
SimpleSim main application.

This is the entry point for the SimpleSim application.
Manages screen navigation and global state.
"""

import tkinter as tk
from tkinter import ttk
from typing import Type, Optional, List, Any
from pathlib import Path

from simplesim.theming import apply_dark_theme, Colors
from simplesim.project import ProjectManager, Project
from simplesim.screens.base_screen import BaseScreen


class SimpleSimApp:
    """
    Main SimpleSim application controller.

    Manages:
    - Window creation and configuration
    - Screen navigation (stack-based)
    - Global state (current project, etc.)
    - Theme application
    """

    WINDOW_TITLE = "SimpleSim"
    WINDOW_SIZE = (1200, 800)
    MIN_SIZE = (800, 600)

    def __init__(self, root: tk.Tk):
        """
        Initialize the SimpleSim application.

        Args:
            root: The root Tk window
        """
        self.root = root
        self._configure_window()

        # Apply dark theme
        apply_dark_theme(self.root)

        # Initialize managers
        self.project_manager = ProjectManager()

        # Current state
        self.current_project: Optional[Project] = None

        # Navigation stack
        self._screen_stack: List[BaseScreen] = []
        self._current_screen: Optional[BaseScreen] = None

        # Main container for screens
        self._container = tk.Frame(self.root, bg=Colors.BG_PRIMARY)
        self._container.pack(fill=tk.BOTH, expand=True)

        # Bind keyboard shortcuts
        self._bind_shortcuts()

        # Start at title screen
        from simplesim.screens import TitleScreen
        self.navigate_to(TitleScreen)

    def _configure_window(self):
        """Configure the main window."""
        self.root.title(self.WINDOW_TITLE)
        self.root.geometry(f"{self.WINDOW_SIZE[0]}x{self.WINDOW_SIZE[1]}")
        self.root.minsize(*self.MIN_SIZE)

        # Center window on screen
        self.root.update_idletasks()
        width = self.root.winfo_width()
        height = self.root.winfo_height()
        x = (self.root.winfo_screenwidth() // 2) - (width // 2)
        y = (self.root.winfo_screenheight() // 2) - (height // 2)
        self.root.geometry(f"{width}x{height}+{x}+{y}")

        # Set window icon (if available)
        try:
            icon_path = Path(__file__).parent.parent / "Assets" / "transparent-logo.png"
            if icon_path.exists():
                from PIL import Image, ImageTk
                icon = Image.open(icon_path)
                icon = icon.resize((32, 32), Image.Resampling.LANCZOS)
                self._icon = ImageTk.PhotoImage(icon)
                self.root.iconphoto(True, self._icon)
        except Exception:
            pass  # Icon loading is optional

        # Handle window close
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

    def _bind_shortcuts(self):
        """Bind keyboard shortcuts."""
        # Escape to go back
        self.root.bind("<Escape>", lambda e: self.navigate_back())

    def _on_close(self):
        """Handle window close event."""
        # Stop any running screens
        if self._current_screen:
            self._current_screen.on_exit()

        # Destroy window
        self.root.destroy()

    # === Navigation ===

    def navigate_to(self, screen_class: Type[BaseScreen], **kwargs):
        """
        Navigate to a new screen.

        Pushes the current screen to the stack and shows the new screen.

        Args:
            screen_class: The screen class to navigate to
            **kwargs: Arguments to pass to the screen
        """
        # Hide current screen (but keep it in stack)
        if self._current_screen:
            self._current_screen.hide()
            self._screen_stack.append(self._current_screen)

        # Create and show new screen
        new_screen = screen_class(self, self._container, **kwargs)
        self._current_screen = new_screen
        new_screen.show()

        # Update window title
        self.root.title(f"{self.WINDOW_TITLE} - {screen_class.TITLE}")

    def navigate_back(self):
        """
        Navigate back to the previous screen.

        Pops the current screen and shows the previous one from the stack.
        """
        if not self._screen_stack:
            return  # Nothing to go back to

        # Destroy current screen
        if self._current_screen:
            self._current_screen.destroy()

        # Pop and show previous screen
        self._current_screen = self._screen_stack.pop()
        self._current_screen.show()

        # Update window title
        self.root.title(f"{self.WINDOW_TITLE} - {self._current_screen.TITLE}")

    def navigate_to_root(self):
        """
        Navigate back to the title screen, clearing the navigation stack.
        """
        # Destroy all screens in stack
        for screen in self._screen_stack:
            screen.destroy()
        self._screen_stack.clear()

        if self._current_screen:
            self._current_screen.destroy()

        # Navigate to title
        from simplesim.screens import TitleScreen
        self._current_screen = TitleScreen(self, self._container)
        self._current_screen.show()
        self.root.title(f"{self.WINDOW_TITLE} - {TitleScreen.TITLE}")

    def replace_screen(self, screen_class: Type[BaseScreen], **kwargs):
        """
        Replace the current screen without adding to stack.

        Useful for refreshing a screen or switching between related screens.

        Args:
            screen_class: The screen class to show
            **kwargs: Arguments to pass to the screen
        """
        # Destroy current screen
        if self._current_screen:
            self._current_screen.destroy()

        # Create and show new screen
        new_screen = screen_class(self, self._container, **kwargs)
        self._current_screen = new_screen
        new_screen.show()

        # Update window title
        self.root.title(f"{self.WINDOW_TITLE} - {screen_class.TITLE}")

    # === State Management ===

    def set_current_project(self, project: Optional[Project]):
        """
        Set the current active project.

        Args:
            project: The project to set as current, or None to clear
        """
        self.current_project = project

    def get_current_project(self) -> Optional[Project]:
        """
        Get the current active project.

        Returns:
            The current Project or None
        """
        return self.current_project


def main():
    """Main entry point for SimpleSim."""
    root = tk.Tk()
    app = SimpleSimApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
