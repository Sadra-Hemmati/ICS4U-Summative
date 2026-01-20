"""
SimpleSim color constants.

Color scheme inspired by WPILib tools and the SimpleSim logo:
- Dark grays for backgrounds
- Red accents (#B22234) matching the logo
- White/light gray text for readability
"""


class Colors:
    """Centralized color constants for SimpleSim theming."""

    # === Background Colors (Dark Grays) ===
    BG_PRIMARY = "#1e1e1e"      # Main window background
    BG_SECONDARY = "#2d2d2d"    # Cards, panels, elevated surfaces
    BG_TERTIARY = "#3d3d3d"     # Hover states, input fields
    BG_DARK = "#141414"         # Even darker for contrast

    # === Accent Colors (Red from Logo) ===
    ACCENT_RED = "#B22234"       # Primary accent (buttons, highlights)
    ACCENT_RED_HOVER = "#CC2840" # Hover state
    ACCENT_RED_DARK = "#8B1A2A"  # Pressed/active state
    ACCENT_RED_LIGHT = "#D64D5D" # Light variant for subtle highlights

    # === Text Colors ===
    TEXT_PRIMARY = "#FFFFFF"     # Main text (white)
    TEXT_SECONDARY = "#B0B0B0"   # Secondary text (light gray)
    TEXT_MUTED = "#707070"       # Disabled/hint text (dark gray)
    TEXT_DARK = "#1A1A1A"        # Text on light backgrounds

    # === Border Colors ===
    BORDER_LIGHT = "#4d4d4d"     # Subtle borders
    BORDER_DARK = "#333333"      # Darker borders
    BORDER_FOCUS = "#B22234"     # Focus rings (accent)

    # === Semantic Colors ===
    SUCCESS = "#4CAF50"          # Green for success states
    SUCCESS_DARK = "#2E7D32"     # Darker green
    WARNING = "#FF9800"          # Orange for warnings
    WARNING_DARK = "#E65100"     # Darker orange
    ERROR = "#F44336"            # Red for errors
    ERROR_DARK = "#C62828"       # Darker red
    INFO = "#2196F3"             # Blue for info

    # === Special Colors ===
    GEAR_RED = "#B22234"         # Red gear in logo
    GEAR_BLACK = "#1A1A1A"       # Black gear in logo

    # === Scrollbar Colors ===
    SCROLLBAR_BG = "#2d2d2d"
    SCROLLBAR_THUMB = "#4d4d4d"
    SCROLLBAR_THUMB_HOVER = "#5d5d5d"

    @classmethod
    def rgb(cls, hex_color: str) -> tuple:
        """Convert hex color to RGB tuple (0-255)."""
        hex_color = hex_color.lstrip('#')
        return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))

    @classmethod
    def rgb_float(cls, hex_color: str) -> tuple:
        """Convert hex color to RGB tuple (0.0-1.0) for PyBullet/OpenGL."""
        r, g, b = cls.rgb(hex_color)
        return (r / 255.0, g / 255.0, b / 255.0)
