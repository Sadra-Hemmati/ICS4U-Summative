"""
JointDialog - Dialog for defining or editing a joint between two links.
"""

from typing import TYPE_CHECKING, Optional, Tuple
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout,
    QDialogButtonBox, QLineEdit, QComboBox, QDoubleSpinBox,
    QCheckBox, QLabel, QGroupBox, QMessageBox, QPushButton
)
from PyQt5.QtCore import Qt, pyqtSignal

if TYPE_CHECKING:
    from ...cad_editor import CADEditor, JointDefinition


class JointDialog(QDialog):
    """Dialog for defining or editing a joint between two links."""

    # Signal emitted to highlight links during preview
    previewRequested = pyqtSignal(list)

    def __init__(self, editor: 'CADEditor', parent=None,
                 editing_joint: 'Optional[JointDefinition]' = None):
        super().__init__(parent)
        self.editor = editor
        self.result_data = None
        self.editing_joint = editing_joint
        self._original_name = editing_joint.name if editing_joint else None

        if editing_joint:
            self.setWindowTitle(f"Edit Joint: {editing_joint.name}")
        else:
            self.setWindowTitle("Define Joint")

        self.setMinimumWidth(450)
        self.setModal(True)

        self._setup_ui()

        # Pre-fill values if editing
        if editing_joint:
            self._load_editing_values()

    def _setup_ui(self):
        """Set up the dialog UI."""
        layout = QVBoxLayout(self)

        # Basic info group
        info_group = QGroupBox("Joint Information")
        info_layout = QFormLayout(info_group)

        # Name
        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("e.g., shoulder_joint, elbow_joint")
        info_layout.addRow("Joint Name:", self.name_edit)

        # Joint type
        self.type_combo = QComboBox()
        self.type_combo.addItem("Revolute (rotation)", "revolute")
        self.type_combo.addItem("Prismatic (linear)", "prismatic")
        self.type_combo.addItem("Fixed (rigid)", "fixed")
        self.type_combo.currentIndexChanged.connect(self._on_type_changed)
        info_layout.addRow("Joint Type:", self.type_combo)

        layout.addWidget(info_group)

        # Links group
        links_group = QGroupBox("Connected Links")
        links_layout = QFormLayout(links_group)

        link_names = list(self.editor.subsystem.links.keys())

        # Parent link
        self.parent_combo = QComboBox()
        self.parent_combo.addItems(link_names)
        self.parent_combo.currentTextChanged.connect(self._on_link_changed)
        links_layout.addRow("Parent Link:", self.parent_combo)

        # Child link
        self.child_combo = QComboBox()
        self.child_combo.addItems(link_names)
        if len(link_names) > 1:
            self.child_combo.setCurrentIndex(1)  # Default to second link
        self.child_combo.currentTextChanged.connect(self._on_link_changed)
        links_layout.addRow("Child Link:", self.child_combo)

        layout.addWidget(links_group)

        # Axis group
        self.axis_group = QGroupBox("Rotation/Translation Axis")
        axis_layout = QVBoxLayout(self.axis_group)

        # Preset axis buttons
        presets_layout = QHBoxLayout()
        presets_layout.addWidget(QLabel("Presets:"))

        for name, values in [("X", (1, 0, 0)), ("Y", (0, 1, 0)), ("Z", (0, 0, 1))]:
            btn = QPushButton(name)
            btn.setMaximumWidth(40)
            btn.clicked.connect(lambda checked, v=values: self._set_axis(*v))
            presets_layout.addWidget(btn)

        presets_layout.addStretch()
        axis_layout.addLayout(presets_layout)

        # Custom axis input
        custom_layout = QHBoxLayout()

        self.axis_x = QDoubleSpinBox()
        self.axis_y = QDoubleSpinBox()
        self.axis_z = QDoubleSpinBox()

        for label, spin in [("X:", self.axis_x), ("Y:", self.axis_y), ("Z:", self.axis_z)]:
            spin.setRange(-1.0, 1.0)
            spin.setDecimals(3)
            spin.setSingleStep(0.1)
            custom_layout.addWidget(QLabel(label))
            custom_layout.addWidget(spin)

        self.axis_z.setValue(1.0)  # Default Z-axis
        axis_layout.addLayout(custom_layout)

        layout.addWidget(self.axis_group)

        # Limits group
        self.limits_group = QGroupBox("Position Limits")
        limits_layout = QFormLayout(self.limits_group)

        self.limits_enabled = QCheckBox("Enable position limits")
        self.limits_enabled.setChecked(True)
        self.limits_enabled.toggled.connect(self._on_limits_toggled)
        limits_layout.addRow(self.limits_enabled)

        limits_values_layout = QHBoxLayout()

        self.limit_lower = QDoubleSpinBox()
        self.limit_lower.setRange(-100.0, 100.0)
        self.limit_lower.setDecimals(3)
        self.limit_lower.setValue(-3.14159)
        self.limit_lower.setSuffix(" rad")
        limits_values_layout.addWidget(QLabel("Lower:"))
        limits_values_layout.addWidget(self.limit_lower)

        self.limit_upper = QDoubleSpinBox()
        self.limit_upper.setRange(-100.0, 100.0)
        self.limit_upper.setDecimals(3)
        self.limit_upper.setValue(3.14159)
        self.limit_upper.setSuffix(" rad")
        limits_values_layout.addWidget(QLabel("Upper:"))
        limits_values_layout.addWidget(self.limit_upper)

        limits_layout.addRow("", limits_values_layout)

        # Hint label
        self.limits_hint = QLabel("For revolute: radians. For prismatic: meters.")
        self.limits_hint.setStyleSheet("color: #666; font-size: 11px;")
        limits_layout.addRow("", self.limits_hint)

        layout.addWidget(self.limits_group)

        # Origin info (auto-calculated)
        origin_label = QLabel("Origin will be calculated automatically from link geometry.")
        origin_label.setStyleSheet("color: #666; font-size: 11px;")
        layout.addWidget(origin_label)

        # Button box
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self._on_accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

        # Focus on name field
        self.name_edit.setFocus()

    def _load_editing_values(self):
        """Load values from the joint being edited."""
        if not self.editing_joint:
            return

        joint = self.editing_joint

        # Name
        self.name_edit.setText(joint.name)

        # Joint type
        type_index = self.type_combo.findData(joint.joint_type)
        if type_index >= 0:
            self.type_combo.setCurrentIndex(type_index)

        # Parent/child links
        parent_index = self.parent_combo.findText(joint.parent_link)
        if parent_index >= 0:
            self.parent_combo.setCurrentIndex(parent_index)

        child_index = self.child_combo.findText(joint.child_link)
        if child_index >= 0:
            self.child_combo.setCurrentIndex(child_index)

        # Axis
        self.axis_x.setValue(joint.axis[0])
        self.axis_y.setValue(joint.axis[1])
        self.axis_z.setValue(joint.axis[2])

        # Limits
        if joint.limits:
            self.limits_enabled.setChecked(True)
            self.limit_lower.setValue(joint.limits[0])
            self.limit_upper.setValue(joint.limits[1])
        else:
            self.limits_enabled.setChecked(False)

    def _on_type_changed(self, index: int):
        """Update UI based on joint type."""
        joint_type = self.type_combo.currentData()

        # Show/hide axis and limits for fixed joints
        is_fixed = joint_type == "fixed"
        self.axis_group.setVisible(not is_fixed)
        self.limits_group.setVisible(not is_fixed)

        # Update limits suffix based on joint type
        if joint_type == "prismatic":
            self.limit_lower.setSuffix(" m")
            self.limit_upper.setSuffix(" m")
            if not self.editing_joint:  # Only reset if not editing
                self.limit_lower.setValue(-1.0)
                self.limit_upper.setValue(1.0)
            self.limits_hint.setText("For prismatic joints: meters.")
        else:
            self.limit_lower.setSuffix(" rad")
            self.limit_upper.setSuffix(" rad")
            if not self.editing_joint:  # Only reset if not editing
                self.limit_lower.setValue(-3.14159)
                self.limit_upper.setValue(3.14159)
            self.limits_hint.setText("For revolute joints: radians. π ≈ 3.14159")

    def _on_link_changed(self, _):
        """Emit preview signal when links change."""
        parent = self.parent_combo.currentText()
        child = self.child_combo.currentText()
        self.previewRequested.emit([parent, child])

    def _on_limits_toggled(self, checked: bool):
        """Enable/disable limit inputs."""
        self.limit_lower.setEnabled(checked)
        self.limit_upper.setEnabled(checked)

    def _set_axis(self, x: float, y: float, z: float):
        """Set axis values from preset."""
        self.axis_x.setValue(x)
        self.axis_y.setValue(y)
        self.axis_z.setValue(z)

    def _normalize_axis(self) -> Tuple[float, float, float]:
        """Normalize the axis vector."""
        x = self.axis_x.value()
        y = self.axis_y.value()
        z = self.axis_z.value()

        length = (x*x + y*y + z*z) ** 0.5
        if length < 1e-10:
            return (0.0, 0.0, 1.0)  # Default to Z if zero

        return (x/length, y/length, z/length)

    def _calculate_origin(self) -> Tuple[float, float, float]:
        """Calculate joint origin from closest points between links."""
        parent_name = self.parent_combo.currentText()
        child_name = self.child_combo.currentText()

        parent_link = self.editor.subsystem.links.get(parent_name)
        child_link = self.editor.subsystem.links.get(child_name)

        if not parent_link or not child_link:
            return (0.0, 0.0, 0.0)

        # Get centers of mass of both links
        parent_com = parent_link.center_of_mass
        child_com = child_link.center_of_mass

        # For now, use midpoint between COMs
        return (
            (parent_com[0] + child_com[0]) / 2,
            (parent_com[1] + child_com[1]) / 2,
            (parent_com[2] + child_com[2]) / 2
        )

    def _on_accept(self):
        """Validate and accept the dialog."""
        name = self.name_edit.text().strip()
        joint_type = self.type_combo.currentData()
        parent = self.parent_combo.currentText()
        child = self.child_combo.currentText()

        # Validation
        if not name:
            QMessageBox.warning(self, "Validation Error", "Joint name is required.")
            self.name_edit.setFocus()
            return

        # Check for name conflicts (allow keeping same name when editing)
        if name in self.editor.subsystem.joints and name != self._original_name:
            QMessageBox.warning(
                self, "Validation Error",
                f"A joint named '{name}' already exists."
            )
            self.name_edit.setFocus()
            return

        if parent == child:
            QMessageBox.warning(
                self, "Validation Error",
                "Parent and child links must be different."
            )
            return

        # Get axis (only for non-fixed joints)
        if joint_type == "fixed":
            axis = (0.0, 0.0, 1.0)
            limits = None
        else:
            axis = self._normalize_axis()

            # Get limits
            if self.limits_enabled.isChecked():
                lower = self.limit_lower.value()
                upper = self.limit_upper.value()
                if lower >= upper:
                    QMessageBox.warning(
                        self, "Validation Error",
                        "Lower limit must be less than upper limit."
                    )
                    return
                limits = (lower, upper)
            else:
                limits = None

        # Collect result data
        self.result_data = {
            'name': name,
            'joint_type': joint_type,
            'parent_link': parent,
            'child_link': child,
            'axis': axis,
            'limits': limits,
            'origin': self._calculate_origin()
        }

        self.accept()
