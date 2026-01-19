"""
CADMainWindow - Custom QMainWindow wrapping PythonOCC viewer with side panel.
"""

from typing import TYPE_CHECKING, Optional, Callable
from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QSplitter, QApplication,
    QMenuBar, QMenu, QAction, QStatusBar, QMessageBox
)
from PyQt5.QtCore import Qt

from OCC.Display.SimpleGui import init_display

from .side_panel import SidePanel

if TYPE_CHECKING:
    from ..cad_editor import CADEditor


class CADMainWindow(QMainWindow):
    """
    Custom main window that wraps PythonOCC viewer with a side panel.

    The PythonOCC viewer is reparented from init_display() into our splitter layout.
    """

    def __init__(self, editor: 'CADEditor'):
        super().__init__()
        self.editor = editor
        self.display = None
        self._occ_window = None
        self._canvas = None
        self._start_display_func = None

        self._setup_window()

    def _setup_window(self):
        """Set up the main window with viewer and side panel."""
        self.setWindowTitle(f"CAD Editor - {self.editor.subsystem.name}")
        self.resize(1400, 900)

        # Initialize PythonOCC display (this creates its own window)
        print("Initializing PythonOCC display...")
        display, start_display, add_menu, add_function_to_menu = init_display()

        self.display = display
        self._start_display_func = start_display
        self._add_menu_func = add_menu
        self._add_function_to_menu_func = add_function_to_menu

        # Find the PythonOCC window and canvas
        app = QApplication.instance()
        for widget in app.topLevelWidgets():
            if hasattr(widget, 'canva'):
                self._occ_window = widget
                self._canvas = widget.canva
                print(f"Found PythonOCC canvas: {type(self._canvas).__name__}")
                break

        if not self._canvas:
            raise RuntimeError("Could not find PythonOCC canvas widget")

        # Create splitter layout
        splitter = QSplitter(Qt.Horizontal)

        # Reparent canvas to our splitter
        self._canvas.setParent(splitter)
        splitter.addWidget(self._canvas)

        # Create and add side panel
        self.side_panel = SidePanel(editor=self.editor, parent=splitter)
        splitter.addWidget(self.side_panel)

        # Set splitter proportions (75% viewer, 25% panel)
        splitter.setSizes([1050, 350])

        self.setCentralWidget(splitter)

        # Set up our menu bar
        self._setup_menus()

        # Set up status bar
        self.statusBar().showMessage("Ready")

        # Connect side panel signals
        self._connect_side_panel_signals()

        # Hide the original OCC window
        if self._occ_window:
            self._occ_window.hide()

    def _setup_menus(self):
        """Set up the menu bar."""
        menubar = self.menuBar()

        # File menu
        file_menu = menubar.addMenu("File")

        generate_action = QAction("Generate Output", self)
        generate_action.setShortcut("Ctrl+G")
        generate_action.triggered.connect(self._on_generate_output)
        file_menu.addAction(generate_action)

        file_menu.addSeparator()

        exit_action = QAction("Exit", self)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        # Define menu
        define_menu = menubar.addMenu("Define")

        link_action = QAction("Define Link from Selection", self)
        link_action.setShortcut("Ctrl+L")
        link_action.triggered.connect(self._on_define_link)
        define_menu.addAction(link_action)

        joint_action = QAction("Define Joint", self)
        joint_action.setShortcut("Ctrl+J")
        joint_action.triggered.connect(self._on_define_joint)
        define_menu.addAction(joint_action)

        define_menu.addSeparator()

        motor_action = QAction("Add Motor", self)
        motor_action.setShortcut("Ctrl+M")
        motor_action.triggered.connect(self._on_add_motor)
        define_menu.addAction(motor_action)

        sensor_action = QAction("Add Sensor", self)
        sensor_action.setShortcut("Ctrl+S")
        sensor_action.triggered.connect(self._on_add_sensor)
        define_menu.addAction(sensor_action)

        define_menu.addSeparator()

        static_action = QAction("Set Static Parent Link", self)
        static_action.triggered.connect(self._on_set_static_parent)
        define_menu.addAction(static_action)

        # Select menu
        select_menu = menubar.addMenu("Select")

        clear_action = QAction("Clear Selection", self)
        clear_action.setShortcut("Escape")
        clear_action.triggered.connect(self._on_clear_selection)
        select_menu.addAction(clear_action)

        select_all_action = QAction("Select All", self)
        select_all_action.setShortcut("Ctrl+A")
        select_all_action.triggered.connect(self._on_select_all)
        select_menu.addAction(select_all_action)

        # View menu
        view_menu = menubar.addMenu("View")

        fit_action = QAction("Fit All", self)
        fit_action.setShortcut("F")
        fit_action.triggered.connect(self._on_fit_all)
        view_menu.addAction(fit_action)

        iso_action = QAction("Isometric View", self)
        iso_action.setShortcut("I")
        iso_action.triggered.connect(self._on_iso_view)
        view_menu.addAction(iso_action)

        view_menu.addSeparator()

        list_parts_action = QAction("List All Parts", self)
        list_parts_action.triggered.connect(self._on_list_parts)
        view_menu.addAction(list_parts_action)

        highlight_undefined_action = QAction("Highlight Undefined Parts", self)
        highlight_undefined_action.triggered.connect(self._on_highlight_undefined)
        view_menu.addAction(highlight_undefined_action)

        # Debug menu
        debug_menu = menubar.addMenu("Debug")

        diag_action = QAction("Selection Diagnostics", self)
        diag_action.triggered.connect(self._on_diagnostics)
        debug_menu.addAction(diag_action)

    def _connect_side_panel_signals(self):
        """Connect side panel button signals to dialog methods."""
        # Create new definitions
        self.side_panel.requestDefineLink.connect(self._on_define_link)
        self.side_panel.requestDefineJoint.connect(self._on_define_joint)
        self.side_panel.requestAddMotor.connect(self._on_add_motor)
        self.side_panel.requestAddSensor.connect(self._on_add_sensor)

        # Edit existing definitions (double-click)
        self.side_panel.requestEditLink.connect(self._on_edit_link)
        self.side_panel.requestEditJoint.connect(self._on_edit_joint)
        self.side_panel.requestEditMotor.connect(self._on_edit_motor)
        self.side_panel.requestEditSensor.connect(self._on_edit_sensor)

    # -------------------------------------------------------------------------
    # Menu Action Handlers
    # -------------------------------------------------------------------------

    def _on_generate_output(self):
        """Handle Generate Output menu action."""
        self.editor.generate_output()

    def _on_define_link(self):
        """Handle Define Link action."""
        from .dialogs import LinkDialog

        if not self.editor.selected_parts:
            QMessageBox.warning(
                self, "No Selection",
                "Please select one or more parts first."
            )
            return

        dialog = LinkDialog(self.editor, self.editor.selected_parts.copy(), self)
        if dialog.exec_():
            data = dialog.result_data
            if data:
                self.editor._create_link_from_dialog(data)
                self.side_panel.refresh()
                self.statusBar().showMessage(f"Created link: {data['name']}")

    def _on_define_joint(self):
        """Handle Define Joint action."""
        from .dialogs import JointDialog

        if len(self.editor.subsystem.links) < 2:
            QMessageBox.warning(
                self, "Not Enough Links",
                "Please define at least 2 links before creating a joint."
            )
            return

        dialog = JointDialog(self.editor, self)
        if dialog.exec_():
            data = dialog.result_data
            if data:
                self.editor._create_joint_from_dialog(data)
                self.side_panel.refresh()
                self.statusBar().showMessage(f"Created joint: {data['name']}")

    def _on_add_motor(self):
        """Handle Add Motor action."""
        from .dialogs import MotorDialog

        if not self.editor.subsystem.joints:
            QMessageBox.warning(
                self, "No Joints",
                "Please define at least one joint before adding a motor."
            )
            return

        dialog = MotorDialog(self.editor, self)
        if dialog.exec_():
            data = dialog.result_data
            if data:
                self.editor._create_motor_from_dialog(data)
                self.side_panel.refresh()
                self.statusBar().showMessage(f"Added motor: {data['name']}")

    def _on_add_sensor(self):
        """Handle Add Sensor action."""
        from .dialogs import SensorDialog

        if not self.editor.subsystem.joints:
            QMessageBox.warning(
                self, "No Joints",
                "Please define at least one joint before adding a sensor."
            )
            return

        dialog = SensorDialog(self.editor, self)
        if dialog.exec_():
            data = dialog.result_data
            if data:
                self.editor._create_sensor_from_dialog(data)
                self.side_panel.refresh()
                self.statusBar().showMessage(f"Added sensor: {data['name']}")

    def _on_set_static_parent(self):
        """Handle Set Static Parent Link action."""
        # Use simple dialog for now
        from PyQt5.QtWidgets import QInputDialog

        links = list(self.editor.subsystem.links.keys())
        if not links:
            QMessageBox.warning(self, "No Links", "Please define at least one link first.")
            return

        link, ok = QInputDialog.getItem(
            self, "Set Static Parent",
            "Select the link that should be the static parent (fixed to world):",
            links, 0, False
        )
        if ok and link:
            self.editor.subsystem.static_parent_link = link
            self.statusBar().showMessage(f"Static parent set to: {link}")

    def _on_clear_selection(self):
        """Clear all selected parts."""
        self.editor.clear_selection()
        self.side_panel.update_selection_label([])

    def _on_select_all(self):
        """Select all parts."""
        for part_name in self.editor.subsystem.parts.keys():
            if part_name not in self.editor.selected_parts:
                self.editor._select_part(part_name)
        self.side_panel.update_selection_label(self.editor.selected_parts)

    def _on_fit_all(self):
        """Fit all parts in view."""
        if self.display:
            self.display.FitAll()

    def _on_iso_view(self):
        """Switch to isometric view."""
        if self.display:
            self.display.View_Iso()

    def _on_list_parts(self):
        """List all parts in console."""
        self.editor._menu_list_parts()

    def _on_highlight_undefined(self):
        """Highlight parts not assigned to any link."""
        self.editor._menu_highlight_undefined()

    def _on_diagnostics(self):
        """Run selection diagnostics."""
        self.editor._debug_selection_pipeline()

    # -------------------------------------------------------------------------
    # Edit Definition Handlers (double-click)
    # -------------------------------------------------------------------------

    def _on_edit_link(self, link_name: str):
        """Handle editing an existing link."""
        from .dialogs import LinkDialog

        if link_name not in self.editor.subsystem.links:
            return

        link = self.editor.subsystem.links[link_name]
        dialog = LinkDialog(self.editor, link.part_names.copy(), self, editing_link=link)
        if dialog.exec_():
            data = dialog.result_data
            if data:
                self.editor._update_link_from_dialog(link_name, data)
                self.side_panel.refresh()
                self.statusBar().showMessage(f"Updated link: {data['name']}")

    def _on_edit_joint(self, joint_name: str):
        """Handle editing an existing joint."""
        from .dialogs import JointDialog

        if joint_name not in self.editor.subsystem.joints:
            return

        joint = self.editor.subsystem.joints[joint_name]
        dialog = JointDialog(self.editor, self, editing_joint=joint)
        if dialog.exec_():
            data = dialog.result_data
            if data:
                self.editor._update_joint_from_dialog(joint_name, data)
                self.side_panel.refresh()
                self.statusBar().showMessage(f"Updated joint: {data['name']}")

    def _on_edit_motor(self, motor_name: str):
        """Handle editing an existing motor."""
        from .dialogs import MotorDialog

        if motor_name not in self.editor.subsystem.motors:
            return

        motor = self.editor.subsystem.motors[motor_name]
        dialog = MotorDialog(self.editor, self, editing_motor=motor)
        if dialog.exec_():
            data = dialog.result_data
            if data:
                self.editor._update_motor_from_dialog(motor_name, data)
                self.side_panel.refresh()
                self.statusBar().showMessage(f"Updated motor: {data['name']}")

    def _on_edit_sensor(self, sensor_name: str):
        """Handle editing an existing sensor."""
        from .dialogs import SensorDialog

        if sensor_name not in self.editor.subsystem.sensors:
            return

        sensor = self.editor.subsystem.sensors[sensor_name]
        dialog = SensorDialog(self.editor, self, editing_sensor=sensor)
        if dialog.exec_():
            data = dialog.result_data
            if data:
                self.editor._update_sensor_from_dialog(sensor_name, data)
                self.side_panel.refresh()
                self.statusBar().showMessage(f"Updated sensor: {data['name']}")

    # -------------------------------------------------------------------------
    # Selection Update
    # -------------------------------------------------------------------------

    def update_selection_display(self):
        """Update the side panel selection display."""
        self.side_panel.update_selection_label(self.editor.selected_parts)

    # -------------------------------------------------------------------------
    # Qt Event Overrides
    # -------------------------------------------------------------------------

    def closeEvent(self, event):
        """Handle window close."""
        # Clean up
        if self._occ_window:
            self._occ_window.close()
        event.accept()

    def show_and_start(self):
        """Show window and start the display loop."""
        self.show()

        # The start_display function enters the Qt event loop
        # But since we've reparented the canvas, we use our own window's event loop
        # Just ensure the display is properly initialized
        if self.display:
            self.display.FitAll()
            self.display.Repaint()
