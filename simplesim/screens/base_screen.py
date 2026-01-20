"""
Base screen class for SimpleSim.

All screens inherit from this abstract base class which provides:
- Standard lifecycle methods (build, on_enter, on_exit)
- Navigation helpers
- Common UI patterns
"""

import tkinter as tk
from tkinter import ttk
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from simplesim.app import SimpleSimApp


class BaseScreen(ABC):
    """
    Abstract base class for all SimpleSim screens.

    Lifecycle:
    1. __init__() - Store references, don't build UI yet
    2. build() - Create all widgets (called once)
    3. on_enter() - Called when screen becomes visible
    4. on_exit() - Called when navigating away
    """

    # Override in subclasses to set screen title
    TITLE = "SimpleSim"

    # Override to True if this screen should have a back button
    HAS_BACK_BUTTON = True

    def __init__(self, app: 'SimpleSimApp', container: tk.Frame):
        """
        Initialize the screen.

        Args:
            app: The main SimpleSimApp instance
            container: The parent frame to place this screen in
        """
        self.app = app
        self.container = container
        self.frame: tk.Frame = None
        self._built = False

    def _ensure_built(self):
        """Ensure the screen UI has been built."""
        if not self._built:
            self._create_frame()
            self.build()
            self._built = True

    def _create_frame(self):
        """Create the main frame for this screen."""
        from simplesim.theming import Colors
        self.frame = tk.Frame(
            self.container,
            bg=Colors.BG_PRIMARY
        )

    @abstractmethod
    def build(self):
        """
        Build the screen UI.

        Called once when the screen is first shown.
        Create all widgets and layout here.
        """
        pass

    def on_enter(self):
        """
        Called when this screen becomes visible.

        Override to start animations, refresh data, etc.
        """
        pass

    def on_exit(self):
        """
        Called when navigating away from this screen.

        Override to stop animations, save state, cleanup, etc.
        """
        pass

    def show(self):
        """Show this screen."""
        self._ensure_built()
        self.frame.pack(fill=tk.BOTH, expand=True)
        self.on_enter()

    def hide(self):
        """Hide this screen."""
        self.on_exit()
        if self.frame:
            self.frame.pack_forget()

    def destroy(self):
        """Destroy this screen and free resources."""
        self.on_exit()
        if self.frame:
            self.frame.destroy()
            self.frame = None
        self._built = False

    # === Navigation Helpers ===

    def navigate_to(self, screen_class, **kwargs):
        """
        Navigate to another screen.

        Args:
            screen_class: The screen class to navigate to
            **kwargs: Arguments to pass to the screen
        """
        self.app.navigate_to(screen_class, **kwargs)

    def navigate_back(self):
        """Navigate back to the previous screen."""
        self.app.navigate_back()

    # === Common UI Components ===

    def create_nav_bar(self, parent: tk.Frame, title: str = None,
                       show_back: bool = None) -> tk.Frame:
        """
        Create a navigation bar with optional back button and title.

        Args:
            parent: Parent frame
            title: Title text (defaults to self.TITLE)
            show_back: Whether to show back button (defaults to self.HAS_BACK_BUTTON)

        Returns:
            The navigation bar frame
        """
        from simplesim.theming import Colors

        if title is None:
            title = self.TITLE
        if show_back is None:
            show_back = self.HAS_BACK_BUTTON

        nav_frame = tk.Frame(parent, bg=Colors.BG_SECONDARY, height=60)
        nav_frame.pack(fill=tk.X)
        nav_frame.pack_propagate(False)

        # Inner container for padding
        inner = tk.Frame(nav_frame, bg=Colors.BG_SECONDARY)
        inner.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)

        # Back button
        if show_back:
            back_btn = ttk.Button(
                inner,
                text="\u2190 Back",
                style="Secondary.TButton",
                command=self.navigate_back
            )
            back_btn.pack(side=tk.LEFT)

        # Title
        title_label = ttk.Label(
            inner,
            text=title,
            style="CardHeader.TLabel"
        )
        if show_back:
            title_label.pack(side=tk.LEFT, padx=(20, 0))
        else:
            title_label.pack(side=tk.LEFT)

        return nav_frame

    def create_scrollable_frame(self, parent: tk.Frame) -> tuple:
        """
        Create a scrollable frame.

        Args:
            parent: Parent frame

        Returns:
            Tuple of (outer_frame, scrollable_inner_frame)
        """
        from simplesim.theming import Colors

        # Outer container
        outer = tk.Frame(parent, bg=Colors.BG_PRIMARY)

        # Canvas for scrolling
        canvas = tk.Canvas(
            outer,
            bg=Colors.BG_PRIMARY,
            highlightthickness=0
        )
        scrollbar = ttk.Scrollbar(
            outer,
            orient=tk.VERTICAL,
            command=canvas.yview
        )
        canvas.configure(yscrollcommand=scrollbar.set)

        # Inner frame for content
        inner = tk.Frame(canvas, bg=Colors.BG_PRIMARY)
        inner_id = canvas.create_window((0, 0), window=inner, anchor=tk.NW)

        # Configure scrolling
        def configure_scroll(event):
            canvas.configure(scrollregion=canvas.bbox("all"))
            # Make inner frame fill canvas width
            canvas.itemconfig(inner_id, width=canvas.winfo_width())

        inner.bind("<Configure>", configure_scroll)
        canvas.bind("<Configure>", lambda e: canvas.itemconfig(inner_id, width=e.width))

        # Mouse wheel scrolling
        def on_mousewheel(event):
            canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

        canvas.bind_all("<MouseWheel>", on_mousewheel)

        # Pack
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Store canvas reference for cleanup
        inner._canvas = canvas

        return outer, inner
