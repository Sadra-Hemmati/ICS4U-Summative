"""
SimpleSim ttk style configuration.

Applies a dark theme with red accents to all tkinter/ttk widgets.
"""

import tkinter as tk
from tkinter import ttk
from .colors import Colors


def apply_dark_theme(root: tk.Tk):
    """
    Apply the SimpleSim dark theme to the application.

    Args:
        root: The root Tk window
    """
    # Configure root window
    root.configure(bg=Colors.BG_PRIMARY)

    # Configure ttk styles
    configure_styles()


def configure_styles():
    """Configure all ttk widget styles for dark theme."""
    style = ttk.Style()

    # Use clam theme as base (most customizable)
    style.theme_use('clam')

    # === Frame Styles ===
    style.configure(
        "TFrame",
        background=Colors.BG_PRIMARY
    )
    style.configure(
        "Card.TFrame",
        background=Colors.BG_SECONDARY
    )
    style.configure(
        "Elevated.TFrame",
        background=Colors.BG_TERTIARY
    )

    # === Label Styles ===
    style.configure(
        "TLabel",
        background=Colors.BG_PRIMARY,
        foreground=Colors.TEXT_PRIMARY,
        font=("Segoe UI", 10)
    )
    style.configure(
        "Title.TLabel",
        background=Colors.BG_PRIMARY,
        foreground=Colors.TEXT_PRIMARY,
        font=("Segoe UI", 28, "bold")
    )
    style.configure(
        "Header.TLabel",
        background=Colors.BG_PRIMARY,
        foreground=Colors.TEXT_PRIMARY,
        font=("Segoe UI", 18, "bold")
    )
    style.configure(
        "Subheader.TLabel",
        background=Colors.BG_PRIMARY,
        foreground=Colors.TEXT_SECONDARY,
        font=("Segoe UI", 12)
    )
    style.configure(
        "Muted.TLabel",
        background=Colors.BG_PRIMARY,
        foreground=Colors.TEXT_MUTED,
        font=("Segoe UI", 10)
    )
    style.configure(
        "Card.TLabel",
        background=Colors.BG_SECONDARY,
        foreground=Colors.TEXT_PRIMARY,
        font=("Segoe UI", 10)
    )
    style.configure(
        "CardTitle.TLabel",
        background=Colors.BG_SECONDARY,
        foreground=Colors.TEXT_PRIMARY,
        font=("Segoe UI", 12, "bold")
    )
    # Header on secondary background
    style.configure(
        "CardHeader.TLabel",
        background=Colors.BG_SECONDARY,
        foreground=Colors.TEXT_PRIMARY,
        font=("Segoe UI", 18, "bold")
    )
    # Muted text on secondary background
    style.configure(
        "CardMuted.TLabel",
        background=Colors.BG_SECONDARY,
        foreground=Colors.TEXT_MUTED,
        font=("Segoe UI", 10)
    )
    # Subheader on secondary background
    style.configure(
        "CardSubheader.TLabel",
        background=Colors.BG_SECONDARY,
        foreground=Colors.TEXT_SECONDARY,
        font=("Segoe UI", 12)
    )
    style.configure(
        "Success.TLabel",
        background=Colors.BG_PRIMARY,
        foreground=Colors.SUCCESS,
        font=("Segoe UI", 10)
    )
    style.configure(
        "Warning.TLabel",
        background=Colors.BG_PRIMARY,
        foreground=Colors.WARNING,
        font=("Segoe UI", 10)
    )
    style.configure(
        "Error.TLabel",
        background=Colors.BG_PRIMARY,
        foreground=Colors.ERROR,
        font=("Segoe UI", 10)
    )

    # === Button Styles ===
    style.configure(
        "TButton",
        background=Colors.BG_TERTIARY,
        foreground=Colors.TEXT_PRIMARY,
        borderwidth=0,
        focuscolor=Colors.ACCENT_RED,
        font=("Segoe UI", 10),
        padding=(15, 8)
    )
    style.map(
        "TButton",
        background=[
            ("active", Colors.BG_TERTIARY),
            ("pressed", Colors.BG_SECONDARY)
        ],
        foreground=[
            ("disabled", Colors.TEXT_MUTED)
        ]
    )

    # Primary accent button (red)
    style.configure(
        "Accent.TButton",
        background=Colors.ACCENT_RED,
        foreground=Colors.TEXT_PRIMARY,
        borderwidth=0,
        font=("Segoe UI", 12, "bold"),
        padding=(20, 12)
    )
    style.map(
        "Accent.TButton",
        background=[
            ("active", Colors.ACCENT_RED_HOVER),
            ("pressed", Colors.ACCENT_RED_DARK)
        ]
    )

    # Large accent button (for Start button)
    style.configure(
        "LargeAccent.TButton",
        background=Colors.ACCENT_RED,
        foreground=Colors.TEXT_PRIMARY,
        borderwidth=0,
        font=("Segoe UI", 16, "bold"),
        padding=(40, 15)
    )
    style.map(
        "LargeAccent.TButton",
        background=[
            ("active", Colors.ACCENT_RED_HOVER),
            ("pressed", Colors.ACCENT_RED_DARK)
        ]
    )

    # Secondary button (outline style effect)
    style.configure(
        "Secondary.TButton",
        background=Colors.BG_SECONDARY,
        foreground=Colors.TEXT_PRIMARY,
        borderwidth=1,
        font=("Segoe UI", 10),
        padding=(15, 8)
    )
    style.map(
        "Secondary.TButton",
        background=[
            ("active", Colors.BG_TERTIARY),
            ("pressed", Colors.BG_PRIMARY)
        ]
    )

    # Action button (for project overview)
    style.configure(
        "Action.TButton",
        background=Colors.BG_SECONDARY,
        foreground=Colors.TEXT_PRIMARY,
        borderwidth=0,
        font=("Segoe UI", 11),
        padding=(20, 15)
    )
    style.map(
        "Action.TButton",
        background=[
            ("active", Colors.BG_TERTIARY),
            ("pressed", Colors.ACCENT_RED_DARK)
        ]
    )

    # Danger button (Stop, Delete)
    style.configure(
        "Danger.TButton",
        background=Colors.ERROR,
        foreground=Colors.TEXT_PRIMARY,
        borderwidth=0,
        font=("Segoe UI", 10, "bold"),
        padding=(15, 8)
    )
    style.map(
        "Danger.TButton",
        background=[
            ("active", Colors.ERROR_DARK),
            ("pressed", "#8B0000")
        ]
    )

    # === Entry Styles ===
    style.configure(
        "TEntry",
        fieldbackground=Colors.BG_TERTIARY,
        foreground=Colors.TEXT_PRIMARY,
        insertcolor=Colors.TEXT_PRIMARY,
        borderwidth=1,
        padding=8
    )
    style.map(
        "TEntry",
        fieldbackground=[
            ("focus", Colors.BG_TERTIARY),
            ("disabled", Colors.BG_SECONDARY)
        ],
        bordercolor=[
            ("focus", Colors.ACCENT_RED)
        ]
    )

    # === Notebook (Tabs) Styles ===
    style.configure(
        "TNotebook",
        background=Colors.BG_PRIMARY,
        borderwidth=0
    )
    style.configure(
        "TNotebook.Tab",
        background=Colors.BG_SECONDARY,
        foreground=Colors.TEXT_SECONDARY,
        padding=(15, 8),
        font=("Segoe UI", 10)
    )
    style.map(
        "TNotebook.Tab",
        background=[
            ("selected", Colors.BG_TERTIARY)
        ],
        foreground=[
            ("selected", Colors.TEXT_PRIMARY)
        ],
        expand=[
            ("selected", [1, 1, 1, 0])
        ]
    )

    # === Scrollbar Styles ===
    style.configure(
        "Vertical.TScrollbar",
        background=Colors.SCROLLBAR_BG,
        troughcolor=Colors.BG_SECONDARY,
        borderwidth=0,
        arrowsize=0
    )
    style.map(
        "Vertical.TScrollbar",
        background=[
            ("active", Colors.SCROLLBAR_THUMB_HOVER),
            ("!active", Colors.SCROLLBAR_THUMB)
        ]
    )

    # === Separator Styles ===
    style.configure(
        "TSeparator",
        background=Colors.BORDER_LIGHT
    )

    # === LabelFrame Styles ===
    style.configure(
        "TLabelframe",
        background=Colors.BG_PRIMARY,
        bordercolor=Colors.BORDER_LIGHT,
        borderwidth=1
    )
    style.configure(
        "TLabelframe.Label",
        background=Colors.BG_PRIMARY,
        foreground=Colors.TEXT_PRIMARY,
        font=("Segoe UI", 10, "bold")
    )

    # === Combobox Styles ===
    style.configure(
        "TCombobox",
        fieldbackground=Colors.BG_TERTIARY,
        background=Colors.BG_TERTIARY,
        foreground=Colors.TEXT_PRIMARY,
        arrowcolor=Colors.TEXT_PRIMARY,
        borderwidth=1,
        padding=5
    )
    style.map(
        "TCombobox",
        fieldbackground=[
            ("readonly", Colors.BG_TERTIARY)
        ],
        selectbackground=[
            ("readonly", Colors.ACCENT_RED)
        ]
    )

    # === Checkbutton Styles ===
    style.configure(
        "TCheckbutton",
        background=Colors.BG_PRIMARY,
        foreground=Colors.TEXT_PRIMARY,
        font=("Segoe UI", 10)
    )
    style.map(
        "TCheckbutton",
        background=[
            ("active", Colors.BG_PRIMARY)
        ],
        indicatorcolor=[
            ("selected", Colors.ACCENT_RED),
            ("!selected", Colors.BG_TERTIARY)
        ]
    )

    # === Progressbar Styles ===
    style.configure(
        "TProgressbar",
        background=Colors.ACCENT_RED,
        troughcolor=Colors.BG_SECONDARY,
        borderwidth=0
    )
