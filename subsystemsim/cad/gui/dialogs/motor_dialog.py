"""
MotorDialog - Dialog for adding or editing a motor on a joint.
"""

from typing import TYPE_CHECKING, Optional
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout,
    QDialogButtonBox, QLineEdit, QComboBox, QDoubleSpinBox,
    QSpinBox, QCheckBox, QLabel, QGroupBox, QMessageBox
)
from PyQt5.QtCore import Qt

if TYPE_CHECKING:
    from ...cad_editor import CADEditor, MotorDefinition

# Motor types with display names and internal values
MOTOR_TYPES = [
    ("WCP Kraken X60 (Brushless)", "krakenx60"),
    ("REV NEO (Brushless)", "neo"),
    ("REV NEO 550 (Brushless)", "neo550"),
    ("REV NEO Vortex (Brushless)", "neovortex"),
    ("VEX Falcon 500 (Brushless)", "falcon500"),
    ("CIM (Brushed)", "cim"),
    ("Mini CIM (Brushed)", "minicim"),
    ("BAG (Brushed)", "bag"),
    ("VEX Venom", "venom"),
]


class MotorDialog(QDialog):
    """Dialog for adding or editing a motor on a joint."""

    def __init__(self, editor: 'CADEditor', parent=None,
                 editing_motor: 'Optional[MotorDefinition]' = None):
        super().__init__(parent)
        self.editor = editor
        self.result_data = None
        self.editing_motor = editing_motor
        self._original_name = editing_motor.name if editing_motor else None

        if editing_motor:
            self.setWindowTitle(f"Edit Motor: {editing_motor.name}")
        else:
            self.setWindowTitle("Add Motor")

        self.setMinimumWidth(400)
        self.setModal(True)

        self._setup_ui()

        # Pre-fill values if editing
        if editing_motor:
            self._load_editing_values()

    def _setup_ui(self):
        """Set up the dialog UI."""
        layout = QVBoxLayout(self)

        # Basic info group
        info_group = QGroupBox("Motor Information")
        info_layout = QFormLayout(info_group)

        # Name
        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("e.g., arm_motor, wrist_motor")
        info_layout.addRow("Motor Name:", self.name_edit)

        # Joint selection
        self.joint_combo = QComboBox()
        joint_names = list(self.editor.subsystem.joints.keys())
        self.joint_combo.addItems(joint_names)
        info_layout.addRow("Drives Joint:", self.joint_combo)

        # Motor type
        self.type_combo = QComboBox()
        for display_name, value in MOTOR_TYPES:
            self.type_combo.addItem(display_name, value)
        info_layout.addRow("Motor Type:", self.type_combo)

        layout.addWidget(info_group)

        # Mechanical group
        mech_group = QGroupBox("Mechanical Properties")
        mech_layout = QFormLayout(mech_group)

        # Gear ratio
        gear_layout = QHBoxLayout()
        self.gear_ratio_spin = QDoubleSpinBox()
        self.gear_ratio_spin.setRange(0.1, 500.0)
        self.gear_ratio_spin.setDecimals(2)
        self.gear_ratio_spin.setValue(1.0)
        gear_layout.addWidget(self.gear_ratio_spin)
        gear_layout.addWidget(QLabel(": 1 reduction"))
        mech_layout.addRow("Gear Ratio:", gear_layout)

        gear_hint = QLabel("e.g., 60 for 60:1 gearbox (motor turns 60x for 1 output turn)")
        gear_hint.setStyleSheet("color: #666; font-size: 11px;")
        mech_layout.addRow("", gear_hint)

        # Inverted
        self.inverted_check = QCheckBox("Motor direction inverted")
        self.inverted_check.setToolTip("Check if positive voltage should produce negative motion")
        mech_layout.addRow("", self.inverted_check)

        layout.addWidget(mech_group)

        # Controller group
        ctrl_group = QGroupBox("Motor Controller")
        ctrl_layout = QFormLayout(ctrl_group)

        # Controller type
        self.controller_combo = QComboBox()
        self.controller_combo.addItem("CAN (SparkMax, TalonFX, etc.)", "can")
        self.controller_combo.addItem("PWM (Spark, Talon SR, Victor)", "pwm")
        self.controller_combo.currentIndexChanged.connect(self._on_controller_changed)
        ctrl_layout.addRow("Controller Type:", self.controller_combo)

        # Device ID
        id_layout = QHBoxLayout()
        self.device_id_label = QLabel("CAN ID:")
        id_layout.addWidget(self.device_id_label)

        self.device_id_spin = QSpinBox()
        self.device_id_spin.setRange(1, 62)
        self.device_id_spin.setValue(1)
        id_layout.addWidget(self.device_id_spin)
        id_layout.addStretch()

        ctrl_layout.addRow("", id_layout)

        layout.addWidget(ctrl_group)

        # Button box
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self._on_accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

        # Focus on name field
        self.name_edit.setFocus()

    def _load_editing_values(self):
        """Load values from the motor being edited."""
        if not self.editing_motor:
            return

        motor = self.editing_motor

        # Name
        self.name_edit.setText(motor.name)

        # Joint
        joint_index = self.joint_combo.findText(motor.joint_name)
        if joint_index >= 0:
            self.joint_combo.setCurrentIndex(joint_index)

        # Motor type
        type_index = self.type_combo.findData(motor.motor_type)
        if type_index >= 0:
            self.type_combo.setCurrentIndex(type_index)

        # Gear ratio
        self.gear_ratio_spin.setValue(motor.gear_ratio)

        # Inverted
        self.inverted_check.setChecked(motor.inverted)

        # Controller type
        ctrl_index = self.controller_combo.findData(motor.controller_type)
        if ctrl_index >= 0:
            self.controller_combo.setCurrentIndex(ctrl_index)

        # Device ID
        self.device_id_spin.setValue(motor.device_id)

    def _on_controller_changed(self, index: int):
        """Update device ID label and range based on controller type."""
        controller_type = self.controller_combo.currentData()

        if controller_type == "can":
            self.device_id_label.setText("CAN ID:")
            self.device_id_spin.setRange(1, 62)
            if not self.editing_motor:
                self.device_id_spin.setValue(1)
        else:  # pwm
            self.device_id_label.setText("PWM Port:")
            self.device_id_spin.setRange(0, 9)
            if not self.editing_motor:
                self.device_id_spin.setValue(0)

    def _on_accept(self):
        """Validate and accept the dialog."""
        name = self.name_edit.text().strip()
        joint = self.joint_combo.currentText()
        motor_type = self.type_combo.currentData()
        controller_type = self.controller_combo.currentData()

        # Validation
        if not name:
            QMessageBox.warning(self, "Validation Error", "Motor name is required.")
            self.name_edit.setFocus()
            return

        # Check for name conflicts (allow keeping same name when editing)
        if name in self.editor.subsystem.motors and name != self._original_name:
            QMessageBox.warning(
                self, "Validation Error",
                f"A motor named '{name}' already exists."
            )
            self.name_edit.setFocus()
            return

        if not joint:
            QMessageBox.warning(self, "Validation Error", "Please select a joint.")
            return

        # Collect result data
        self.result_data = {
            'name': name,
            'joint_name': joint,
            'motor_type': motor_type,
            'gear_ratio': self.gear_ratio_spin.value(),
            'controller_type': controller_type,
            'device_id': self.device_id_spin.value(),
            'inverted': self.inverted_check.isChecked()
        }

        self.accept()
