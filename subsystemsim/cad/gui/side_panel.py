"""
SidePanel - Side panel with tabs for Links, Joints, Motors, Sensors.
Provides hover-to-highlight functionality for 3D parts.
"""

from typing import TYPE_CHECKING, List, Dict, Tuple, Optional
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTabWidget,
    QPushButton, QLabel, QGroupBox, QMessageBox
)
from PyQt5.QtCore import pyqtSignal

from .widgets.definition_list import DefinitionListWidget

if TYPE_CHECKING:
    from ..cad_editor import CADEditor

# Highlight colors (RGB 0-1)
HIGHLIGHT_COLOR = (0.2, 0.8, 1.0)          # Cyan - general hover
PARENT_HIGHLIGHT_COLOR = (0.4, 1.0, 0.4)   # Green - parent links
CHILD_HIGHLIGHT_COLOR = (1.0, 0.6, 0.2)    # Orange - child links


class SidePanel(QWidget):
    """
    Side panel with tabs for managing subsystem definitions.
    Hovering over items highlights corresponding 3D parts.
    """

    # Signals for requesting dialogs (create new)
    requestDefineLink = pyqtSignal()
    requestDefineJoint = pyqtSignal()
    requestAddMotor = pyqtSignal()
    requestAddSensor = pyqtSignal()

    # Signals for editing existing definitions
    requestEditLink = pyqtSignal(str)    # link_name
    requestEditJoint = pyqtSignal(str)   # joint_name
    requestEditMotor = pyqtSignal(str)   # motor_name
    requestEditSensor = pyqtSignal(str)  # sensor_name

    def __init__(self, editor: 'CADEditor', parent=None):
        super().__init__(parent)
        self.editor = editor
        self._highlighted_parts: List[str] = []
        self._original_colors: Dict[str, Tuple[float, float, float]] = {}

        self._setup_ui()
        self._connect_signals()

    def _setup_ui(self):
        """Set up the side panel UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(8)

        # Title
        title = QLabel("Subsystem Definitions")
        title.setStyleSheet("font-size: 14px; font-weight: bold; padding: 4px;")
        layout.addWidget(title)

        # Tab widget
        self.tabs = QTabWidget()
        self.tabs.setDocumentMode(True)

        # Links tab
        links_widget = QWidget()
        links_layout = QVBoxLayout(links_widget)
        links_layout.setContentsMargins(4, 4, 4, 4)

        self.links_list = DefinitionListWidget()
        links_layout.addWidget(self.links_list)

        self.define_link_btn = QPushButton("Define Link from Selection")
        self.define_link_btn.setToolTip("Group selected parts into a rigid link")
        links_layout.addWidget(self.define_link_btn)

        self.tabs.addTab(links_widget, "Links")

        # Joints tab
        joints_widget = QWidget()
        joints_layout = QVBoxLayout(joints_widget)
        joints_layout.setContentsMargins(4, 4, 4, 4)

        self.joints_list = DefinitionListWidget()
        joints_layout.addWidget(self.joints_list)

        self.define_joint_btn = QPushButton("Define Joint")
        self.define_joint_btn.setToolTip("Create a joint between two links")
        joints_layout.addWidget(self.define_joint_btn)

        self.tabs.addTab(joints_widget, "Joints")

        # Motors tab
        motors_widget = QWidget()
        motors_layout = QVBoxLayout(motors_widget)
        motors_layout.setContentsMargins(4, 4, 4, 4)

        self.motors_list = DefinitionListWidget()
        motors_layout.addWidget(self.motors_list)

        self.add_motor_btn = QPushButton("Add Motor")
        self.add_motor_btn.setToolTip("Attach a motor to a joint")
        motors_layout.addWidget(self.add_motor_btn)

        self.tabs.addTab(motors_widget, "Motors")

        # Sensors tab
        sensors_widget = QWidget()
        sensors_layout = QVBoxLayout(sensors_widget)
        sensors_layout.setContentsMargins(4, 4, 4, 4)

        self.sensors_list = DefinitionListWidget()
        sensors_layout.addWidget(self.sensors_list)

        self.add_sensor_btn = QPushButton("Add Sensor")
        self.add_sensor_btn.setToolTip("Add a sensor to a joint")
        sensors_layout.addWidget(self.add_sensor_btn)

        self.tabs.addTab(sensors_widget, "Sensors")

        layout.addWidget(self.tabs, 1)  # Take remaining space

        # Selection info at bottom
        self.selection_label = QLabel("Selection: None")
        self.selection_label.setStyleSheet("color: #666; padding: 4px;")
        layout.addWidget(self.selection_label)

        # Set minimum width
        self.setMinimumWidth(250)

    def _connect_signals(self):
        """Connect signals for hover highlighting, buttons, and edit requests."""
        # Hover signals for highlighting
        self.links_list.itemHovered.connect(self._highlight_link)
        self.links_list.hoverCleared.connect(self._clear_highlight)

        self.joints_list.itemHovered.connect(self._highlight_joint)
        self.joints_list.hoverCleared.connect(self._clear_highlight)

        self.motors_list.itemHovered.connect(self._highlight_motor)
        self.motors_list.hoverCleared.connect(self._clear_highlight)

        self.sensors_list.itemHovered.connect(self._highlight_sensor)
        self.sensors_list.hoverCleared.connect(self._clear_highlight)

        # Button signals (create new)
        self.define_link_btn.clicked.connect(self.requestDefineLink.emit)
        self.define_joint_btn.clicked.connect(self.requestDefineJoint.emit)
        self.add_motor_btn.clicked.connect(self.requestAddMotor.emit)
        self.add_sensor_btn.clicked.connect(self.requestAddSensor.emit)

        # Double-click signals (edit existing)
        self.links_list.itemEditRequested.connect(self.requestEditLink.emit)
        self.joints_list.itemEditRequested.connect(self.requestEditJoint.emit)
        self.motors_list.itemEditRequested.connect(self.requestEditMotor.emit)
        self.sensors_list.itemEditRequested.connect(self.requestEditSensor.emit)

    def refresh(self):
        """Refresh all lists from editor data."""
        self._refresh_links_list()
        self._refresh_joints_list()
        self._refresh_motors_list()
        self._refresh_sensors_list()

    def _refresh_links_list(self):
        """Refresh the links list from editor data."""
        self.links_list.clear()
        for name, link in self.editor.subsystem.links.items():
            parts_count = len(link.part_names)
            display = f"{name} ({parts_count} parts)"
            self.links_list.addDefinition(name, display)

    def _refresh_joints_list(self):
        """Refresh the joints list from editor data."""
        self.joints_list.clear()
        for name, joint in self.editor.subsystem.joints.items():
            display = f"{name} [{joint.joint_type}]"
            self.joints_list.addDefinition(name, display)

    def _refresh_motors_list(self):
        """Refresh the motors list from editor data."""
        self.motors_list.clear()
        for name, motor in self.editor.subsystem.motors.items():
            display = f"{name} ({motor.motor_type})"
            self.motors_list.addDefinition(name, display)

    def _refresh_sensors_list(self):
        """Refresh the sensors list from editor data."""
        self.sensors_list.clear()
        for name, sensor in self.editor.subsystem.sensors.items():
            display = f"{name} ({sensor.sensor_type})"
            self.sensors_list.addDefinition(name, display)

    def update_selection_label(self, selected_parts: List[str]):
        """Update the selection info label."""
        if not selected_parts:
            self.selection_label.setText("Selection: None")
        elif len(selected_parts) == 1:
            self.selection_label.setText(f"Selection: {selected_parts[0]}")
        else:
            self.selection_label.setText(f"Selection: {len(selected_parts)} parts")

    # -------------------------------------------------------------------------
    # Hover-to-Highlight Methods
    # -------------------------------------------------------------------------

    def _highlight_link(self, link_name: str):
        """Highlight all parts belonging to a link."""
        self._clear_highlight()

        if link_name not in self.editor.subsystem.links:
            return

        link = self.editor.subsystem.links[link_name]
        self._highlight_parts(link.part_names, HIGHLIGHT_COLOR)

    def _highlight_joint(self, joint_name: str):
        """Highlight parent and child links of a joint."""
        self._clear_highlight()

        if joint_name not in self.editor.subsystem.joints:
            return

        joint = self.editor.subsystem.joints[joint_name]

        # Highlight parent link parts in green
        if joint.parent_link in self.editor.subsystem.links:
            parent_parts = self.editor.subsystem.links[joint.parent_link].part_names
            self._highlight_parts(parent_parts, PARENT_HIGHLIGHT_COLOR)

        # Highlight child link parts in orange
        if joint.child_link in self.editor.subsystem.links:
            child_parts = self.editor.subsystem.links[joint.child_link].part_names
            self._highlight_parts(child_parts, CHILD_HIGHLIGHT_COLOR)

    def _highlight_motor(self, motor_name: str):
        """Highlight the joint driven by a motor."""
        if motor_name not in self.editor.subsystem.motors:
            return

        motor = self.editor.subsystem.motors[motor_name]
        self._highlight_joint(motor.joint_name)

    def _highlight_sensor(self, sensor_name: str):
        """Highlight the joint measured by a sensor."""
        if sensor_name not in self.editor.subsystem.sensors:
            return

        sensor = self.editor.subsystem.sensors[sensor_name]
        self._highlight_joint(sensor.joint_name)

    def _highlight_parts(self, part_names: List[str], color: Tuple[float, float, float]):
        """Highlight specific parts with given color."""
        if not hasattr(self.editor, 'display') or self.editor.display is None:
            return

        try:
            from OCC.Core.Quantity import Quantity_Color, Quantity_TOC_RGB
            context = self.editor.display.Context

            for part_name in part_names:
                if part_name not in self.editor.subsystem.parts:
                    continue

                part = self.editor.subsystem.parts[part_name]

                # Store original color for restoration
                if part_name not in self._original_colors:
                    self._original_colors[part_name] = part.color

                # Apply highlight color
                if part.ais_shape:
                    context.SetColor(
                        part.ais_shape,
                        Quantity_Color(color[0], color[1], color[2], Quantity_TOC_RGB),
                        True
                    )

                self._highlighted_parts.append(part_name)

            context.UpdateCurrentViewer()

        except Exception as e:
            print(f"[WARN] Highlight error: {e}")

    def _clear_highlight(self):
        """Restore original colors to all highlighted parts."""
        if not self._highlighted_parts:
            return

        if not hasattr(self.editor, 'display') or self.editor.display is None:
            self._highlighted_parts.clear()
            self._original_colors.clear()
            return

        try:
            from OCC.Core.Quantity import Quantity_Color, Quantity_TOC_RGB
            context = self.editor.display.Context

            for part_name in self._highlighted_parts:
                if part_name not in self.editor.subsystem.parts:
                    continue

                part = self.editor.subsystem.parts[part_name]

                # Restore original color (or selected color if selected)
                if part.is_selected:
                    # Keep selection color
                    from ..cad_editor import SELECTION_COLOR
                    restore_color = SELECTION_COLOR
                else:
                    restore_color = self._original_colors.get(part_name, part.color)

                if part.ais_shape:
                    context.SetColor(
                        part.ais_shape,
                        Quantity_Color(restore_color[0], restore_color[1], restore_color[2], Quantity_TOC_RGB),
                        True
                    )

            self._highlighted_parts.clear()
            self._original_colors.clear()
            context.UpdateCurrentViewer()

        except Exception as e:
            print(f"[WARN] Clear highlight error: {e}")
            self._highlighted_parts.clear()
            self._original_colors.clear()
