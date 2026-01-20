"""
Rounded frame widget for SimpleSim.

Provides a frame with rounded corners using Canvas as background layer.
"""

import tkinter as tk
from simplesim.theming import Colors


class RoundedFrame(tk.Frame):
    """
    A frame with rounded corners.

    Uses a Canvas placed behind as a background layer,
    keeping the frame's normal layout behavior intact.
    """

    def __init__(self, parent, bg=None, corner_radius=12, **kwargs):
        """
        Initialize the rounded frame.

        Args:
            parent: Parent widget
            bg: Background color (default: Colors.BG_SECONDARY)
            corner_radius: Radius of corners in pixels
            **kwargs: Additional frame options
        """
        self._bg_color = bg or Colors.BG_SECONDARY
        self._corner_radius = corner_radius
        self._hover_color = None
        self._parent_bg = Colors.BG_PRIMARY

        # Get parent background if possible
        try:
            self._parent_bg = parent.cget('bg')
        except (tk.TclError, AttributeError):
            pass

        # Remove bg from kwargs - we make the frame transparent
        kwargs.pop('bg', None)
        kwargs.pop('background', None)

        super().__init__(parent, bg=self._bg_color, **kwargs)

        # Create canvas for rounded background
        self._bg_canvas = tk.Canvas(
            self,
            bg=self._parent_bg,
            highlightthickness=0
        )
        # Place canvas to fill entire frame, behind content
        self._bg_canvas.place(x=0, y=0, relwidth=1, relheight=1)
        # Use tk.Misc.lower to lower the canvas widget (not canvas items)
        tk.Misc.lower(self._bg_canvas)

        # Bind resize to redraw
        self.bind('<Configure>', self._on_resize)

    def _draw_rounded_rect(self):
        """Draw the rounded rectangle background."""
        self._bg_canvas.delete('all')

        width = self.winfo_width()
        height = self.winfo_height()

        if width <= 1 or height <= 1:
            return

        r = min(self._corner_radius, width // 2, height // 2)
        color = self._hover_color or self._bg_color

        # Draw rounded rectangle using arcs and rectangles
        # This is more reliable than polygon for clean corners

        # Four corner circles (as arcs)
        self._bg_canvas.create_arc(0, 0, r * 2, r * 2, start=90, extent=90,
                                    fill=color, outline=color)
        self._bg_canvas.create_arc(width - r * 2, 0, width, r * 2, start=0, extent=90,
                                    fill=color, outline=color)
        self._bg_canvas.create_arc(0, height - r * 2, r * 2, height, start=180, extent=90,
                                    fill=color, outline=color)
        self._bg_canvas.create_arc(width - r * 2, height - r * 2, width, height, start=270, extent=90,
                                    fill=color, outline=color)

        # Fill rectangles
        self._bg_canvas.create_rectangle(r, 0, width - r, height, fill=color, outline=color)
        self._bg_canvas.create_rectangle(0, r, width, height - r, fill=color, outline=color)

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

        # Update frame background for children
        new_bg = self._hover_color or self._bg_color
        self.configure(bg=new_bg)

    def configure_bg(self, color):
        """Change the background color."""
        self._bg_color = color
        self._draw_rounded_rect()
        self.configure(bg=color)


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
