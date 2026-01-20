"""
Title screen for SimpleSim.

Displays the logo, animated gears background, and a Start button.
"""

import tkinter as tk
from tkinter import ttk
from pathlib import Path
from typing import TYPE_CHECKING

from .base_screen import BaseScreen
from simplesim.theming import Colors
from simplesim.widgets import GearAnimation, RoundedFrame

if TYPE_CHECKING:
    from simplesim.app import SimpleSimApp


class TitleScreen(BaseScreen):
    """
    Title/splash screen for SimpleSim.

    Features:
    - Animated gears in the background
    - Centered logo
    - Large "Start" button
    """

    TITLE = "Welcome"
    HAS_BACK_BUTTON = False  # Title screen is the root

    def __init__(self, app: 'SimpleSimApp', container: tk.Frame):
        super().__init__(app, container)
        self._logo_image = None
        self._gear_animation = None

    def build(self):
        """Build the title screen UI."""
        # Animated gears background (covers entire screen)
        self._gear_animation = GearAnimation(self.frame)
        self._gear_animation.place(relx=0, rely=0, relwidth=1, relheight=1)

        # Center container (over the gears)
        center_frame = tk.Frame(self.frame, bg=Colors.BG_PRIMARY)
        center_frame.place(relx=0.5, rely=0.5, anchor=tk.CENTER)

        # Add semi-transparent background to center content
        # Using a rounded frame with padding for the "card" effect
        content_frame = RoundedFrame(
            center_frame,
            bg=Colors.BG_SECONDARY,
            corner_radius=16
        )
        content_frame.pack()

        # Inner padding frame (RoundedFrame doesn't support padx/pady directly)
        inner_padding = tk.Frame(content_frame, bg=Colors.BG_SECONDARY)
        inner_padding.pack(padx=60, pady=40)

        # Load and display logo
        self._load_logo(inner_padding)

        # Spacer
        tk.Frame(inner_padding, bg=Colors.BG_SECONDARY, height=30).pack()

        # Start button
        start_btn = ttk.Button(
            inner_padding,
            text="Start",
            style="LargeAccent.TButton",
            command=self._on_start
        )
        start_btn.pack()

        # Version info at bottom
        version_label = ttk.Label(
            self.frame,
            text="v1.0.0",
            style="Muted.TLabel"
        )
        version_label.place(relx=0.98, rely=0.98, anchor=tk.SE)

    def _load_logo(self, parent: tk.Frame):
        """Load and display the logo image."""
        try:
            from PIL import Image, ImageTk

            # Find logo file
            logo_path = Path(__file__).parent.parent.parent / "Assets" / "transparent-logo.png"

            if logo_path.exists():
                # Load and resize logo
                logo = Image.open(logo_path)

                # Calculate size (max 400px wide, maintain aspect ratio)
                max_width = 400
                ratio = max_width / logo.width
                new_size = (max_width, int(logo.height * ratio))
                logo = logo.resize(new_size, Image.Resampling.LANCZOS)

                # Convert to PhotoImage
                self._logo_image = ImageTk.PhotoImage(logo)

                # Display in label
                logo_label = tk.Label(
                    parent,
                    image=self._logo_image,
                    bg=Colors.BG_SECONDARY
                )
                logo_label.pack()
            else:
                self._show_text_logo(parent)

        except ImportError:
            # Pillow not installed, show text logo
            self._show_text_logo(parent)
        except Exception as e:
            print(f"Could not load logo: {e}")
            self._show_text_logo(parent)

    def _show_text_logo(self, parent: tk.Frame):
        """Show text-based logo as fallback."""
        # "Simple" in white
        title_frame = tk.Frame(parent, bg=Colors.BG_SECONDARY)
        title_frame.pack()

        simple_label = tk.Label(
            title_frame,
            text="Simple",
            font=("Segoe UI", 48, "bold"),
            fg=Colors.TEXT_PRIMARY,
            bg=Colors.BG_SECONDARY
        )
        simple_label.pack(side=tk.LEFT)

        # "Sim" in red
        sim_label = tk.Label(
            title_frame,
            text="Sim",
            font=("Segoe UI", 48, "bold"),
            fg=Colors.ACCENT_RED,
            bg=Colors.BG_SECONDARY
        )
        sim_label.pack(side=tk.LEFT)

    def _on_start(self):
        """Handle Start button click."""
        from simplesim.screens import ProjectsScreen
        self.navigate_to(ProjectsScreen)

    def on_enter(self):
        """Start animations when screen becomes visible."""
        if self._gear_animation:
            self._gear_animation.start()

    def on_exit(self):
        """Stop animations when leaving screen."""
        if self._gear_animation:
            self._gear_animation.stop()
