"""
Rounded frame widget for SimpleSim.

Provides a frame with rounded corners using Canvas.
"""

import tkinter as tk
from simplesim.theming import Colors


class RoundedFrame(tk.Canvas):
    """
    A frame with rounded corners.

    Uses a Canvas to draw a rounded rectangle background,
    with a frame placed on top for content.
    """

    def __init__(self, parent, bg=None, corner_radius=12, **kwargs):
        """
        Initialize the rounded frame.

        Args:
            parent: Parent widget
            bg: Background color (default: Colors.BG_SECONDARY)
            corner_radius: Radius of corners in pixels
            **kwargs: Additional canvas options
        """
        self._bg_color = bg or Colors.BG_SECONDARY
        self._corner_radius = corner_radius
        self._hover_color = None

        # Remove bg from kwargs if present (we handle it ourselves)
        kwargs.pop('bg', None)
        kwargs.pop('background', None)

        super().__init__(
            parent,
            bg=Colors.BG_PRIMARY,
            highlightthickness=0,
            **kwargs
        )

        # Create inner frame for content
        self.inner = tk.Frame(self, bg=self._bg_color)

        # Bind resize to redraw
        self.bind('<Configure>', self._on_resize)

        # Draw initial background
        self._draw_rounded_rect()

    def _draw_rounded_rect(self):
        """Draw the rounded rectangle background."""
        self.delete('bg')

        width = self.winfo_width()
        height = self.winfo_height()

        if width <= 1 or height <= 1:
            return

        r = self._corner_radius
        color = self._hover_color or self._bg_color

        # Draw rounded rectangle using polygon with arcs
        # This creates a smooth rounded rectangle
        points = []

        # Top-left corner
        for i in range(r + 1):
            x = r - r * (1 - (i / r) ** 2) ** 0.5
            points.append((x, r - i))

        # Top-right corner
        for i in range(r + 1):
            x = width - r + r * (1 - ((r - i) / r) ** 2) ** 0.5
            points.append((x, i))

        # Bottom-right corner
        for i in range(r + 1):
            x = width - r + r * (1 - (i / r) ** 2) ** 0.5
            points.append((x, height - r + i))

        # Bottom-left corner
        for i in range(r + 1):
            x = r - r * (1 - ((r - i) / r) ** 2) ** 0.5
            points.append((x, height - i))

        # Flatten points for create_polygon
        flat_points = [coord for point in points for coord in point]

        self.create_polygon(
            flat_points,
            fill=color,
            outline=color,
            smooth=True,
            tags='bg'
        )

        # Place inner frame on top
        self.create_window(
            self._corner_radius // 2,
            self._corner_radius // 2,
            window=self.inner,
            anchor='nw',
            width=width - self._corner_radius,
            height=height - self._corner_radius,
            tags='content'
        )

    def _on_resize(self, event):
        """Handle resize event."""
        self._draw_rounded_rect()

    def set_hover(self, hovering: bool):
        """Set hover state for visual feedback."""
        if hovering:
            self._hover_color = Colors.BG_TERTIARY
        else:
            self._hover_color = None
        self._draw_rounded_rect()

        # Update inner frame background
        new_bg = self._hover_color or self._bg_color
        self.inner.configure(bg=new_bg)
        self._update_children_bg(self.inner, new_bg)

    def _update_children_bg(self, widget, color):
        """Recursively update background color of children."""
        for child in widget.winfo_children():
            try:
                child.configure(bg=color)
            except tk.TclError:
                pass
            self._update_children_bg(child, color)

    def configure_bg(self, color):
        """Change the background color."""
        self._bg_color = color
        self._draw_rounded_rect()
        self.inner.configure(bg=color)


class RoundedButton(tk.Canvas):
    """
    A button with rounded corners.
    """

    def __init__(self, parent, text="", command=None, bg=None, fg=None,
                 hover_bg=None, corner_radius=8, font=None, padx=20, pady=10,
                 **kwargs):
        """
        Initialize the rounded button.

        Args:
            parent: Parent widget
            text: Button text
            command: Click callback
            bg: Background color
            fg: Text color
            hover_bg: Hover background color
            corner_radius: Corner radius
            font: Text font
            padx: Horizontal padding
            pady: Vertical padding
        """
        self._bg_color = bg or Colors.BG_TERTIARY
        self._fg_color = fg or Colors.TEXT_PRIMARY
        self._hover_bg = hover_bg or Colors.BG_SECONDARY
        self._corner_radius = corner_radius
        self._text = text
        self._command = command
        self._font = font or ("Segoe UI", 10)
        self._padx = padx
        self._pady = pady
        self._is_hovering = False

        # Calculate size based on text
        super().__init__(
            parent,
            bg=Colors.BG_PRIMARY,
            highlightthickness=0,
            cursor="hand2",
            **kwargs
        )

        # Bind events
        self.bind('<Configure>', self._on_resize)
        self.bind('<Enter>', self._on_enter)
        self.bind('<Leave>', self._on_leave)
        self.bind('<Button-1>', self._on_click)

        self._draw()

    def _draw(self):
        """Draw the button."""
        self.delete('all')

        width = self.winfo_width()
        height = self.winfo_height()

        if width <= 1 or height <= 1:
            return

        r = self._corner_radius
        color = self._hover_bg if self._is_hovering else self._bg_color

        # Draw rounded rectangle
        self.create_oval(0, 0, r * 2, r * 2, fill=color, outline=color)
        self.create_oval(width - r * 2, 0, width, r * 2, fill=color, outline=color)
        self.create_oval(0, height - r * 2, r * 2, height, fill=color, outline=color)
        self.create_oval(width - r * 2, height - r * 2, width, height, fill=color, outline=color)
        self.create_rectangle(r, 0, width - r, height, fill=color, outline=color)
        self.create_rectangle(0, r, width, height - r, fill=color, outline=color)

        # Draw text
        self.create_text(
            width // 2,
            height // 2,
            text=self._text,
            fill=self._fg_color,
            font=self._font
        )

    def _on_resize(self, event):
        self._draw()

    def _on_enter(self, event):
        self._is_hovering = True
        self._draw()

    def _on_leave(self, event):
        self._is_hovering = False
        self._draw()

    def _on_click(self, event):
        if self._command:
            self._command()
