"""
Animated gear widget for SimpleSim title screen.

Draws and animates rotating gears using tkinter Canvas.
"""

import tkinter as tk
import math
from typing import List, Tuple
from simplesim.theming import Colors


class GearAnimation(tk.Canvas):
    """
    Canvas widget that displays animated rotating gears.

    The gears rotate continuously when the animation is running,
    creating a subtle mechanical background effect.
    """

    def __init__(self, parent, **kwargs):
        """
        Initialize the gear animation canvas.

        Args:
            parent: Parent widget
            **kwargs: Additional canvas options
        """
        # Set defaults
        kwargs.setdefault('bg', Colors.BG_PRIMARY)
        kwargs.setdefault('highlightthickness', 0)

        super().__init__(parent, **kwargs)

        self._running = False
        self._angle = 0.0
        self._animation_id = None

        # Gear configurations: (x_ratio, y_ratio, radius, teeth, color, speed_mult)
        # x_ratio and y_ratio are relative to canvas size (0.0-1.0)
        self._gears: List[Tuple[float, float, int, int, str, float]] = [
            # Background gears (larger, slower, more transparent)
            (0.15, 0.25, 80, 12, Colors.GEAR_RED, 0.3),
            (0.85, 0.75, 100, 16, Colors.GEAR_BLACK, -0.25),
            (0.75, 0.20, 60, 10, Colors.BG_TERTIARY, 0.4),
            (0.25, 0.80, 70, 11, Colors.BG_TERTIARY, -0.35),
            # Smaller accent gears
            (0.10, 0.60, 40, 8, Colors.ACCENT_RED_DARK, 0.5),
            (0.90, 0.40, 45, 9, Colors.BORDER_LIGHT, -0.45),
            (0.50, 0.10, 35, 7, Colors.BG_SECONDARY, 0.6),
            (0.50, 0.90, 50, 10, Colors.BG_SECONDARY, -0.5),
        ]

        # Bind resize event
        self.bind('<Configure>', self._on_resize)

    def _on_resize(self, event):
        """Handle canvas resize."""
        self._draw_gears()

    def _draw_gear(self, cx: float, cy: float, radius: int, teeth: int,
                   color: str, angle: float):
        """
        Draw a single gear at the specified position.

        Args:
            cx: Center x coordinate
            cy: Center y coordinate
            radius: Outer radius of the gear
            teeth: Number of teeth
            color: Fill color
            angle: Current rotation angle in radians
        """
        # Gear parameters
        inner_radius = radius * 0.7
        tooth_height = radius * 0.15
        tooth_width = math.pi / teeth * 0.6

        # Generate gear polygon points
        points = []
        for i in range(teeth * 2):
            # Alternate between inner and outer radius
            if i % 2 == 0:
                # Outer point (tooth tip)
                r = radius
            else:
                # Inner point (between teeth)
                r = inner_radius

            # Calculate angle for this point
            point_angle = angle + (i * math.pi / teeth)

            # Add slight width to teeth
            if i % 2 == 0:
                # Tooth - add two points for flat top
                a1 = point_angle - tooth_width / 2
                a2 = point_angle + tooth_width / 2
                points.append(cx + r * math.cos(a1))
                points.append(cy + r * math.sin(a1))
                points.append(cx + r * math.cos(a2))
                points.append(cy + r * math.sin(a2))
            else:
                # Valley between teeth
                points.append(cx + r * math.cos(point_angle))
                points.append(cy + r * math.sin(point_angle))

        # Draw gear body
        if len(points) >= 6:
            self.create_polygon(
                points,
                fill=color,
                outline=color,
                width=1,
                tags='gear'
            )

        # Draw center hole
        hole_radius = inner_radius * 0.4
        self.create_oval(
            cx - hole_radius, cy - hole_radius,
            cx + hole_radius, cy + hole_radius,
            fill=Colors.BG_PRIMARY,
            outline=Colors.BG_PRIMARY,
            tags='gear'
        )

    def _draw_gears(self):
        """Draw all gears at their current positions."""
        self.delete('gear')

        width = self.winfo_width()
        height = self.winfo_height()

        if width <= 1 or height <= 1:
            return

        for x_ratio, y_ratio, radius, teeth, color, speed_mult in self._gears:
            cx = width * x_ratio
            cy = height * y_ratio
            gear_angle = self._angle * speed_mult
            self._draw_gear(cx, cy, radius, teeth, color, gear_angle)

    def _animate(self):
        """Animation loop."""
        if not self._running:
            return

        # Update angle
        self._angle += 0.02  # Rotation speed
        if self._angle > 2 * math.pi:
            self._angle -= 2 * math.pi

        # Redraw
        self._draw_gears()

        # Schedule next frame (~30 FPS)
        self._animation_id = self.after(33, self._animate)

    def start(self):
        """Start the gear animation."""
        if self._running:
            return

        self._running = True
        self._animate()

    def stop(self):
        """Stop the gear animation."""
        self._running = False
        if self._animation_id:
            self.after_cancel(self._animation_id)
            self._animation_id = None

    def is_running(self) -> bool:
        """Check if animation is currently running."""
        return self._running
