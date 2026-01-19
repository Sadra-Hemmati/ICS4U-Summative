"""
Qt GUI module for SubsystemSim CAD Editor.

Provides:
- CADMainWindow: Custom main window with side panel
- SidePanel: Tabs for Links, Joints, Motors, Sensors with hover highlighting
- Dialogs: LinkDialog, JointDialog, MotorDialog, SensorDialog
"""

from .main_window import CADMainWindow
from .side_panel import SidePanel

__all__ = ['CADMainWindow', 'SidePanel']
