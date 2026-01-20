"""
LinkDialog - Dialog for defining or editing a link from selected parts.
"""

from typing import TYPE_CHECKING, List, Optional
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout,
    QDialogButtonBox, QLineEdit, QDoubleSpinBox,
    QCheckBox, QLabel, QGroupBox, QMessageBox, QListWidget,
    QListWidgetItem, QPushButton, QAbstractItemView
)
from PyQt5.QtCore import Qt

if TYPE_CHECKING:
    from ...cad_editor import CADEditor, LinkDefinition

# Default density for mass calculation (aluminum)
DEFAULT_DENSITY = 2700.0  # kg/m³


class LinkDialog(QDialog):
    """Dialog for defining or editing a link from selected parts."""

    def __init__(self, editor: 'CADEditor', selected_parts: List[str], parent=None,
                 editing_link: 'Optional[LinkDefinition]' = None):
        super().__init__(parent)
        self.editor = editor
        self.selected_parts = list(selected_parts)  # Make a mutable copy
        self.result_data = None
        self.editing_link = editing_link
        self._original_name = editing_link.name if editing_link else None

        if editing_link:
            self.setWindowTitle(f"Edit Link: {editing_link.name}")
        else:
            self.setWindowTitle("Define Link")

        self.setMinimumWidth(450)
        self.setMinimumHeight(400)
        self.setModal(True)

        self._setup_ui()

        # Pre-fill values if editing
        if editing_link:
            self._load_editing_values()

    def _setup_ui(self):
        """Set up the dialog UI."""
        layout = QVBoxLayout(self)

        # Parts group with list and add/remove buttons
        parts_group = QGroupBox("Parts in Link")
        parts_layout = QVBoxLayout(parts_group)

        # Parts list (editable in edit mode)
        self.parts_list = QListWidget()
        self.parts_list.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.parts_list.setMaximumHeight(150)
        parts_layout.addWidget(self.parts_list)

        # Count label
        self.count_label = QLabel(f"Total: {len(self.selected_parts)} parts")
        self.count_label.setStyleSheet("color: #B0B0B0;")
        parts_layout.addWidget(self.count_label)

        # Add/Remove buttons
        btn_layout = QHBoxLayout()

        self.add_parts_btn = QPushButton("Add Selected Parts")
        self.add_parts_btn.setToolTip("Add currently selected (orange) parts from the 3D view")
        self.add_parts_btn.clicked.connect(self._on_add_parts)
        btn_layout.addWidget(self.add_parts_btn)

        self.remove_parts_btn = QPushButton("Remove Selected")
        self.remove_parts_btn.setToolTip("Remove selected parts from this link")
        self.remove_parts_btn.clicked.connect(self._on_remove_parts)
        btn_layout.addWidget(self.remove_parts_btn)

        parts_layout.addLayout(btn_layout)

        layout.addWidget(parts_group)

        # Link properties group
        props_group = QGroupBox("Link Properties")
        props_layout = QFormLayout(props_group)

        # Name input
        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("e.g., arm_link, base_link, wrist")
        props_layout.addRow("Link Name:", self.name_edit)

        # Auto-calculated mass
        self.auto_mass = self._calculate_auto_mass()
        auto_mass_text = f"{self.auto_mass:.4f} kg (from volume × {DEFAULT_DENSITY} kg/m³)"
        self.auto_mass_label = QLabel(auto_mass_text)
        self.auto_mass_label.setStyleSheet("color: #B0B0B0;")
        props_layout.addRow("Calculated Mass:", self.auto_mass_label)

        # Mass override
        override_layout = QHBoxLayout()

        self.mass_override_check = QCheckBox("Override mass:")
        self.mass_override_check.toggled.connect(self._on_override_toggled)
        override_layout.addWidget(self.mass_override_check)

        self.mass_spin = QDoubleSpinBox()
        self.mass_spin.setRange(0.001, 1000.0)
        self.mass_spin.setDecimals(4)
        self.mass_spin.setSuffix(" kg")
        self.mass_spin.setValue(self.auto_mass)
        self.mass_spin.setEnabled(False)
        override_layout.addWidget(self.mass_spin)

        props_layout.addRow("", override_layout)

        layout.addWidget(props_group)

        # Center of mass info (read-only, auto-calculated)
        com = self._calculate_center_of_mass()
        self.com_label = QLabel(f"Center of mass: ({com[0]:.3f}, {com[1]:.3f}, {com[2]:.3f}) m")
        self.com_label.setStyleSheet("color: #B0B0B0; font-size: 11px;")
        layout.addWidget(self.com_label)

        # Button box
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self._on_accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

        # Focus on name field
        self.name_edit.setFocus()

        # NOW populate the parts list (after all widgets are created)
        self._populate_parts_list()

    def _populate_parts_list(self):
        """Populate the parts list widget (initial population only)."""
        self.parts_list.clear()
        for part_name in self.selected_parts:
            item = QListWidgetItem(part_name)
            item.setData(Qt.UserRole, part_name)
            self.parts_list.addItem(item)

    def _load_editing_values(self):
        """Load values from the link being edited."""
        if not self.editing_link:
            return

        self.name_edit.setText(self.editing_link.name)

        if self.editing_link.mass_override:
            self.mass_override_check.setChecked(True)
            self.mass_spin.setValue(self.editing_link.mass)

    def _refresh_parts_list(self):
        """Refresh the parts list widget after add/remove."""
        self.parts_list.clear()
        for part_name in self.selected_parts:
            item = QListWidgetItem(part_name)
            item.setData(Qt.UserRole, part_name)
            self.parts_list.addItem(item)
        self.count_label.setText(f"Total: {len(self.selected_parts)} parts")
        self._update_mass_display()
        self._update_com_display()

    def _update_mass_display(self):
        """Update the auto-calculated mass display."""
        self.auto_mass = self._calculate_auto_mass()
        self.auto_mass_label.setText(f"{self.auto_mass:.4f} kg (from volume × {DEFAULT_DENSITY} kg/m³)")
        if not self.mass_override_check.isChecked():
            self.mass_spin.setValue(self.auto_mass)

    def _update_com_display(self):
        """Update the center of mass display."""
        com = self._calculate_center_of_mass()
        self.com_label.setText(f"Center of mass: ({com[0]:.3f}, {com[1]:.3f}, {com[2]:.3f}) m")

    def _on_add_parts(self):
        """Add currently selected parts from the 3D view."""
        # Get parts currently selected in the editor (orange parts)
        editor_selected = self.editor.selected_parts.copy()

        added = 0
        for part_name in editor_selected:
            if part_name not in self.selected_parts:
                self.selected_parts.append(part_name)
                added += 1

        if added > 0:
            self._refresh_parts_list()
            QMessageBox.information(self, "Parts Added", f"Added {added} part(s) to the link.")
        else:
            QMessageBox.information(self, "No New Parts",
                                    "No new parts to add. Select parts in the 3D view first.")

    def _on_remove_parts(self):
        """Remove selected parts from the list."""
        selected_items = self.parts_list.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "No Selection", "Select parts in the list to remove.")
            return

        for item in selected_items:
            part_name = item.data(Qt.UserRole)
            if part_name in self.selected_parts:
                self.selected_parts.remove(part_name)

        self._refresh_parts_list()

    def _on_override_toggled(self, checked: bool):
        """Enable/disable mass spin box based on override checkbox."""
        self.mass_spin.setEnabled(checked)

    def _calculate_auto_mass(self) -> float:
        """Calculate mass from volumes of selected parts."""
        total_volume = 0.0
        for part_name in self.selected_parts:
            if part_name in self.editor.subsystem.parts:
                total_volume += self.editor.subsystem.parts[part_name].volume
        return total_volume * DEFAULT_DENSITY

    def _calculate_center_of_mass(self):
        """Calculate weighted center of mass from part COMs."""
        total_mass = 0.0
        weighted_com = [0.0, 0.0, 0.0]

        for part_name in self.selected_parts:
            if part_name not in self.editor.subsystem.parts:
                continue

            part = self.editor.subsystem.parts[part_name]
            part_mass = part.volume * DEFAULT_DENSITY

            if part_mass > 0:
                total_mass += part_mass
                weighted_com[0] += part.center_of_mass[0] * part_mass
                weighted_com[1] += part.center_of_mass[1] * part_mass
                weighted_com[2] += part.center_of_mass[2] * part_mass

        if total_mass > 0:
            return (
                weighted_com[0] / total_mass,
                weighted_com[1] / total_mass,
                weighted_com[2] / total_mass
            )
        return (0.0, 0.0, 0.0)

    def _on_accept(self):
        """Validate and accept the dialog."""
        name = self.name_edit.text().strip()

        # Validation
        if not name:
            QMessageBox.warning(self, "Validation Error", "Link name is required.")
            self.name_edit.setFocus()
            return

        if not self.selected_parts:
            QMessageBox.warning(self, "Validation Error", "Link must contain at least one part.")
            return

        # Check for name conflicts (allow keeping same name when editing)
        if name in self.editor.subsystem.links and name != self._original_name:
            QMessageBox.warning(
                self, "Validation Error",
                f"A link named '{name}' already exists."
            )
            self.name_edit.setFocus()
            return

        # Check for invalid characters
        if not name.replace("_", "").replace("-", "").isalnum():
            QMessageBox.warning(
                self, "Validation Error",
                "Link name should only contain letters, numbers, underscores, and hyphens."
            )
            self.name_edit.setFocus()
            return

        # Collect result data
        if self.mass_override_check.isChecked():
            mass = self.mass_spin.value()
            mass_override = True
        else:
            mass = self.auto_mass
            mass_override = False

        self.result_data = {
            'name': name,
            'part_names': list(self.selected_parts),
            'mass': mass,
            'mass_override': mass_override,
            'center_of_mass': self._calculate_center_of_mass()
        }

        self.accept()
