"""
Qt GUI module for SubsystemSim CAD Editor.

Provides:
- CADMainWindow: Custom main window with side panel
- SidePanel: Tabs for Links, Joints, Motors, Sensors with hover highlighting
- Dialogs: LinkDialog, JointDialog, MotorDialog, SensorDialog
- dark_theme: Dark theme stylesheet matching SimpleSim
"""

from .main_window import CADMainWindow
from .side_panel import SidePanel
from .dark_theme import DARK_STYLESHEET, apply_dark_theme

__all__ = ['CADMainWindow', 'SidePanel', 'DARK_STYLESHEET', 'apply_dark_theme']
