"""
SensorDialog - Dialog for adding or editing a sensor on a joint.
"""

from typing import TYPE_CHECKING, List, Optional
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout,
    QDialogButtonBox, QLineEdit, QComboBox, QSpinBox,
    QLabel, QGroupBox, QMessageBox, QStackedWidget, QWidget
)
from PyQt5.QtCore import Qt

if TYPE_CHECKING:
    from ...cad_editor import CADEditor, SensorDefinition

# Sensor types
SENSOR_TYPES = [
    ("Quadrature Encoder (DIO)", "encoder"),
    ("CANcoder / Absolute Encoder (CAN)", "cancoder"),
    ("Duty Cycle Encoder (DIO)", "duty_cycle"),
]


class SensorDialog(QDialog):
    """Dialog for adding or editing a sensor on a joint."""

    def __init__(self, editor: 'CADEditor', parent=None,
                 editing_sensor: 'Optional[SensorDefinition]' = None):
        super().__init__(parent)
        self.editor = editor
        self.result_data = None
        self.editing_sensor = editing_sensor
        self._original_name = editing_sensor.name if editing_sensor else None

        if editing_sensor:
            self.setWindowTitle(f"Edit Sensor: {editing_sensor.name}")
        else:
            self.setWindowTitle("Add Sensor")

        self.setMinimumWidth(400)
        self.setModal(True)

        self._setup_ui()

        # Pre-fill values if editing
        if editing_sensor:
            self._load_editing_values()

    def _setup_ui(self):
        """Set up the dialog UI."""
        layout = QVBoxLayout(self)

        # Basic info group
        info_group = QGroupBox("Sensor Information")
        info_layout = QFormLayout(info_group)

        # Name
        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("e.g., arm_encoder, wrist_sensor")
        info_layout.addRow("Sensor Name:", self.name_edit)

        # Joint selection
        self.joint_combo = QComboBox()
        joint_names = list(self.editor.subsystem.joints.keys())
        self.joint_combo.addItems(joint_names)
        info_layout.addRow("Measures Joint:", self.joint_combo)

        # Sensor type
        self.type_combo = QComboBox()
        for display_name, value in SENSOR_TYPES:
            self.type_combo.addItem(display_name, value)
        self.type_combo.currentIndexChanged.connect(self._on_type_changed)
        info_layout.addRow("Sensor Type:", self.type_combo)

        layout.addWidget(info_group)

        # Connection group - changes based on sensor type
        self.connection_group = QGroupBox("Connection")
        self.connection_layout = QVBoxLayout(self.connection_group)

        # Stacked widget for different connection types
        self.connection_stack = QStackedWidget()

        # Page 0: Quadrature encoder (2 DIO ports)
        quad_page = QWidget()
        quad_layout = QFormLayout(quad_page)

        self.dio_port_a = QSpinBox()
        self.dio_port_a.setRange(0, 9)
        self.dio_port_a.setValue(0)
        quad_layout.addRow("DIO Port A (Channel A):", self.dio_port_a)

        self.dio_port_b = QSpinBox()
        self.dio_port_b.setRange(0, 9)
        self.dio_port_b.setValue(1)
        quad_layout.addRow("DIO Port B (Channel B):", self.dio_port_b)

        self.connection_stack.addWidget(quad_page)

        # Page 1: CANcoder (CAN ID)
        can_page = QWidget()
        can_layout = QFormLayout(can_page)

        self.can_id_spin = QSpinBox()
        self.can_id_spin.setRange(1, 62)
        self.can_id_spin.setValue(1)
        can_layout.addRow("CAN ID:", self.can_id_spin)

        self.connection_stack.addWidget(can_page)

        # Page 2: Duty cycle encoder (1 DIO port)
        duty_page = QWidget()
        duty_layout = QFormLayout(duty_page)

        self.dio_port_single = QSpinBox()
        self.dio_port_single.setRange(0, 9)
        self.dio_port_single.setValue(0)
        duty_layout.addRow("DIO Port:", self.dio_port_single)

        self.connection_stack.addWidget(duty_page)

        self.connection_layout.addWidget(self.connection_stack)
        layout.addWidget(self.connection_group)

        # Resolution group
        res_group = QGroupBox("Resolution")
        res_layout = QFormLayout(res_group)

        res_input_layout = QHBoxLayout()
        self.resolution_spin = QSpinBox()
        self.resolution_spin.setRange(1, 65536)
        self.resolution_spin.setValue(2048)
        res_input_layout.addWidget(self.resolution_spin)
        res_input_layout.addWidget(QLabel("ticks per revolution"))
        res_layout.addRow("Encoder Resolution:", res_input_layout)

        self.resolution_hint = QLabel("Standard quadrature: 2048. CANcoder: 4096.")
        self.resolution_hint.setStyleSheet("color: #B0B0B0; font-size: 11px;")
        res_layout.addRow("", self.resolution_hint)

        layout.addWidget(res_group)

        # Button box
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self._on_accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

        # Focus on name field
        self.name_edit.setFocus()

        # Initialize to first sensor type (only if not editing)
        if not self.editing_sensor:
            self._on_type_changed(0)

    def _load_editing_values(self):
        """Load values from the sensor being edited."""
        if not self.editing_sensor:
            return

        sensor = self.editing_sensor

        # Name
        self.name_edit.setText(sensor.name)

        # Joint
        joint_index = self.joint_combo.findText(sensor.joint_name)
        if joint_index >= 0:
            self.joint_combo.setCurrentIndex(joint_index)

        # Sensor type
        type_index = self.type_combo.findData(sensor.sensor_type)
        if type_index >= 0:
            self.type_combo.setCurrentIndex(type_index)
            # Update the stack page
            self._on_type_changed(type_index)

        # Connection-specific values
        if sensor.sensor_type == "encoder":
            if len(sensor.hal_ports) >= 2:
                self.dio_port_a.setValue(sensor.hal_ports[0])
                self.dio_port_b.setValue(sensor.hal_ports[1])
        elif sensor.sensor_type == "cancoder":
            if sensor.can_id is not None:
                self.can_id_spin.setValue(sensor.can_id)
        elif sensor.sensor_type == "duty_cycle":
            if len(sensor.hal_ports) >= 1:
                self.dio_port_single.setValue(sensor.hal_ports[0])

        # Resolution
        self.resolution_spin.setValue(sensor.ticks_per_revolution)

    def _on_type_changed(self, index: int):
        """Update connection UI and resolution based on sensor type."""
        sensor_type = self.type_combo.currentData()

        # Update connection stack
        if sensor_type == "encoder":
            self.connection_stack.setCurrentIndex(0)
            if not self.editing_sensor:
                self.resolution_spin.setValue(2048)
            self.resolution_hint.setText("Standard quadrature encoder: 2048 ticks/rev")
        elif sensor_type == "cancoder":
            self.connection_stack.setCurrentIndex(1)
            if not self.editing_sensor:
                self.resolution_spin.setValue(4096)
            self.resolution_hint.setText("CTRE CANcoder: 4096 ticks/rev")
        elif sensor_type == "duty_cycle":
            self.connection_stack.setCurrentIndex(2)
            if not self.editing_sensor:
                self.resolution_spin.setValue(1)
            self.resolution_hint.setText("Duty cycle reports absolute position (0-1)")

    def _on_accept(self):
        """Validate and accept the dialog."""
        name = self.name_edit.text().strip()
        joint = self.joint_combo.currentText()
        sensor_type = self.type_combo.currentData()

        # Validation
        if not name:
            QMessageBox.warning(self, "Validation Error", "Sensor name is required.")
            self.name_edit.setFocus()
            return

        # Check for name conflicts (allow keeping same name when editing)
        if name in self.editor.subsystem.sensors and name != self._original_name:
            QMessageBox.warning(
                self, "Validation Error",
                f"A sensor named '{name}' already exists."
            )
            self.name_edit.setFocus()
            return

        if not joint:
            QMessageBox.warning(self, "Validation Error", "Please select a joint.")
            return

        # Collect connection-specific data
        hal_ports: List[int] = []
        can_id: Optional[int] = None
        controller_type = "dio"

        if sensor_type == "encoder":
            port_a = self.dio_port_a.value()
            port_b = self.dio_port_b.value()
            if port_a == port_b:
                QMessageBox.warning(
                    self, "Validation Error",
                    "DIO ports A and B must be different."
                )
                return
            hal_ports = [port_a, port_b]
            controller_type = "dio"

        elif sensor_type == "cancoder":
            can_id = self.can_id_spin.value()
            controller_type = "can"

        elif sensor_type == "duty_cycle":
            hal_ports = [self.dio_port_single.value()]
            controller_type = "dio"

        # Collect result data
        self.result_data = {
            'name': name,
            'sensor_type': sensor_type,
            'joint_name': joint,
            'controller_type': controller_type,
            'hal_ports': hal_ports,
            'can_id': can_id,
            'ticks_per_revolution': self.resolution_spin.value()
        }

        self.accept()
