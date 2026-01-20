"""
CAD Editor - Visual STEP file editor for defining subsystem structure.

Allows users to:
1. Load STEP assembly files
2. View all parts in 3D with different colors
3. Right-click to define links, joints, motors, sensors
4. Export to OBJ meshes + config.json + URDF

Uses PythonOCC 7.9+ modern API patterns.
"""

import json
import math
from pathlib import Path
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Any

# PythonOCC imports - using modern 7.9+ API patterns
from OCC.Core.STEPControl import STEPControl_Reader
from OCC.Core.IFSelect import IFSelect_RetDone
from OCC.Core.TopExp import TopExp_Explorer
from OCC.Core.TopAbs import TopAbs_SOLID, TopAbs_COMPOUND
from OCC.Core.TopoDS import TopoDS_Shape, TopoDS_Solid, TopoDS_Compound, topods
from OCC.Core.BRepMesh import BRepMesh_IncrementalMesh
from OCC.Core.StlAPI import StlAPI_Writer
from OCC.Core.gp import gp_Pnt, gp_Vec
from OCC.Core.BRepExtrema import BRepExtrema_DistShapeShape
from OCC.Display.SimpleGui import init_display
from OCC.Core.Quantity import Quantity_Color, Quantity_TOC_RGB
from OCC.Core.AIS import AIS_Shape
from OCC.Core.TopAbs import TopAbs_FACE, TopAbs_SHAPE

# XDE imports for reading colors/materials from STEP
try:
    from OCC.Core.STEPCAFControl import STEPCAFControl_Reader
    from OCC.Core.TDocStd import TDocStd_Document
    from OCC.Core.XCAFDoc import XCAFDoc_DocumentTool
    from OCC.Core.TDF import TDF_LabelSequence
    from OCC.Core.XCAFApp import XCAFApp_Application
    from OCC.Core.TCollection import TCollection_ExtendedString
    HAS_XDE = True
except ImportError:
    HAS_XDE = False
    print("[WARNING] XDE modules not available, color reading disabled")

# Modern API imports - module-level access
from OCC.Core import BRepGProp
from OCC.Core import BRepBndLib
from OCC.Core import GProp
from OCC.Core import Bnd

# PyQt5 imports for GUI
from PyQt5.QtWidgets import QApplication


# Default material density (kg/m^3) - Aluminum 6061
DEFAULT_DENSITY = 2700.0

# Material densities (kg/m^3) for common materials
MATERIAL_DENSITIES = {
    "aluminum": 2700.0,
    "steel": 7850.0,
    "stainless": 8000.0,
    "plastic": 1200.0,
    "abs": 1050.0,
    "pla": 1250.0,
    "nylon": 1150.0,
    "polycarbonate": 1200.0,
    "carbon fiber": 1600.0,
    "titanium": 4500.0,
    "brass": 8500.0,
    "copper": 8960.0,
    "wood": 700.0,
    "default": 2700.0  # Aluminum as default
}

# Muted but DISTINCT color palette for parts (easy to tell apart)
MUTED_COLORS = [
    (0.65, 0.65, 0.75),  # Light steel blue
    (0.75, 0.60, 0.55),  # Terracotta
    (0.55, 0.70, 0.55),  # Sage green
    (0.70, 0.55, 0.70),  # Dusty purple
    (0.75, 0.70, 0.55),  # Sand/tan
    (0.55, 0.65, 0.75),  # Sky blue
    (0.65, 0.75, 0.55),  # Lime green
    (0.75, 0.55, 0.60),  # Rose
    (0.55, 0.70, 0.70),  # Teal
    (0.70, 0.65, 0.75),  # Lavender
    (0.75, 0.75, 0.60),  # Cream/yellow
    (0.60, 0.55, 0.70),  # Violet
]

# Selection highlight color (bright red - SimpleSim accent)
SELECTION_COLOR = (0.9, 0.15, 0.15)

# Assigned to link color (dark red to indicate part is defined)
ASSIGNED_COLOR = (0.5, 0.1, 0.1)

# Undefined/unassigned parts color (warning orange)
UNDEFINED_COLOR = (0.9, 0.5, 0.2)


@dataclass
class PartInfo:
    """Information about a single part from STEP file."""
    name: str
    shape: TopoDS_Shape
    color: Tuple[float, float, float]
    original_color: Optional[Tuple[float, float, float]] = None  # Color from STEP file
    material: Optional[str] = None  # Material name from STEP file
    density: float = DEFAULT_DENSITY  # kg/m^3
    volume: float = 0.0  # m^3
    center_of_mass: Tuple[float, float, float] = (0.0, 0.0, 0.0)
    bounding_box: Tuple[Tuple[float, float, float], Tuple[float, float, float]] = None
    ais_shape: Any = None  # AIS_Shape for display
    is_selected: bool = False  # Selection state


@dataclass
class LinkDefinition:
    """User-defined link (rigid body)."""
    name: str
    part_names: List[str]  # Parts that make up this link
    mass: float = 0.0  # kg (auto-calculated or user override)
    mass_override: bool = False
    center_of_mass: Tuple[float, float, float] = (0.0, 0.0, 0.0)
    inertia: Tuple[float, float, float] = (0.01, 0.01, 0.01)  # Ixx, Iyy, Izz


@dataclass
class JointDefinition:
    """User-defined joint connecting two links."""
    name: str
    joint_type: str  # "revolute", "prismatic", "fixed"
    parent_link: str
    child_link: str
    origin: Tuple[float, float, float] = (0.0, 0.0, 0.0)  # Auto-calculated
    axis: Tuple[float, float, float] = (0.0, 0.0, 1.0)  # User-specified
    limits: Optional[Tuple[float, float]] = None  # min, max (radians or meters)


@dataclass
class MotorDefinition:
    """User-defined motor on a joint."""
    name: str
    joint_name: str
    motor_type: str  # "neo", "cim", "falcon500", etc.
    gear_ratio: float = 1.0
    controller_type: str = "pwm"  # "pwm" or "can"
    device_id: int = 0  # PWM port or CAN ID
    inverted: bool = False


@dataclass
class SensorDefinition:
    """User-defined sensor on a joint."""
    name: str
    sensor_type: str  # "encoder", "cancoder", "limit_switch", etc.
    joint_name: str
    controller_type: str = "dio"  # "dio" or "can"
    hal_ports: List[int] = field(default_factory=list)  # DIO ports for quadrature encoder
    can_id: Optional[int] = None  # CAN ID for CANcoder
    ticks_per_revolution: int = 2048  # For encoders


@dataclass
class SubsystemDefinition:
    """Complete subsystem definition."""
    name: str = "subsystem"
    parts: Dict[str, PartInfo] = field(default_factory=dict)
    links: Dict[str, LinkDefinition] = field(default_factory=dict)
    joints: Dict[str, JointDefinition] = field(default_factory=dict)
    motors: Dict[str, MotorDefinition] = field(default_factory=dict)
    sensors: Dict[str, SensorDefinition] = field(default_factory=dict)
    static_parent_link: Optional[str] = None  # Link that undefined parts attach to


class CADEditor:
    """
    Visual CAD editor for defining FRC subsystem structure from STEP files.
    """

    # Unit conversion factors to meters
    UNIT_SCALES = {
        'meter': 1.0,
        'metre': 1.0,
        'm': 1.0,
        'millimeter': 0.001,
        'millimetre': 0.001,
        'mm': 0.001,
        'centimeter': 0.01,
        'centimetre': 0.01,
        'cm': 0.01,
        'inch': 0.0254,
        'in': 0.0254,
        'foot': 0.3048,
        'ft': 0.3048,
    }

    def __init__(self):
        self.subsystem = SubsystemDefinition()
        self.display = None
        self.start_display = None
        self.selected_parts: List[str] = []
        self._step_file_path: Optional[Path] = None
        self._color_index = 0  # For assigning muted colors
        self._color_map: Dict[Tuple[float, float, float], int] = {}  # Map original colors to palette index
        self._canvas = None  # Qt canvas for mouse events
        self._unit_scale = 0.001  # Default: assume millimeters (most common in CAD)
        self._detected_unit = "millimeter"  # String name of detected unit
        self._output_dir: Optional[str] = None  # Output directory for generated files (set via --output)
        self._main_window = None  # Reference to main window for closing

    def _detect_step_units(self, file_path: str) -> Tuple[str, float]:
        """
        Detect the length unit used in a STEP file by parsing its contents.

        STEP files define units using SI_UNIT entities. Common patterns:
        - SI_UNIT($,.LENGTH_UNIT.) with prefix like MILLI, CENTI
        - CONVERSION_BASED_UNIT for inches, feet

        Args:
            file_path: Path to STEP file

        Returns:
            Tuple of (unit_name, scale_to_meters)
        """
        import re

        try:
            with open(file_path, 'r', errors='ignore') as f:
                content = f.read(50000)  # Read first 50KB (header + start of data)

            # Look for SI_UNIT with prefix (most common)
            # Pattern: SI_UNIT(.MILLI.,.LENGTH_UNIT.) or similar
            si_pattern = r"SI_UNIT\s*\(\s*\.\s*(\w+)\s*\.\s*,\s*\.LENGTH_UNIT\.\s*\)"
            si_match = re.search(si_pattern, content, re.IGNORECASE)

            if si_match:
                prefix = si_match.group(1).upper()
                if prefix == 'MILLI':
                    return ('millimeter', 0.001)
                elif prefix == 'CENTI':
                    return ('centimeter', 0.01)
                elif prefix == 'MICRO':
                    return ('micrometer', 0.000001)
                elif prefix == 'KILO':
                    return ('kilometer', 1000.0)

            # Look for plain SI_UNIT without prefix (meters)
            # Pattern: SI_UNIT($,.LENGTH_UNIT.) where $ means no prefix
            plain_si = r"SI_UNIT\s*\(\s*\$\s*,\s*\.LENGTH_UNIT\.\s*\)"
            if re.search(plain_si, content, re.IGNORECASE):
                return ('meter', 1.0)

            # Look for CONVERSION_BASED_UNIT (inches, feet)
            # Pattern: 'INCH' or 'FOOT' in context of length unit
            if re.search(r"'INCH'", content, re.IGNORECASE):
                return ('inch', 0.0254)
            if re.search(r"'FOOT'", content, re.IGNORECASE):
                return ('foot', 0.3048)

            # Look for length_measure with specific values that hint at units
            # If we find (LENGTH_UNIT()LENGTH_MEASURE(25.4)) it's likely mm
            measure_pattern = r"LENGTH_MEASURE\s*\(\s*([\d.]+)\s*\)"
            measure_match = re.search(measure_pattern, content)
            if measure_match:
                value = float(measure_match.group(1))
                # 25.4 is the conversion factor for inch to mm
                if abs(value - 25.4) < 0.01:
                    return ('millimeter', 0.001)

            # Default: assume millimeters (most common in mechanical CAD)
            print("[INFO] Could not detect STEP units, assuming millimeters")
            return ('millimeter', 0.001)

        except Exception as e:
            print(f"[WARNING] Error detecting STEP units: {e}, assuming millimeters")
            return ('millimeter', 0.001)

    def load_step_file(self, file_path: str) -> bool:
        """
        Load a STEP file and extract all parts with colors.

        Args:
            file_path: Path to STEP file

        Returns:
            True if successful, False otherwise
        """
        self._step_file_path = Path(file_path)

        if not self._step_file_path.exists():
            print(f"[ERROR] File not found: {file_path}")
            return False

        print(f"Loading STEP file: {file_path}")

        # Detect units from STEP file
        self._detected_unit, self._unit_scale = self._detect_step_units(file_path)
        print(f"[INFO] Detected units: {self._detected_unit} (scale to meters: {self._unit_scale})")

        # NOTE: XDE reader disabled - causes silent crashes on some systems
        # Using basic reader with distinct color palette instead
        # To re-enable XDE, set USE_XDE = True below
        USE_XDE = False

        if USE_XDE and HAS_XDE:
            print("[INFO] Attempting XDE reader for color extraction...")
            try:
                success = self._load_step_with_xde(str(self._step_file_path))
                if success:
                    print(f"Extracted {len(self.subsystem.parts)} part(s) with colors")
                    self.subsystem.name = self._step_file_path.stem
                    return True
                print("[INFO] XDE loading failed, falling back to basic reader")
            except Exception as e:
                print(f"[WARNING] XDE error: {e}, using basic reader")

        # Basic reader (assigns distinct colors from palette)
        reader = STEPControl_Reader()
        status = reader.ReadFile(str(self._step_file_path))

        if status != IFSelect_RetDone:
            print(f"[ERROR] Failed to read STEP file (status={status})")
            return False

        reader.TransferRoots()
        num_shapes = reader.NbShapes()
        print(f"Found {num_shapes} shape(s) in STEP file")

        if num_shapes == 0:
            print("[ERROR] No shapes found in STEP file")
            return False

        self.subsystem.parts.clear()

        for i in range(1, num_shapes + 1):
            shape = reader.Shape(i)
            self._extract_parts_from_shape(shape, f"Part_{i}")

        print(f"Extracted {len(self.subsystem.parts)} part(s)")
        self.subsystem.name = self._step_file_path.stem

        return True

    def _load_step_with_xde(self, file_path: str) -> bool:
        """Load STEP file using XDE to get colors and materials.

        XDE (Extended Data Framework) can read color and material info from STEP files.
        This is more complex than the basic reader but preserves appearance data.
        """
        try:
            # Import XDE modules
            from OCC.Core.STEPCAFControl import STEPCAFControl_Reader
            from OCC.Core.XCAFDoc import XCAFDoc_DocumentTool, XCAFDoc_ColorSurf, XCAFDoc_ColorGen
            from OCC.Core.TDF import TDF_LabelSequence
            from OCC.Core.Quantity import Quantity_Color
            from OCC.Core.TCollection import TCollection_ExtendedString
            from OCC.Core.TDocStd import TDocStd_Document
            from OCC.Core.XCAFApp import XCAFApp_Application

            print("  Creating XDE document...")

            # Get or create the XDE application
            app = XCAFApp_Application.GetApplication()

            # Create a new document with a proper handle
            doc_handle = app.NewDocument(TCollection_ExtendedString("MDTV-XCAF"))

            print("  Reading STEP file with XDE reader...")

            # Create and configure the STEP reader
            reader = STEPCAFControl_Reader()
            reader.SetColorMode(True)
            reader.SetNameMode(True)
            reader.SetLayerMode(True)

            # Read the file
            status = reader.ReadFile(file_path)
            if status != IFSelect_RetDone:
                print(f"  XDE ReadFile failed with status {status}")
                return False

            print("  Transferring shapes...")

            # Transfer to document - this can be slow for large files
            if not reader.Transfer(doc_handle):
                print("  XDE Transfer failed")
                return False

            # Get the document from handle
            doc = doc_handle

            # Get tools for accessing shapes and colors
            shape_tool = XCAFDoc_DocumentTool.ShapeTool(doc.Main())
            color_tool = XCAFDoc_DocumentTool.ColorTool(doc.Main())

            # Get all top-level shapes
            labels = TDF_LabelSequence()
            shape_tool.GetFreeShapes(labels)  # GetFreeShapes gets top-level shapes

            if labels.Length() == 0:
                # Try GetShapes as fallback
                shape_tool.GetShapes(labels)

            print(f"  XDE found {labels.Length()} shape labels")

            if labels.Length() == 0:
                return False

            self.subsystem.parts.clear()
            self._color_index = 0

            # Process each shape label
            for i in range(1, labels.Length() + 1):
                label = labels.Value(i)
                shape = shape_tool.GetShape(label)

                if shape.IsNull():
                    continue

                # Try to get name from label
                part_name = f"Part_{i}"
                try:
                    from OCC.Core.TDataStd import TDataStd_Name
                    name_attr = TDataStd_Name()
                    if label.FindAttribute(TDataStd_Name.GetID(), name_attr):
                        name_str = name_attr.Get()
                        if hasattr(name_str, 'ToExtString'):
                            part_name = name_str.ToExtString()
                        elif hasattr(name_str, 'ToCString'):
                            part_name = name_str.ToCString()
                except Exception:
                    pass

                # Try to get color
                original_color = None
                try:
                    color = Quantity_Color()
                    if color_tool.GetColor(label, XCAFDoc_ColorSurf, color):
                        original_color = (color.Red(), color.Green(), color.Blue())
                    elif color_tool.GetColor(label, XCAFDoc_ColorGen, color):
                        original_color = (color.Red(), color.Green(), color.Blue())
                except Exception:
                    pass

                # Extract solids from the shape
                explorer = TopExp_Explorer(shape, TopAbs_SOLID)
                solid_idx = 0
                while explorer.More():
                    solid = topods.Solid(explorer.Current())
                    solid_idx += 1
                    solid_name = f"{part_name}_Solid_{solid_idx}" if solid_idx > 1 else part_name
                    self._add_part(solid_name, solid, original_color=original_color)
                    explorer.Next()

                # If no solids found, add the shape itself
                if solid_idx == 0:
                    self._add_part(part_name, shape, original_color=original_color)

            return len(self.subsystem.parts) > 0

        except ImportError as e:
            print(f"  XDE modules not available: {e}")
            return False
        except Exception as e:
            print(f"  XDE loading error: {e}")
            import traceback
            traceback.print_exc()
            return False

    def _extract_parts_from_shape(self, shape: TopoDS_Shape, base_name: str):
        """
        Extract individual solids from a shape (which may be a compound).
        """
        # Try to explore for solids
        explorer = TopExp_Explorer(shape, TopAbs_SOLID)

        solid_count = 0
        while explorer.More():
            solid = topods.Solid(explorer.Current())
            solid_count += 1

            part_name = f"{base_name}_Solid_{solid_count}"
            self._add_part(part_name, solid)

            explorer.Next()

        # If no solids found, treat the whole shape as one part
        if solid_count == 0:
            self._add_part(base_name, shape)

    def _add_part(self, name: str, shape: TopoDS_Shape,
                  original_color: Optional[Tuple[float, float, float]] = None,
                  material: Optional[str] = None):
        """Add a part to the subsystem with muted color assignment."""
        # Assign muted color based on original color or cycling through palette
        if original_color is not None:
            # Round original color to group similar colors
            color_key = (round(original_color[0], 1),
                        round(original_color[1], 1),
                        round(original_color[2], 1))

            if color_key not in self._color_map:
                self._color_map[color_key] = self._color_index
                self._color_index = (self._color_index + 1) % len(MUTED_COLORS)

            color = MUTED_COLORS[self._color_map[color_key]]
        else:
            # No original color, assign next muted color
            color = MUTED_COLORS[self._color_index % len(MUTED_COLORS)]
            self._color_index += 1

        # Determine density from material
        density = DEFAULT_DENSITY
        if material:
            material_lower = material.lower()
            for mat_name, mat_density in MATERIAL_DENSITIES.items():
                if mat_name in material_lower:
                    density = mat_density
                    break

        # Calculate volume and center of mass using modern API
        props = GProp.GProp_GProps()
        BRepGProp.brepgprop.VolumeProperties(shape, props)

        volume = props.Mass()  # In STEP file units (cubed)
        # Convert to m^3 using detected unit scale
        # Volume scales with the cube of the linear scale
        scale = self._unit_scale
        volume_m3 = volume * (scale ** 3)

        com = props.CentreOfMass()
        # Convert to meters using detected unit scale
        center_of_mass = (com.X() * scale, com.Y() * scale, com.Z() * scale)

        # Calculate bounding box using modern API
        bbox = Bnd.Bnd_Box()
        BRepBndLib.brepbndlib.Add(shape, bbox, True)
        xmin, ymin, zmin, xmax, ymax, zmax = bbox.Get()
        # Convert to meters using detected unit scale
        bounding_box = (
            (xmin * scale, ymin * scale, zmin * scale),
            (xmax * scale, ymax * scale, zmax * scale)
        )

        # Calculate mass from volume and density
        mass = volume_m3 * density

        part = PartInfo(
            name=name,
            shape=shape,
            color=color,
            original_color=original_color,
            material=material,
            density=density,
            volume=volume_m3,
            center_of_mass=center_of_mass,
            bounding_box=bounding_box
        )

        self.subsystem.parts[name] = part

        # Simple output
        print(f"  Added: {name} (mass={mass*1000:.1f}g)")

    def start_viewer(self):
        """Start the 3D viewer with all parts displayed using custom GUI."""
        if not self.subsystem.parts:
            print("[ERROR] No parts loaded. Load a STEP file first.")
            return

        print("Starting 3D viewer with GUI...")
        print(f"Displaying {len(self.subsystem.parts)} parts...")

        # Import GUI components (avoid circular imports)
        try:
            from .gui import CADMainWindow
        except ImportError:
            from subsystemsim.cad.gui import CADMainWindow

        # Ensure QApplication exists
        app = QApplication.instance()
        if not app:
            app = QApplication([])

        # Create the main window (this calls init_display internally)
        self.main_window = CADMainWindow(editor=self)
        self.display = self.main_window.display

        context = self.display.Context

        # Store mapping from AIS_Shape to part name for selection
        self._ais_to_part: Dict[int, str] = {}

        # PERFORMANCE: Pre-mesh all shapes with coarse tessellation
        print("Meshing parts (coarse tessellation for performance)...")
        for part_name, part in self.subsystem.parts.items():
            mesh = BRepMesh_IncrementalMesh(part.shape, 0.5, False, 0.5, True)
            mesh.Perform()

        # Display all parts with their colors
        print("Displaying parts...")
        for part_name, part in self.subsystem.parts.items():
            ais_shape = self.display.DisplayShape(
                part.shape,
                color=Quantity_Color(part.color[0], part.color[1], part.color[2], Quantity_TOC_RGB),
                update=False
            )[0]
            part.ais_shape = ais_shape
            self._ais_to_part[id(ais_shape)] = part_name

        # Force update after batch display
        self.display.FitAll()
        context.UpdateCurrentViewer()

        # Setup selection modes
        print("Setting up selection...")
        try:
            if hasattr(self.display, 'SetSelectionModeFace'):
                self.display.SetSelectionModeFace()
                print("[OK] Selection mode: Face")
            elif hasattr(self.display, 'SetSelectionModeSolid'):
                self.display.SetSelectionModeSolid()
                print("[OK] Selection mode: Solid")
            else:
                from OCC.Core.TopAbs import TopAbs_SOLID
                try:
                    selection_mode = AIS_Shape.SelectionMode(TopAbs_SOLID)
                    context.Activate(selection_mode, True)
                    print(f"[OK] Selection mode: {selection_mode} (manual)")
                except Exception as e:
                    print(f"[WARN] Could not set selection mode: {e}")
        except Exception as e:
            print(f"[WARN] Selection mode setup failed: {e}")

        # Register the selection callback
        self.display.register_select_callback(self._on_shape_selected)
        print("[OK] Selection callback registered")

        # CRITICAL: Monkey-patch the display's Select method to call MoveTo first
        self._patch_display_select()

        # WORKAROUND: Set up our own click detection as fallback
        self._setup_click_selection()

        # Final display update
        self.display.FitAll()
        self.display.View_Iso()
        self.display.Repaint()

        print("\n" + "="*60)
        print("CAD Editor Ready!")
        print("="*60)
        print("")
        print("CONTROLS:")
        print("  CLICK on part  -> Select/deselect (turns ORANGE)")
        print("  LEFT DRAG      -> Rotate view")
        print("  MIDDLE DRAG    -> Pan view")
        print("  SCROLL         -> Zoom")
        print("")
        print("WORKFLOW:")
        print("  1. Click parts to select them (orange = selected)")
        print("  2. Use Define menu or side panel buttons")
        print("  3. Hover over items in side panel to highlight 3D parts")
        print("  4. File -> Generate Output when done")
        print("="*60 + "\n")

        # Show window and start Qt event loop
        self.main_window.show_and_start()
        app.exec_()

    def _patch_display_select(self):
        """Monkey-patch the display's Select method to call MoveTo first."""
        original_select = self.display.Select
        display = self.display

        def patched_select(X, Y):
            # Call MoveTo first to detect what's under the cursor
            display.MoveTo(X, Y)
            # Then call the original Select
            original_select(X, Y)

        self.display.Select = patched_select
        print("[OK] Patched Select() to call MoveTo() first")

    def _setup_click_selection(self):
        """Set up custom click-to-select since MoveTo() detection may be broken."""
        try:
            # Try to import Qt modules directly (PyQt5 or PySide2)
            QtCore = None
            QtWidgets = None
            Qt = None

            try:
                from PyQt5 import QtCore, QtWidgets
                from PyQt5.QtCore import Qt
                qt_backend = "PyQt5"
            except ImportError:
                try:
                    from PySide2 import QtCore, QtWidgets
                    from PySide2.QtCore import Qt
                    qt_backend = "PySide2"
                except ImportError:
                    try:
                        from PyQt6 import QtCore, QtWidgets
                        from PyQt6.QtCore import Qt
                        qt_backend = "PyQt6"
                    except ImportError:
                        try:
                            from PySide6 import QtCore, QtWidgets
                            from PySide6.QtCore import Qt
                            qt_backend = "PySide6"
                        except ImportError:
                            print("[WARN] No Qt backend found (PyQt5/PySide2/PyQt6/PySide6)")
                            return

            print(f"  Qt backend: {qt_backend}")

            # Import QRubberBand for drag selection
            from PyQt5.QtWidgets import QRubberBand
            from PyQt5.QtCore import QRect, QPoint, QSize

            # Define the event filter class here where QtCore is available
            class ClickEventFilter(QtCore.QObject):
                """Qt event filter to handle mouse clicks and drag selection."""
                def __init__(self, editor, parent, qt_backend):
                    super().__init__(parent)
                    self.editor = editor
                    self.qt_backend = qt_backend
                    self._click_start = None
                    self._drag_selecting = False
                    self._rubber_band = None
                    self._debug = False  # Disable verbose debug output

                def eventFilter(self, obj, event):
                    event_type = event.type()

                    # Get Qt constants
                    left_button = Qt.MouseButton.LeftButton if hasattr(Qt, 'MouseButton') else Qt.LeftButton
                    shift_modifier = Qt.KeyboardModifier.ShiftModifier if hasattr(Qt, 'KeyboardModifier') else Qt.ShiftModifier
                    press_type = QtCore.QEvent.Type.MouseButtonPress if hasattr(QtCore.QEvent, 'Type') else 2
                    release_type = QtCore.QEvent.Type.MouseButtonRelease if hasattr(QtCore.QEvent, 'Type') else 3
                    move_type = QtCore.QEvent.Type.MouseMove if hasattr(QtCore.QEvent, 'Type') else 5

                    # Handle mouse press
                    if event_type == press_type:
                        try:
                            if event.button() == left_button:
                                # Get position
                                if hasattr(event, 'position'):
                                    pos = event.position()
                                    x, y = int(pos.x()), int(pos.y())
                                else:
                                    x, y = event.x(), event.y()
                                self._click_start = (x, y)

                                # Check for Shift modifier for drag selection
                                if event.modifiers() & shift_modifier:
                                    self._drag_selecting = True
                                    # Create rubber band
                                    if self._rubber_band is None:
                                        self._rubber_band = QRubberBand(QRubberBand.Rectangle, obj)
                                    self._rubber_band.setGeometry(QRect(QPoint(x, y), QSize()))
                                    self._rubber_band.show()
                                    if self._debug:
                                        print(f"[DEBUG] Drag selection started at ({x}, {y})")
                                    return True  # Consume event to prevent view rotation
                                else:
                                    self._drag_selecting = False
                                    if self._debug:
                                        print(f"[DEBUG] Mouse press at ({x}, {y})")
                        except Exception as e:
                            if self._debug:
                                print(f"[DEBUG] Press event error: {e}")

                    # Handle mouse move for rubber band
                    elif event_type == move_type and self._drag_selecting and self._click_start:
                        try:
                            if hasattr(event, 'position'):
                                pos = event.position()
                                x, y = int(pos.x()), int(pos.y())
                            else:
                                x, y = event.x(), event.y()

                            start_x, start_y = self._click_start
                            # Update rubber band geometry
                            if self._rubber_band:
                                rect = QRect(QPoint(min(start_x, x), min(start_y, y)),
                                           QPoint(max(start_x, x), max(start_y, y)))
                                self._rubber_band.setGeometry(rect)
                            return True  # Consume event
                        except Exception as e:
                            if self._debug:
                                print(f"[DEBUG] Move event error: {e}")

                    # Handle mouse release
                    elif event_type == release_type:
                        try:
                            if event.button() == left_button and self._click_start:
                                # Get position
                                if hasattr(event, 'position'):
                                    pos = event.position()
                                    end_x, end_y = int(pos.x()), int(pos.y())
                                else:
                                    end_x, end_y = event.x(), event.y()

                                start_x, start_y = self._click_start
                                self._click_start = None

                                # Handle drag selection
                                if self._drag_selecting:
                                    self._drag_selecting = False
                                    if self._rubber_band:
                                        self._rubber_band.hide()

                                    # Calculate selection rectangle
                                    min_x = min(start_x, end_x)
                                    max_x = max(start_x, end_x)
                                    min_y = min(start_y, end_y)
                                    max_y = max(start_y, end_y)

                                    # Only select if dragged a meaningful distance
                                    if max_x - min_x > 5 or max_y - min_y > 5:
                                        self.editor._handle_rect_select(min_x, min_y, max_x, max_y)
                                    return True  # Consume event

                                # Regular click selection
                                dx = abs(end_x - start_x)
                                dy = abs(end_y - start_y)
                                if self._debug:
                                    print(f"[DEBUG] Mouse release at ({end_x}, {end_y}), delta=({dx}, {dy})")

                                if dx < 5 and dy < 5:
                                    if self._debug:
                                        print(f"[DEBUG] Triggering click selection at ({end_x}, {end_y})")
                                    self.editor._handle_click_select(end_x, end_y)
                        except Exception as e:
                            if self._debug:
                                print(f"[DEBUG] Release event error: {e}")

                    # Return False to let the event propagate (so view rotation still works)
                    return False

            # Find the canvas widget - the qtViewer3d that handles OpenGL rendering
            app = QtWidgets.QApplication.instance()
            canvas = None
            main_window = None

            if app:
                print("  Searching for Qt canvas widget...")

                # Method 1: Look for the main window with a 'canva' attribute (PythonOCC pattern)
                for widget in app.topLevelWidgets():
                    widget_name = type(widget).__name__
                    print(f"    Top-level widget: {widget_name}")

                    # Check if this is the main window with a canvas
                    if hasattr(widget, 'canva'):
                        main_window = widget
                        canvas = widget.canva
                        print(f"    -> Found canvas via 'canva' attribute: {type(canvas).__name__}")
                        break

                    # Check central widget for QMainWindow
                    if hasattr(widget, 'centralWidget'):
                        central = widget.centralWidget()
                        if central:
                            central_name = type(central).__name__
                            print(f"    -> Central widget: {central_name}")
                            # The central widget should be the viewer
                            if 'viewer' in central_name.lower() or 'qt' in central_name.lower():
                                canvas = central
                                main_window = widget
                                break

                # Method 2: Search all widgets for qtViewer3d or similar
                if canvas is None:
                    for widget in app.allWidgets():
                        widget_name = type(widget).__name__
                        # Look for the OpenGL viewer widget
                        if any(x in widget_name.lower() for x in ['viewer', 'qtviewer', 'glwidget', 'opengl']):
                            canvas = widget
                            print(f"    -> Found via name search: {widget_name}")
                            break

                # Method 3: Find widget that accepts focus and has OpenGL context
                if canvas is None:
                    for widget in app.allWidgets():
                        # Check for widgets that typically handle 3D rendering
                        if hasattr(widget, 'paintEngine') and widget.width() > 100 and widget.height() > 100:
                            widget_name = type(widget).__name__
                            if widget_name not in ['QMenuBar', 'QToolBar', 'QStatusBar', 'QMenu']:
                                canvas = widget
                                print(f"    -> Found via size heuristic: {widget_name} ({widget.width()}x{widget.height()})")
                                break

            if canvas:
                # Store reference to prevent garbage collection
                self._canvas = canvas
                self._click_filter = ClickEventFilter(self, canvas, qt_backend)
                canvas.installEventFilter(self._click_filter)
                print(f"[OK] Click event filter installed on {type(canvas).__name__}")
            else:
                print("[WARN] Could not find canvas widget for click detection")
                print("       Listing all widgets for debugging:")
                if app:
                    for w in app.allWidgets()[:20]:  # Limit to first 20
                        print(f"         - {type(w).__name__}: {w.width()}x{w.height()}")
                print("       Use 'Select -> Select by Name' menu instead")

        except Exception as e:
            print(f"[WARN] Could not setup click selection: {e}")
            import traceback
            traceback.print_exc()
            print("       Use 'Select -> Select by Name' menu instead")


    def _handle_click_select(self, x, y):
        """Handle a click at screen coordinates (x, y) for selection."""
        print(f"[CLICK] Processing click at screen ({x}, {y})")

        try:
            context = self.display.Context
            view = self.display.View

            # Check if MoveTo detects anything - if so, let native Qt handler do Select()
            # We don't call Select() here because native mouseReleaseEvent will do it
            try:
                self.display.MoveTo(int(x), int(y))
                context.InitDetected()
                detected_count = 0
                while context.MoreDetected():
                    detected_count += 1
                    context.NextDetected()
                print(f"[CLICK] MoveTo detected {detected_count} shapes")

                if detected_count > 0:
                    # Native Qt mouseReleaseEvent will call Select() - don't do it here
                    # to avoid double-triggering the callback (which would toggle twice)
                    print(f"[CLICK] MoveTo working - native Qt will handle Select()")
                    return  # Let native handler do the selection
            except Exception as e:
                print(f"[CLICK] MoveTo/Select failed: {e}")

            # Fallback: Use bounding box intersection with ray
            print("[CLICK] Using ray-cast fallback...")
            from OCC.Core.gp import gp_Pnt, gp_Dir, gp_Lin

            # Get view parameters - Eye() returns (x, y, z) tuple
            eye = view.Eye()
            eye_x, eye_y, eye_z = eye[0], eye[1], eye[2]
            print(f"[CLICK] Eye position: ({eye_x:.1f}, {eye_y:.1f}, {eye_z:.1f})")

            # Convert screen point to 3D world coordinates using ConvertWithProj
            # ConvertWithProj returns (X, Y, Z, Vx, Vy, Vz) - point and direction
            try:
                conv_result = view.ConvertWithProj(int(x), int(y))
                # ConvertWithProj returns 6 values: X, Y, Z (point) and Vx, Vy, Vz (direction)
                if len(conv_result) >= 6:
                    x3d, y3d, z3d = conv_result[0], conv_result[1], conv_result[2]
                    ray_dir_x, ray_dir_y, ray_dir_z = conv_result[3], conv_result[4], conv_result[5]
                    print(f"[CLICK] ConvertWithProj point: ({x3d:.1f}, {y3d:.1f}, {z3d:.1f})")
                    print(f"[CLICK] ConvertWithProj dir: ({ray_dir_x:.3f}, {ray_dir_y:.3f}, {ray_dir_z:.3f})")
                else:
                    raise ValueError(f"ConvertWithProj returned {len(conv_result)} values, expected 6")
            except Exception as e:
                print(f"[CLICK] ConvertWithProj failed: {e}, using eye-based ray")
                # Fallback: use projection direction from eye to target
                at = view.At()
                at_x, at_y, at_z = at[0], at[1], at[2]
                ray_dir_x = at_x - eye_x
                ray_dir_y = at_y - eye_y
                ray_dir_z = at_z - eye_z
                ray_length = (ray_dir_x**2 + ray_dir_y**2 + ray_dir_z**2)**0.5
                if ray_length > 1e-10:
                    ray_dir_x /= ray_length
                    ray_dir_y /= ray_length
                    ray_dir_z /= ray_length
                # Use eye position as ray origin
                x3d, y3d, z3d = eye_x, eye_y, eye_z
                print(f"[CLICK] Fallback ray from eye toward At: ({ray_dir_x:.3f}, {ray_dir_y:.3f}, {ray_dir_z:.3f})")

            # Normalize direction (in case ConvertWithProj direction isn't normalized)
            ray_length = (ray_dir_x**2 + ray_dir_y**2 + ray_dir_z**2)**0.5
            if ray_length < 1e-10:
                print("[CLICK] Ray length too small")
                return
            ray_dir_x /= ray_length
            ray_dir_y /= ray_length
            ray_dir_z /= ray_length

            # Check each part - use shape proximity check
            best_part = None
            best_dist = float('inf')
            hits = []

            for part_name, part in self.subsystem.parts.items():
                if part.bounding_box:
                    bb = part.bounding_box
                    min_pt, max_pt = bb

                    # Convert bounding box from meters back to mm for comparison
                    min_mm = (min_pt[0] * 1000, min_pt[1] * 1000, min_pt[2] * 1000)
                    max_mm = (max_pt[0] * 1000, max_pt[1] * 1000, max_pt[2] * 1000)

                    # Ray-AABB intersection test
                    if self._ray_intersects_box(eye_x, eye_y, eye_z,
                                                 ray_dir_x, ray_dir_y, ray_dir_z,
                                                 min_mm, max_mm):
                        # Calculate distance from eye to box center
                        cx = (min_mm[0] + max_mm[0]) / 2
                        cy = (min_mm[1] + max_mm[1]) / 2
                        cz = (min_mm[2] + max_mm[2]) / 2
                        dist = ((eye_x - cx)**2 + (eye_y - cy)**2 + (eye_z - cz)**2)**0.5
                        hits.append((part_name, dist))
                        if dist < best_dist:
                            best_dist = dist
                            best_part = part_name

            if hits:
                print(f"[CLICK] Ray hits {len(hits)} bounding boxes: {[h[0] for h in hits[:5]]}...")

            if best_part:
                self._toggle_part_selection(best_part)
                print(f"[CLICK] Selected: {best_part} (distance: {best_dist:.1f})")
            else:
                # Debug: show some bounding boxes for comparison
                if self.subsystem.parts:
                    first_part = next(iter(self.subsystem.parts.values()))
                    if first_part.bounding_box:
                        bb = first_part.bounding_box
                        min_mm = (bb[0][0] * 1000, bb[0][1] * 1000, bb[0][2] * 1000)
                        max_mm = (bb[1][0] * 1000, bb[1][1] * 1000, bb[1][2] * 1000)
                        print(f"[CLICK] Sample bounding box (first part): min={min_mm}, max={max_mm}")
                print(f"[CLICK] No part found at screen ({x}, {y})")

        except Exception as e:
            print(f"[CLICK] Error: {e}")
            import traceback
            traceback.print_exc()

    def _handle_rect_select(self, min_x: int, min_y: int, max_x: int, max_y: int):
        """Handle drag rectangle selection - select all parts within screen rectangle."""
        print(f"[RECT] Processing rectangle selection: ({min_x}, {min_y}) to ({max_x}, {max_y})")

        try:
            view = self.display.View
            selected_count = 0

            for part_name, part in self.subsystem.parts.items():
                # Get the center of mass in world coordinates (meters -> mm for OCC)
                com = part.center_of_mass
                world_x = com[0] * 1000  # Convert m to mm
                world_y = com[1] * 1000
                world_z = com[2] * 1000

                # Project 3D point to 2D screen coordinates
                try:
                    screen_x, screen_y = view.Convert(world_x, world_y, world_z)

                    # Check if screen point is within selection rectangle
                    if min_x <= screen_x <= max_x and min_y <= screen_y <= max_y:
                        # Add to selection if not already selected
                        if part_name not in self.selected_parts:
                            self._select_part(part_name)
                            selected_count += 1
                except Exception as e:
                    # Fallback: use bounding box center
                    if part.bounding_box:
                        bb = part.bounding_box
                        cx = ((bb[0][0] + bb[1][0]) / 2) * 1000
                        cy = ((bb[0][1] + bb[1][1]) / 2) * 1000
                        cz = ((bb[0][2] + bb[1][2]) / 2) * 1000
                        try:
                            screen_x, screen_y = view.Convert(cx, cy, cz)
                            if min_x <= screen_x <= max_x and min_y <= screen_y <= max_y:
                                if part_name not in self.selected_parts:
                                    self._select_part(part_name)
                                    selected_count += 1
                        except:
                            pass

            print(f"[RECT] Selected {selected_count} parts")

            # Update main window selection display if available
            if hasattr(self, 'main_window') and self.main_window:
                self.main_window.update_selection_display()

        except Exception as e:
            print(f"[RECT] Error: {e}")
            import traceback
            traceback.print_exc()

    def _ray_intersects_box(self, ox, oy, oz, dx, dy, dz, box_min, box_max):
        """Check if a ray intersects an axis-aligned bounding box (slab method)."""
        tmin = float('-inf')
        tmax = float('inf')

        # Check X slab
        if abs(dx) > 1e-10:
            t1 = (box_min[0] - ox) / dx
            t2 = (box_max[0] - ox) / dx
            tmin = max(tmin, min(t1, t2))
            tmax = min(tmax, max(t1, t2))
        elif ox < box_min[0] or ox > box_max[0]:
            return False

        # Check Y slab
        if abs(dy) > 1e-10:
            t1 = (box_min[1] - oy) / dy
            t2 = (box_max[1] - oy) / dy
            tmin = max(tmin, min(t1, t2))
            tmax = min(tmax, max(t1, t2))
        elif oy < box_min[1] or oy > box_max[1]:
            return False

        # Check Z slab
        if abs(dz) > 1e-10:
            t1 = (box_min[2] - oz) / dz
            t2 = (box_max[2] - oz) / dz
            tmin = max(tmin, min(t1, t2))
            tmax = min(tmax, max(t1, t2))
        elif oz < box_min[2] or oz > box_max[2]:
            return False

        # Ray intersects if tmax >= tmin and tmax > 0 (box is in front of ray)
        return tmax >= tmin and tmax > 0

    def _setup_menus(self):
        """Set up the menu bar."""
        # Debug menu (temporary - for diagnosing selection issues)
        self.add_menu("Debug")
        self.add_function_to_menu("Debug", self._debug_selection_pipeline)

        # File menu
        self.add_menu("File")
        self.add_function_to_menu("File", self._menu_generate_output)

        # Selection menu
        self.add_menu("Select")
        self.add_function_to_menu("Select", self._menu_get_selection)
        self.add_function_to_menu("Select", self._menu_clear_selection)
        self.add_function_to_menu("Select", self._menu_select_by_name)

        # Define menu
        self.add_menu("Define")
        self.add_function_to_menu("Define", self._menu_define_link)
        self.add_function_to_menu("Define", self._menu_define_joint)
        self.add_function_to_menu("Define", self._menu_add_motor)
        self.add_function_to_menu("Define", self._menu_add_sensor)
        self.add_function_to_menu("Define", self._menu_set_static_parent)

        # View menu
        self.add_menu("View")
        self.add_function_to_menu("View", self._menu_show_definitions)
        self.add_function_to_menu("View", self._menu_highlight_undefined)
        self.add_function_to_menu("View", self._menu_list_parts)

    def _debug_selection_pipeline(self):
        """Debug function to test each stage of the selection pipeline."""
        print("\n" + "="*70)
        print("SELECTION PIPELINE DIAGNOSTICS (v2)")
        print("="*70)

        context = self.display.Context
        first_part = next(iter(self.subsystem.parts.values()), None)

        # =====================================================================
        # STAGE 1: Display Object
        # =====================================================================
        print("\n[STAGE 1] Display object check:")
        print(f"  display type: {type(self.display)}")
        print(f"  display.Context: {hasattr(self.display, 'Context')} -> {type(context).__name__}")
        print(f"  display.View: {hasattr(self.display, 'View')}")
        print(f"  display.MoveTo: {hasattr(self.display, 'MoveTo')}")
        print(f"  display.Select: {hasattr(self.display, 'Select')}")
        stage1_ok = all([hasattr(self.display, x) for x in ['Context', 'View', 'MoveTo', 'Select']])
        print(f"  -> Stage 1: {'PASS' if stage1_ok else 'FAIL'}")

        # =====================================================================
        # STAGE 2: Callbacks
        # =====================================================================
        print("\n[STAGE 2] Callback registration:")
        if hasattr(self.display, '_select_callbacks'):
            cb_count = len(self.display._select_callbacks)
            print(f"  _select_callbacks: {cb_count} registered")
            for i, cb in enumerate(self.display._select_callbacks):
                print(f"    [{i}] {cb}")
            stage2_ok = cb_count > 0
        else:
            print("  _select_callbacks: NOT FOUND")
            stage2_ok = False
        print(f"  -> Stage 2: {'PASS' if stage2_ok else 'FAIL'}")

        # =====================================================================
        # STAGE 3: AIS Shapes
        # =====================================================================
        print("\n[STAGE 3] AIS shape check:")
        ais_count = sum(1 for p in self.subsystem.parts.values() if p.ais_shape is not None)
        print(f"  Parts with AIS shapes: {ais_count}/{len(self.subsystem.parts)}")
        stage3_ok = ais_count > 0
        print(f"  -> Stage 3: {'PASS' if stage3_ok else 'FAIL'}")

        # =====================================================================
        # STAGE 4: Qt Backend & Event Filter
        # =====================================================================
        print("\n[STAGE 4] Qt backend & event filter:")
        qt_backend = None
        QtWidgets = None
        try:
            try:
                from PyQt5 import QtCore, QtWidgets
                qt_backend = "PyQt5"
            except ImportError:
                try:
                    from PySide2 import QtCore, QtWidgets
                    qt_backend = "PySide2"
                except ImportError:
                    try:
                        from PyQt6 import QtCore, QtWidgets
                        qt_backend = "PyQt6"
                    except ImportError:
                        try:
                            from PySide6 import QtCore, QtWidgets
                            qt_backend = "PySide6"
                        except ImportError:
                            pass
        except Exception as e:
            print(f"  Qt import error: {e}")

        print(f"  Qt backend: {qt_backend if qt_backend else 'NOT FOUND'}")

        # Check event filter
        has_filter = hasattr(self, '_click_filter') and self._click_filter is not None
        has_canvas = hasattr(self, '_canvas') and self._canvas is not None
        print(f"  Event filter installed: {has_filter}")
        print(f"  Canvas widget stored: {has_canvas}")
        if has_canvas:
            print(f"    Canvas type: {type(self._canvas).__name__}")
            print(f"    Canvas size: {self._canvas.width()}x{self._canvas.height()}")

        stage4_ok = qt_backend is not None and has_filter and has_canvas
        print(f"  -> Stage 4: {'PASS' if stage4_ok else 'FAIL'}")

        # =====================================================================
        # STAGE 5: Qt Widget Tree (find the viewer widget)
        # =====================================================================
        print("\n[STAGE 5] Qt widget tree:")
        if QtWidgets:
            app = QtWidgets.QApplication.instance()
            if app:
                print(f"  QApplication instance: Found")
                print(f"  Top-level widgets:")
                for w in app.topLevelWidgets():
                    wname = type(w).__name__
                    has_canva = hasattr(w, 'canva')
                    has_central = hasattr(w, 'centralWidget')
                    print(f"    - {wname} ({w.width()}x{w.height()}) canva={has_canva} central={has_central}")
                    if has_canva:
                        c = w.canva
                        print(f"      -> canva: {type(c).__name__} ({c.width()}x{c.height()})")
                    if has_central and w.centralWidget():
                        c = w.centralWidget()
                        print(f"      -> centralWidget: {type(c).__name__} ({c.width()}x{c.height()})")
            else:
                print(f"  QApplication instance: NOT FOUND")
        else:
            print(f"  Qt not available, skipping widget tree")

        # =====================================================================
        # STAGE 6: Bounding Box Data
        # =====================================================================
        print("\n[STAGE 6] Bounding box data:")
        bb_count = sum(1 for p in self.subsystem.parts.values() if p.bounding_box is not None)
        print(f"  Parts with bounding boxes: {bb_count}/{len(self.subsystem.parts)}")
        if first_part and first_part.bounding_box:
            bb = first_part.bounding_box
            min_mm = (bb[0][0] * 1000, bb[0][1] * 1000, bb[0][2] * 1000)
            max_mm = (bb[1][0] * 1000, bb[1][1] * 1000, bb[1][2] * 1000)
            print(f"  First part bounding box (mm):")
            print(f"    min: ({min_mm[0]:.1f}, {min_mm[1]:.1f}, {min_mm[2]:.1f})")
            print(f"    max: ({max_mm[0]:.1f}, {max_mm[1]:.1f}, {max_mm[2]:.1f})")
            size = (max_mm[0]-min_mm[0], max_mm[1]-min_mm[1], max_mm[2]-min_mm[2])
            print(f"    size: ({size[0]:.1f}, {size[1]:.1f}, {size[2]:.1f})")
        stage6_ok = bb_count > 0
        print(f"  -> Stage 6: {'PASS' if stage6_ok else 'FAIL'}")

        # =====================================================================
        # STAGE 7: View Parameters (for ray casting)
        # =====================================================================
        print("\n[STAGE 7] View parameters (ray casting):")
        ray_origin = None
        ray_dir = None
        try:
            view = self.display.View
            eye = view.Eye()
            at = view.At()
            print(f"  Eye position: ({eye[0]:.1f}, {eye[1]:.1f}, {eye[2]:.1f})")
            print(f"  At (target): ({at[0]:.1f}, {at[1]:.1f}, {at[2]:.1f})")

            # Test coordinate conversion using ConvertWithProj
            # ConvertWithProj returns (X, Y, Z, Vx, Vy, Vz) - point and direction
            try:
                conv = view.ConvertWithProj(512, 384)
                print(f"  ConvertWithProj(512,384) returned {len(conv)} values")
                if len(conv) >= 6:
                    print(f"  3D point: ({conv[0]:.1f}, {conv[1]:.1f}, {conv[2]:.1f})")
                    print(f"  Direction: ({conv[3]:.3f}, {conv[4]:.3f}, {conv[5]:.3f})")
                    ray_origin = (conv[0], conv[1], conv[2])
                    ray_dir = (conv[3], conv[4], conv[5])
                elif len(conv) >= 3:
                    print(f"  3D point only: ({conv[0]:.1f}, {conv[1]:.1f}, {conv[2]:.1f})")
                    ray_origin = (conv[0], conv[1], conv[2])
                    # Calculate direction from eye to point
                    dx, dy, dz = conv[0] - eye[0], conv[1] - eye[1], conv[2] - eye[2]
                    length = (dx**2 + dy**2 + dz**2)**0.5
                    if length > 0:
                        ray_dir = (dx/length, dy/length, dz/length)
            except Exception as e:
                print(f"  ConvertWithProj failed: {e}")
                # Fallback: use eye->at direction
                dx, dy, dz = at[0] - eye[0], at[1] - eye[1], at[2] - eye[2]
                length = (dx**2 + dy**2 + dz**2)**0.5
                if length > 0:
                    ray_dir = (dx/length, dy/length, dz/length)
                    ray_origin = (eye[0], eye[1], eye[2])
                    print(f"  Fallback ray dir: ({ray_dir[0]:.3f}, {ray_dir[1]:.3f}, {ray_dir[2]:.3f})")

            stage7_ok = ray_origin is not None and ray_dir is not None
        except Exception as e:
            print(f"  View parameter error: {e}")
            stage7_ok = False
        print(f"  -> Stage 7: {'PASS' if stage7_ok else 'FAIL'}")

        # =====================================================================
        # STAGE 8: Ray-Box Intersection Test
        # =====================================================================
        print("\n[STAGE 8] Ray-box intersection test:")
        try:
            if ray_origin is None or ray_dir is None:
                print("  Skipped - no valid ray from Stage 7")
                stage8_ok = False
            else:
                # Test ray against all bounding boxes
                hits = []
                for part_name, part in self.subsystem.parts.items():
                    if part.bounding_box:
                        bb = part.bounding_box
                        min_mm = (bb[0][0] * 1000, bb[0][1] * 1000, bb[0][2] * 1000)
                        max_mm = (bb[1][0] * 1000, bb[1][1] * 1000, bb[1][2] * 1000)
                        if self._ray_intersects_box(ray_origin[0], ray_origin[1], ray_origin[2],
                                                     ray_dir[0], ray_dir[1], ray_dir[2],
                                                     min_mm, max_mm):
                            hits.append(part_name)

                print(f"  Ray from center of screen hits {len(hits)} bounding boxes")
                if hits:
                    print(f"    First 5 hits: {hits[:5]}")
                stage8_ok = True  # Test ran successfully (hits or not)
        except Exception as e:
            print(f"  Ray-box test error: {e}")
            stage8_ok = False
        print(f"  -> Stage 8: {'PASS' if stage8_ok else 'FAIL'}")

        # =====================================================================
        # STAGE 9: Native OCC MoveTo Detection
        # =====================================================================
        print("\n[STAGE 9] Native OCC MoveTo detection:")
        try:
            self.display.MoveTo(512, 384)
            context.InitDetected()
            detected_count = 0
            while context.MoreDetected():
                detected_count += 1
                context.NextDetected()
            print(f"  MoveTo(512,384) detected: {detected_count} shapes")

            # Test multiple points
            total_detections = 0
            for x, y in [(100, 100), (200, 200), (300, 300), (400, 400), (500, 500), (600, 400), (700, 300)]:
                self.display.MoveTo(x, y)
                context.InitDetected()
                count = 0
                while context.MoreDetected():
                    count += 1
                    context.NextDetected()
                total_detections += count

            print(f"  Total detections across 7 test points: {total_detections}")
            stage9_ok = detected_count > 0 or total_detections > 0
        except Exception as e:
            print(f"  MoveTo detection error: {e}")
            stage9_ok = False
        print(f"  -> Stage 9: {'PASS' if stage9_ok else 'FAIL - MoveTo broken, using ray-cast fallback'}")

        # =====================================================================
        # STAGE 10: Programmatic Selection (SetSelected)
        # =====================================================================
        print("\n[STAGE 10] Programmatic selection (SetSelected):")
        if first_part and first_part.ais_shape:
            try:
                context.ClearSelected(True)
                context.SetSelected(first_part.ais_shape, True)
                context.UpdateCurrentViewer()

                context.InitSelected()
                count = 0
                while context.MoreSelected():
                    count += 1
                    context.NextSelected()
                print(f"  SetSelected on first part: {count} selected")
                print(f"  (Check viewer - first part should be highlighted)")
                stage10_ok = count > 0
            except Exception as e:
                print(f"  SetSelected error: {e}")
                stage10_ok = False
        else:
            print(f"  No parts available for test")
            stage10_ok = False
        print(f"  -> Stage 10: {'PASS' if stage10_ok else 'FAIL'}")

        # =====================================================================
        # STAGE 11: Simulate Click Handler
        # =====================================================================
        print("\n[STAGE 11] Simulate click handler:")
        try:
            print(f"  Calling _handle_click_select(512, 384)...")
            self._handle_click_select(512, 384)
            print(f"  Click handler completed")
            stage11_ok = True
        except Exception as e:
            print(f"  Click handler error: {e}")
            import traceback
            traceback.print_exc()
            stage11_ok = False
        print(f"  -> Stage 11: {'PASS' if stage11_ok else 'FAIL'}")

        # =====================================================================
        # SUMMARY
        # =====================================================================
        print("\n" + "="*70)
        print("DIAGNOSTIC SUMMARY")
        print("="*70)
        results = [
            ("1. Display object", stage1_ok),
            ("2. Callbacks", stage2_ok),
            ("3. AIS shapes", stage3_ok),
            ("4. Qt & event filter", stage4_ok),
            ("6. Bounding boxes", stage6_ok),
            ("7. View parameters", stage7_ok),
            ("8. Ray-box test", stage8_ok),
            ("9. MoveTo detection", stage9_ok),
            ("10. SetSelected", stage10_ok),
            ("11. Click handler", stage11_ok),
        ]

        for name, ok in results:
            status = "PASS" if ok else "FAIL"
            print(f"  {name}: {status}")

        print("\n" + "="*70)
        print("INTERPRETATION:")
        print("="*70)
        if not stage4_ok:
            print("  * Stage 4 FAIL: Qt event filter not installed!")
            print("    -> Clicks cannot be captured")
            print("    -> Check Qt backend installation")
        if not stage9_ok and stage8_ok:
            print("  * Stage 9 FAIL but Stage 8 PASS: MoveTo detection broken")
            print("    -> This is a known PythonOCC issue")
            print("    -> Ray-cast fallback should work if Stage 4 passes")
        if stage4_ok and stage8_ok and not stage9_ok:
            print("  * Stages 4 & 8 PASS: Click selection should work via ray-cast!")
            print("    -> If clicking still fails, check Stage 11 output")
        if all(ok for _, ok in results):
            print("  * All stages PASS: Selection should be working!")
        print("="*70 + "\n")

    def _on_shape_selected(self, selected_shapes, *args):
        """Callback when shape is selected."""
        print(f"[CALLBACK] selected_shapes={len(selected_shapes)} types={[type(s).__name__ for s in selected_shapes]}")

        # The selected_shapes list contains TopoDS shapes (Face, Solid, etc.)
        # We need to find which part each selected shape belongs to
        from OCC.Core.TopExp import TopExp_Explorer
        from OCC.Core.TopAbs import TopAbs_FACE, TopAbs_SOLID

        for selected_shape in selected_shapes:
            found = False

            # Try to match the selected shape (or its parent) against our parts
            for part_name, part in self.subsystem.parts.items():
                if part.shape is None:
                    continue

                # Method 1: Direct comparison using IsSame
                try:
                    if part.shape.IsSame(selected_shape):
                        self._toggle_part_selection(part_name)
                        found = True
                        break
                except Exception:
                    pass

                # Method 2: Check if selected face/edge is part of this shape
                try:
                    # Explore faces in the part's shape
                    explorer = TopExp_Explorer(part.shape, TopAbs_FACE)
                    while explorer.More():
                        face = explorer.Current()
                        if face.IsSame(selected_shape):
                            self._toggle_part_selection(part_name)
                            found = True
                            break
                        explorer.Next()
                    if found:
                        break

                    # Also try solids
                    explorer = TopExp_Explorer(part.shape, TopAbs_SOLID)
                    while explorer.More():
                        solid = explorer.Current()
                        if solid.IsSame(selected_shape):
                            self._toggle_part_selection(part_name)
                            found = True
                            break
                        explorer.Next()
                    if found:
                        break
                except Exception as e:
                    pass

            if not found:
                print(f"[CALLBACK] Could not match shape {type(selected_shape).__name__} to any part")

    def _toggle_part_selection(self, part_name: str):
        """Toggle selection state of a part and update its color."""
        if part_name not in self.subsystem.parts:
            return

        part = self.subsystem.parts[part_name]

        if part_name in self.selected_parts:
            # Deselect - restore original color
            self.selected_parts.remove(part_name)
            part.is_selected = False
            if part.ais_shape:
                self.display.Context.SetColor(
                    part.ais_shape,
                    Quantity_Color(part.color[0], part.color[1], part.color[2], Quantity_TOC_RGB),
                    True
                )
            print(f"  Deselected: {part_name}")
        else:
            # Select - highlight in orange
            self.selected_parts.append(part_name)
            part.is_selected = True
            if part.ais_shape:
                self.display.Context.SetColor(
                    part.ais_shape,
                    Quantity_Color(SELECTION_COLOR[0], SELECTION_COLOR[1], SELECTION_COLOR[2], Quantity_TOC_RGB),
                    True
                )
            print(f"  Selected: {part_name}")

        self.display.Context.UpdateCurrentViewer()

        # Update main window selection display if available
        if hasattr(self, 'main_window') and self.main_window:
            self.main_window.update_selection_display()

    def _select_part(self, part_name: str):
        """Select a part (add to selection) and highlight it orange."""
        if part_name not in self.subsystem.parts:
            return
        if part_name in self.selected_parts:
            return  # Already selected

        part = self.subsystem.parts[part_name]
        self.selected_parts.append(part_name)
        part.is_selected = True

        if part.ais_shape:
            self.display.Context.SetColor(
                part.ais_shape,
                Quantity_Color(SELECTION_COLOR[0], SELECTION_COLOR[1], SELECTION_COLOR[2], Quantity_TOC_RGB),
                True
            )
        self.display.Context.UpdateCurrentViewer()

    def _deselect_part(self, part_name: str):
        """Deselect a part and restore its original color."""
        if part_name not in self.subsystem.parts:
            return
        if part_name not in self.selected_parts:
            return  # Not selected

        part = self.subsystem.parts[part_name]
        self.selected_parts.remove(part_name)
        part.is_selected = False

        if part.ais_shape:
            self.display.Context.SetColor(
                part.ais_shape,
                Quantity_Color(part.color[0], part.color[1], part.color[2], Quantity_TOC_RGB),
                True
            )
        self.display.Context.UpdateCurrentViewer()

    def _clear_all_selections(self):
        """Clear all selections and restore original colors."""
        for part_name in list(self.selected_parts):
            self._deselect_part(part_name)
        self.selected_parts.clear()

    def clear_selection(self):
        """Public method to clear all selections."""
        self._clear_all_selections()
        if self.display:
            self.display.Context.ClearSelected(True)

    # =========================================================================
    # Dialog Helper Methods (used by GUI dialogs)
    # =========================================================================

    def _create_link_from_dialog(self, data: dict):
        """Create a link definition from dialog result data."""
        link = LinkDefinition(
            name=data['name'],
            part_names=data['part_names'],
            mass=data['mass'],
            mass_override=data['mass_override'],
            center_of_mass=data['center_of_mass']
        )

        self.subsystem.links[data['name']] = link
        print(f"[OK] Created link: {data['name']} with {len(data['part_names'])} part(s)")

        # Update part colors to show they're assigned (green)
        for part_name in data['part_names']:
            if part_name in self.subsystem.parts:
                part = self.subsystem.parts[part_name]
                part.color = ASSIGNED_COLOR
                part.is_selected = False
                if part.ais_shape:
                    self.display.Context.SetColor(
                        part.ais_shape,
                        Quantity_Color(ASSIGNED_COLOR[0], ASSIGNED_COLOR[1], ASSIGNED_COLOR[2], Quantity_TOC_RGB),
                        True
                    )

        # Clear selection list since parts are now assigned
        self.selected_parts.clear()
        self.display.Context.UpdateCurrentViewer()

    def _create_joint_from_dialog(self, data: dict):
        """Create a joint definition from dialog result data."""
        # Calculate origin if not provided
        origin = data.get('origin')
        if origin is None or origin == (0.0, 0.0, 0.0):
            origin = self._calculate_joint_origin(data['parent_link'], data['child_link'])

        joint = JointDefinition(
            name=data['name'],
            joint_type=data['joint_type'],
            parent_link=data['parent_link'],
            child_link=data['child_link'],
            origin=origin,
            axis=data['axis'],
            limits=data['limits']
        )

        self.subsystem.joints[data['name']] = joint
        print(f"[OK] Created joint: {data['name']} ({data['joint_type']}) "
              f"connecting {data['parent_link']} -> {data['child_link']}")

    def _create_motor_from_dialog(self, data: dict):
        """Create a motor definition from dialog result data."""
        motor = MotorDefinition(
            name=data['name'],
            joint_name=data['joint_name'],
            motor_type=data['motor_type'],
            gear_ratio=data['gear_ratio'],
            controller_type=data['controller_type'],
            device_id=data['device_id'],
            inverted=data['inverted']
        )

        self.subsystem.motors[data['name']] = motor
        print(f"[OK] Added motor: {data['name']} ({data['motor_type']}) "
              f"to joint {data['joint_name']}")

    def _create_sensor_from_dialog(self, data: dict):
        """Create a sensor definition from dialog result data."""
        sensor = SensorDefinition(
            name=data['name'],
            sensor_type=data['sensor_type'],
            joint_name=data['joint_name'],
            controller_type=data['controller_type'],
            hal_ports=data.get('hal_ports', []),
            can_id=data.get('can_id'),
            ticks_per_revolution=data['ticks_per_revolution']
        )

        self.subsystem.sensors[data['name']] = sensor
        print(f"[OK] Added sensor: {data['name']} ({data['sensor_type']}) "
              f"to joint {data['joint_name']}")

    def get_parts_for_link(self, link_name: str) -> List[str]:
        """Get list of part names belonging to a link."""
        if link_name in self.subsystem.links:
            return self.subsystem.links[link_name].part_names
        return []

    def get_parts_for_joint(self, joint_name: str) -> List[str]:
        """Get list of part names involved in a joint (from both links)."""
        if joint_name not in self.subsystem.joints:
            return []

        joint = self.subsystem.joints[joint_name]
        parts = []

        # Get parts from parent link
        if joint.parent_link in self.subsystem.links:
            parts.extend(self.subsystem.links[joint.parent_link].part_names)

        # Get parts from child link
        if joint.child_link in self.subsystem.links:
            parts.extend(self.subsystem.links[joint.child_link].part_names)

        return parts

    def get_link_names_for_joint(self, joint_name: str) -> Tuple[Optional[str], Optional[str]]:
        """Get parent and child link names for a joint."""
        if joint_name in self.subsystem.joints:
            joint = self.subsystem.joints[joint_name]
            return (joint.parent_link, joint.child_link)
        return (None, None)

    # =========================================================================
    # Update Methods (for editing existing definitions)
    # =========================================================================

    def _update_link_from_dialog(self, old_name: str, data: dict):
        """Update an existing link definition from dialog result data."""
        if old_name not in self.subsystem.links:
            return

        old_link = self.subsystem.links[old_name]

        # Find parts that were removed from the link
        removed_parts = set(old_link.part_names) - set(data['part_names'])
        added_parts = set(data['part_names']) - set(old_link.part_names)

        # Remove old link
        del self.subsystem.links[old_name]

        # Update any joints that referenced the old link name
        if old_name != data['name']:
            for joint in self.subsystem.joints.values():
                if joint.parent_link == old_name:
                    joint.parent_link = data['name']
                if joint.child_link == old_name:
                    joint.child_link = data['name']

        # Create updated link
        link = LinkDefinition(
            name=data['name'],
            part_names=data['part_names'],
            mass=data['mass'],
            mass_override=data['mass_override'],
            center_of_mass=data['center_of_mass']
        )
        self.subsystem.links[data['name']] = link

        # Update colors for removed parts (back to original)
        for part_name in removed_parts:
            if part_name in self.subsystem.parts:
                part = self.subsystem.parts[part_name]
                # Reset to muted color if not in any other link
                in_other_link = any(part_name in l.part_names for l in self.subsystem.links.values())
                if not in_other_link:
                    idx = list(self.subsystem.parts.keys()).index(part_name) % len(MUTED_COLORS)
                    part.color = MUTED_COLORS[idx]
                    if part.ais_shape and self.display:
                        self.display.Context.SetColor(
                            part.ais_shape,
                            Quantity_Color(part.color[0], part.color[1], part.color[2], Quantity_TOC_RGB),
                            True
                        )

        # Update colors for added parts (green assigned color)
        for part_name in added_parts:
            if part_name in self.subsystem.parts:
                part = self.subsystem.parts[part_name]
                part.color = ASSIGNED_COLOR
                part.is_selected = False
                if part.ais_shape and self.display:
                    self.display.Context.SetColor(
                        part.ais_shape,
                        Quantity_Color(ASSIGNED_COLOR[0], ASSIGNED_COLOR[1], ASSIGNED_COLOR[2], Quantity_TOC_RGB),
                        True
                    )

        if self.display:
            self.display.Context.UpdateCurrentViewer()

        print(f"[OK] Updated link: {data['name']}")

    def _update_joint_from_dialog(self, old_name: str, data: dict):
        """Update an existing joint definition from dialog result data."""
        if old_name not in self.subsystem.joints:
            return

        # Remove old joint
        del self.subsystem.joints[old_name]

        # Update any motors/sensors that referenced the old joint name
        if old_name != data['name']:
            for motor in self.subsystem.motors.values():
                if motor.joint_name == old_name:
                    motor.joint_name = data['name']
            for sensor in self.subsystem.sensors.values():
                if sensor.joint_name == old_name:
                    sensor.joint_name = data['name']

        # Calculate origin if not provided
        origin = data.get('origin')
        if origin is None or origin == (0.0, 0.0, 0.0):
            origin = self._calculate_joint_origin(data['parent_link'], data['child_link'])

        # Create updated joint
        joint = JointDefinition(
            name=data['name'],
            joint_type=data['joint_type'],
            parent_link=data['parent_link'],
            child_link=data['child_link'],
            origin=origin,
            axis=data['axis'],
            limits=data['limits']
        )
        self.subsystem.joints[data['name']] = joint
        print(f"[OK] Updated joint: {data['name']}")

    def _update_motor_from_dialog(self, old_name: str, data: dict):
        """Update an existing motor definition from dialog result data."""
        if old_name not in self.subsystem.motors:
            return

        # Remove old motor
        del self.subsystem.motors[old_name]

        # Create updated motor
        motor = MotorDefinition(
            name=data['name'],
            joint_name=data['joint_name'],
            motor_type=data['motor_type'],
            gear_ratio=data['gear_ratio'],
            controller_type=data['controller_type'],
            device_id=data['device_id'],
            inverted=data['inverted']
        )
        self.subsystem.motors[data['name']] = motor
        print(f"[OK] Updated motor: {data['name']}")

    def _update_sensor_from_dialog(self, old_name: str, data: dict):
        """Update an existing sensor definition from dialog result data."""
        if old_name not in self.subsystem.sensors:
            return

        # Remove old sensor
        del self.subsystem.sensors[old_name]

        # Create updated sensor
        sensor = SensorDefinition(
            name=data['name'],
            sensor_type=data['sensor_type'],
            joint_name=data['joint_name'],
            controller_type=data['controller_type'],
            hal_ports=data.get('hal_ports', []),
            can_id=data.get('can_id'),
            ticks_per_revolution=data['ticks_per_revolution']
        )
        self.subsystem.sensors[data['name']] = sensor
        print(f"[OK] Updated sensor: {data['name']}")

    # =========================================================================
    # Menu Functions
    # =========================================================================

    def _menu_define_link(self):
        """Menu: Define selected parts as a link."""
        self.define_link_from_selection()

    def _menu_define_joint(self):
        """Menu: Define a joint between two links."""
        self.define_joint_dialog()

    def _menu_add_motor(self):
        """Menu: Add a motor to a joint."""
        self.add_motor_dialog()

    def _menu_add_sensor(self):
        """Menu: Add a sensor to a joint."""
        self.add_sensor_dialog()

    def _menu_set_static_parent(self):
        """Menu: Set which link undefined parts attach to."""
        self.set_static_parent_dialog()

    def _menu_generate_output(self):
        """Menu: Generate output files."""
        self.generate_output()

    def _menu_show_definitions(self):
        """Menu: Show all current definitions."""
        self.print_definitions()

    def _menu_highlight_undefined(self):
        """Menu: Highlight parts not assigned to any link."""
        self.highlight_undefined_parts()

    def _menu_list_parts(self):
        """Menu: List all parts with their names."""
        print("\n--- All Parts ---")
        for i, (part_name, part) in enumerate(self.subsystem.parts.items()):
            vol_cm3 = part.volume * 1e6
            print(f"  {i+1}. {part_name} (vol: {vol_cm3:.2f} cm³)")
        print(f"Total: {len(self.subsystem.parts)} parts\n")

    def _menu_get_selection(self):
        """Menu: Get currently selected objects from viewer context."""
        context = self.display.Context

        # Try using GetSelectedShapes() method first
        try:
            selected_shapes = self.display.GetSelectedShapes()
            if selected_shapes:
                for shp in selected_shapes:
                    for part_name, part in self.subsystem.parts.items():
                        try:
                            if part.shape.IsSame(shp):
                                if part_name not in self.selected_parts:
                                    self.selected_parts.append(part_name)
                                    print(f"Found selected: {part_name}")
                                break
                        except Exception:
                            pass
                if self.selected_parts:
                    print(f"Currently selected: {self.selected_parts}")
                    return
        except Exception as e:
            print(f"[DEBUG] GetSelectedShapes failed: {e}")

        # Fallback: iterate through context selection
        try:
            context.InitSelected()
            while context.MoreSelected():
                try:
                    # Get the selected shape directly
                    selected_shape = context.SelectedShape()
                    for part_name, part in self.subsystem.parts.items():
                        try:
                            if part.shape.IsSame(selected_shape):
                                if part_name not in self.selected_parts:
                                    self.selected_parts.append(part_name)
                                    print(f"Found selected: {part_name}")
                                break
                        except Exception:
                            pass
                except Exception as e:
                    print(f"[DEBUG] Could not get selected shape: {e}")
                context.NextSelected()
        except Exception as e:
            print(f"[DEBUG] Context iteration failed: {e}")

        if self.selected_parts:
            print(f"Currently selected: {self.selected_parts}")
        else:
            print("No parts found in viewer selection. Use 'Select -> Select by Name' instead.")

    def _menu_clear_selection(self):
        """Menu: Clear current selection and restore original colors."""
        self._clear_all_selections()
        self.display.Context.ClearSelected(True)
        print("Selection cleared - all parts restored to original colors.")

    def _menu_select_by_name(self):
        """Menu: Select a part by entering its name (can add multiple)."""
        print("\n--- Select Part by Name ---")
        print("Available parts:")
        for i, part_name in enumerate(self.subsystem.parts.keys()):
            selected = " [SELECTED - ORANGE]" if part_name in self.selected_parts else ""
            print(f"  {i+1}. {part_name}{selected}")

        print("\nEnter part names/numbers separated by commas (e.g., '1,2,3' or 'Part_1,Part_2')")
        print("Or enter 'all' to select all, 'none' to clear selection")
        selection = input("Selection: ").strip()

        if not selection:
            print("Cancelled.")
            return

        if selection.lower() == 'none':
            self._clear_all_selections()
            print("Selection cleared.")
            return

        if selection.lower() == 'all':
            for part_name in self.subsystem.parts.keys():
                self._select_part(part_name)
            print(f"Selected all {len(self.selected_parts)} parts (highlighted orange)")
            return

        # Parse comma-separated list
        items = [s.strip() for s in selection.split(',')]
        for item in items:
            name = item
            # Check if user entered a number
            try:
                idx = int(item) - 1
                if 0 <= idx < len(self.subsystem.parts):
                    name = list(self.subsystem.parts.keys())[idx]
            except ValueError:
                pass  # User entered a name, not a number

            if name in self.subsystem.parts:
                if name not in self.selected_parts:
                    self._select_part(name)
                    print(f"Added (orange): {name}")
                else:
                    print(f"Already selected: {name}")
            else:
                print(f"Not found: {item}")

        print(f"Currently selected: {self.selected_parts}")

    # =========================================================================
    # Definition Functions
    # =========================================================================

    def define_link_from_selection(self):
        """Define selected parts as a link."""
        if not self.selected_parts:
            print("[ERROR] No parts selected. Click on parts first.")
            return

        # Simple input (will be replaced with proper dialog)
        print("\n--- Define Link ---")
        print(f"Parts: {self.selected_parts}")

        name = input("Link name: ").strip()
        if not name:
            print("Cancelled.")
            return

        # Check if name already exists
        if name in self.subsystem.links:
            print(f"[ERROR] Link '{name}' already exists.")
            return

        # Calculate combined mass from volumes
        total_volume = sum(
            self.subsystem.parts[p].volume
            for p in self.selected_parts
            if p in self.subsystem.parts
        )
        auto_mass = total_volume * DEFAULT_DENSITY

        print(f"Auto-calculated mass: {auto_mass:.3f} kg")
        mass_input = input(f"Mass override (or Enter for auto): ").strip()

        if mass_input:
            try:
                mass = float(mass_input)
                mass_override = True
            except ValueError:
                print("Invalid mass, using auto-calculated.")
                mass = auto_mass
                mass_override = False
        else:
            mass = auto_mass
            mass_override = False

        # Calculate combined center of mass
        com = self._calculate_combined_com(self.selected_parts)

        # Create link definition
        link = LinkDefinition(
            name=name,
            part_names=list(self.selected_parts),
            mass=mass,
            mass_override=mass_override,
            center_of_mass=com
        )

        self.subsystem.links[name] = link
        print(f"[OK] Created link: {name} with {len(self.selected_parts)} part(s)")

        # Update part colors to show they're assigned (green)
        # Also update their base color so they stay green when deselected
        for part_name in list(self.selected_parts):
            if part_name in self.subsystem.parts:
                part = self.subsystem.parts[part_name]
                # Update the part's base color to "assigned" green
                part.color = ASSIGNED_COLOR
                part.is_selected = False
                # Apply the color
                if part.ais_shape:
                    self.display.Context.SetColor(
                        part.ais_shape,
                        Quantity_Color(ASSIGNED_COLOR[0], ASSIGNED_COLOR[1], ASSIGNED_COLOR[2], Quantity_TOC_RGB),
                        True
                    )

        # Clear selection list since parts are now assigned
        self.selected_parts.clear()
        self.display.Context.UpdateCurrentViewer()
        print(f"    Parts assigned to link shown in green")

    def define_joint_dialog(self):
        """Define a joint between two links."""
        if len(self.subsystem.links) < 2:
            print("[ERROR] Need at least 2 links defined to create a joint.")
            return

        print("\n--- Define Joint ---")
        print(f"Available links: {list(self.subsystem.links.keys())}")

        name = input("Joint name: ").strip()
        if not name:
            print("Cancelled.")
            return

        parent = input("Parent link name: ").strip()
        if parent not in self.subsystem.links:
            print(f"[ERROR] Link '{parent}' not found.")
            return

        child = input("Child link name: ").strip()
        if child not in self.subsystem.links:
            print(f"[ERROR] Link '{child}' not found.")
            return

        print("Joint types: revolute, prismatic, fixed")
        joint_type = input("Joint type: ").strip().lower()
        if joint_type not in ["revolute", "prismatic", "fixed"]:
            print("[ERROR] Invalid joint type.")
            return

        # Auto-calculate origin from closest points between parts
        origin = self._calculate_joint_origin(parent, child)
        print(f"Auto-calculated origin: ({origin[0]:.4f}, {origin[1]:.4f}, {origin[2]:.4f})")

        # Get axis from user
        print("Enter axis as x,y,z (e.g., '0,0,1' for Z-axis):")
        axis_input = input("Axis [0,0,1]: ").strip()
        if axis_input:
            try:
                parts = axis_input.split(",")
                axis = (float(parts[0]), float(parts[1]), float(parts[2]))
                # Normalize
                mag = math.sqrt(axis[0]**2 + axis[1]**2 + axis[2]**2)
                axis = (axis[0]/mag, axis[1]/mag, axis[2]/mag)
            except (ValueError, IndexError):
                print("Invalid axis, using Z-axis.")
                axis = (0.0, 0.0, 1.0)
        else:
            axis = (0.0, 0.0, 1.0)

        # Get limits for revolute/prismatic joints
        limits = None
        if joint_type in ["revolute", "prismatic"]:
            limits_input = input("Limits (min,max) or Enter for unlimited: ").strip()
            if limits_input:
                try:
                    parts = limits_input.split(",")
                    limits = (float(parts[0]), float(parts[1]))
                except (ValueError, IndexError):
                    print("Invalid limits, using unlimited.")
                    limits = None

        joint = JointDefinition(
            name=name,
            joint_type=joint_type,
            parent_link=parent,
            child_link=child,
            origin=origin,
            axis=axis,
            limits=limits
        )

        self.subsystem.joints[name] = joint
        print(f"[OK] Created joint: {name} ({joint_type}) connecting {parent} -> {child}")

    def add_motor_dialog(self):
        """Add a motor to a joint."""
        if not self.subsystem.joints:
            print("[ERROR] No joints defined. Create a joint first.")
            return

        print("\n" + "="*50)
        print("ADD MOTOR")
        print("="*50)
        print(f"Available joints: {list(self.subsystem.joints.keys())}")

        name = input("\nMotor name: ").strip()
        if not name:
            print("Cancelled.")
            return

        joint_name = input("Joint to drive: ").strip()
        if joint_name not in self.subsystem.joints:
            print(f"[ERROR] Joint '{joint_name}' not found.")
            return

        print("\nMotor types:")
        print("  krakenx60 - WCP Kraken X60 (brushless)")
        print("  neo       - REV NEO (brushless)")
        print("  neo550    - REV NEO 550 (brushless)")
        print("  neovortex - REV NEO Vortex (brushless)")
        print("  falcon500 - CTRE Falcon 500 (brushless)")
        print("  cim       - CIM motor (brushed)")
        print("  minicim   - Mini CIM (brushed)")
        print("  bag       - BAG motor (brushed)")
        print("  venom     - Playing With Fusion Venom")
        motor_type = input("Motor type [krakenx60]: ").strip().lower() or "krakenx60"
        if motor_type not in ["krakenx60", "neo", "neo550", "neovortex", "falcon500", "cim", "minicim", "bag", "venom"]:
            print(f"[WARNING] Unknown motor type '{motor_type}', using krakenx60")
            motor_type = "krakenx60"

        try:
            gear_ratio = float(input("Gear ratio (e.g., 60 for 60:1) [1.0]: ").strip() or "1.0")
        except ValueError:
            gear_ratio = 1.0

        print("\nController type:")
        print("  pwm - PWM motor controller (e.g., Spark, Talon SR)")
        print("  can - CAN motor controller (e.g., SparkMax, TalonFX)")
        controller_type = input("Controller type [can]: ").strip().lower() or "can"
        if controller_type not in ["pwm", "can"]:
            controller_type = "can"

        if controller_type == "pwm":
            try:
                device_id = int(input("PWM port (0-9) [0]: ").strip() or "0")
            except ValueError:
                device_id = 0
            id_label = f"PWM[{device_id}]"
        else:  # CAN
            try:
                device_id = int(input("CAN ID (1-62) [1]: ").strip() or "1")
            except ValueError:
                device_id = 1
            id_label = f"CAN ID {device_id}"

        inverted_input = input("Inverted? (y/n) [n]: ").strip().lower()
        inverted = inverted_input == 'y'

        motor = MotorDefinition(
            name=name,
            joint_name=joint_name,
            motor_type=motor_type,
            gear_ratio=gear_ratio,
            controller_type=controller_type,
            device_id=device_id,
            inverted=inverted
        )

        self.subsystem.motors[name] = motor
        print(f"\n[OK] Added motor: {name}")
        print(f"     Type: {motor_type}, Gear ratio: {gear_ratio}:1")
        print(f"     Controller: {id_label}, Inverted: {inverted}")
        print(f"     Drives joint: {joint_name}")

    def add_sensor_dialog(self):
        """Add a sensor to a joint."""
        if not self.subsystem.joints:
            print("[ERROR] No joints defined. Create a joint first.")
            return

        print("\n" + "="*50)
        print("ADD SENSOR")
        print("="*50)
        print(f"Available joints: {list(self.subsystem.joints.keys())}")

        name = input("\nSensor name: ").strip()
        if not name:
            print("Cancelled.")
            return

        joint_name = input("Joint to measure: ").strip()
        if joint_name not in self.subsystem.joints:
            print(f"[ERROR] Joint '{joint_name}' not found.")
            return

        print("\nSensor types:")
        print("  encoder  - Quadrature encoder (DIO ports)")
        print("  cancoder - CTRE CANcoder (CAN bus)")
        print("  duty_cycle - REV Through Bore Encoder (DIO port)")
        sensor_type = input("Sensor type [encoder]: ").strip().lower() or "encoder"

        hal_ports = []
        can_id = None
        ticks = 2048

        if sensor_type == "encoder":
            print("\nQuadrature encoder uses two DIO ports (A and B channels)")
            try:
                port_a = int(input("DIO port A [0]: ").strip() or "0")
                port_b = int(input("DIO port B [1]: ").strip() or "1")
                hal_ports = [port_a, port_b]
            except ValueError:
                hal_ports = [0, 1]

            try:
                ticks = int(input("Ticks per revolution [2048]: ").strip() or "2048")
            except ValueError:
                ticks = 2048

            controller_type = "dio"
            id_label = f"DIO[{hal_ports[0]}, {hal_ports[1]}]"

        elif sensor_type == "cancoder":
            print("\nCANcoder uses CAN bus")
            try:
                can_id = int(input("CAN ID [1]: ").strip() or "1")
            except ValueError:
                can_id = 1

            ticks = 4096  # CANcoder resolution
            controller_type = "can"
            id_label = f"CAN ID {can_id}"

        elif sensor_type == "duty_cycle":
            print("\nDuty cycle encoder uses one DIO port")
            try:
                port = int(input("DIO port [0]: ").strip() or "0")
                hal_ports = [port]
            except ValueError:
                hal_ports = [0]

            ticks = 1  # Absolute encoder, reports position directly
            controller_type = "dio"
            id_label = f"DIO[{hal_ports[0]}]"

        else:
            print(f"[WARNING] Unknown sensor type '{sensor_type}', using encoder")
            sensor_type = "encoder"
            hal_ports = [0, 1]
            ticks = 2048
            controller_type = "dio"
            id_label = "DIO[0, 1]"

        sensor = SensorDefinition(
            name=name,
            sensor_type=sensor_type,
            joint_name=joint_name,
            controller_type=controller_type,
            hal_ports=hal_ports,
            can_id=can_id,
            ticks_per_revolution=ticks
        )

        self.subsystem.sensors[name] = sensor
        print(f"\n[OK] Added sensor: {name}")
        print(f"     Type: {sensor_type}, Resolution: {ticks} ticks/rev")
        print(f"     Connection: {id_label}")
        print(f"     Measures joint: {joint_name}")

    def set_static_parent_dialog(self):
        """Set which link undefined parts attach to."""
        if not self.subsystem.links:
            print("[ERROR] No links defined yet.")
            return

        print("\n--- Set Static Parent Link ---")
        print("Undefined parts will be merged and attached to this link.")
        print(f"Available links: {list(self.subsystem.links.keys())}")

        link_name = input("Parent link name: ").strip()
        if link_name not in self.subsystem.links:
            print(f"[ERROR] Link '{link_name}' not found.")
            return

        self.subsystem.static_parent_link = link_name
        print(f"[OK] Undefined parts will attach to: {link_name}")

    # =========================================================================
    # Helper Functions
    # =========================================================================

    def _calculate_combined_com(self, part_names: List[str]) -> Tuple[float, float, float]:
        """Calculate weighted center of mass for multiple parts."""
        total_mass = 0.0
        weighted_com = [0.0, 0.0, 0.0]

        for part_name in part_names:
            if part_name not in self.subsystem.parts:
                continue
            part = self.subsystem.parts[part_name]
            mass = part.volume * DEFAULT_DENSITY
            total_mass += mass
            weighted_com[0] += mass * part.center_of_mass[0]
            weighted_com[1] += mass * part.center_of_mass[1]
            weighted_com[2] += mass * part.center_of_mass[2]

        if total_mass > 0:
            return (
                weighted_com[0] / total_mass,
                weighted_com[1] / total_mass,
                weighted_com[2] / total_mass
            )
        return (0.0, 0.0, 0.0)

    def _calculate_joint_origin(self, parent_link: str, child_link: str) -> Tuple[float, float, float]:
        """
        Auto-calculate joint origin from closest points between parent and child parts.
        """
        parent_parts = self.subsystem.links[parent_link].part_names
        child_parts = self.subsystem.links[child_link].part_names

        min_dist = float('inf')
        best_point = (0.0, 0.0, 0.0)

        for p_name in parent_parts:
            if p_name not in self.subsystem.parts:
                continue
            p_shape = self.subsystem.parts[p_name].shape

            for c_name in child_parts:
                if c_name not in self.subsystem.parts:
                    continue
                c_shape = self.subsystem.parts[c_name].shape

                # Calculate minimum distance between shapes
                dist_calc = BRepExtrema_DistShapeShape(p_shape, c_shape)
                if dist_calc.IsDone() and dist_calc.NbSolution() > 0:
                    dist = dist_calc.Value()
                    if dist < min_dist:
                        min_dist = dist
                        # Get midpoint of closest points
                        pt1 = dist_calc.PointOnShape1(1)
                        pt2 = dist_calc.PointOnShape2(1)
                        # Convert to meters using detected unit scale
                        scale = self._unit_scale
                        best_point = (
                            (pt1.X() + pt2.X()) * 0.5 * scale,
                            (pt1.Y() + pt2.Y()) * 0.5 * scale,
                            (pt1.Z() + pt2.Z()) * 0.5 * scale
                        )

        return best_point

    def _get_undefined_parts(self) -> List[str]:
        """Get list of parts not assigned to any link."""
        assigned = set()
        for link in self.subsystem.links.values():
            assigned.update(link.part_names)

        return [p for p in self.subsystem.parts.keys() if p not in assigned]

    def highlight_undefined_parts(self):
        """Highlight parts not assigned to any link in soft red."""
        undefined = self._get_undefined_parts()
        print(f"\nUndefined parts ({len(undefined)}):")

        for part_name in undefined:
            if part_name in self.subsystem.parts:
                part = self.subsystem.parts[part_name]
                if part.ais_shape:
                    self.display.Context.SetColor(
                        part.ais_shape,
                        Quantity_Color(UNDEFINED_COLOR[0], UNDEFINED_COLOR[1], UNDEFINED_COLOR[2], Quantity_TOC_RGB),
                        True
                    )
                print(f"  - {part_name}")

        self.display.Context.UpdateCurrentViewer()

        if undefined:
            print(f"\nThese parts need to be assigned to links.")
            print(f"Use 'Define -> Set Static Parent' to auto-attach them to a base link.")
        else:
            print("All parts are assigned to links.")

    def print_definitions(self):
        """Print all current definitions."""
        print("\n" + "="*60)
        print("CURRENT DEFINITIONS")
        print("="*60)

        print(f"\nSubsystem: {self.subsystem.name}")
        print(f"Total parts: {len(self.subsystem.parts)}")

        print(f"\nLinks ({len(self.subsystem.links)}):")
        for link in self.subsystem.links.values():
            print(f"  - {link.name}: {link.part_names} ({link.mass:.3f} kg)")

        print(f"\nJoints ({len(self.subsystem.joints)}):")
        for joint in self.subsystem.joints.values():
            limits_str = f" limits={joint.limits}" if joint.limits else " (unlimited)"
            print(f"  - {joint.name}: {joint.joint_type} {joint.parent_link} -> {joint.child_link}{limits_str}")

        print(f"\nMotors ({len(self.subsystem.motors)}):")
        for motor in self.subsystem.motors.values():
            if motor.controller_type == "pwm":
                id_str = f"PWM[{motor.device_id}]"
            else:
                id_str = f"CAN[{motor.device_id}]"
            inv_str = " INVERTED" if motor.inverted else ""
            print(f"  - {motor.name}: {motor.motor_type} {motor.gear_ratio}:1 {id_str}{inv_str} -> {motor.joint_name}")

        print(f"\nSensors ({len(self.subsystem.sensors)}):")
        for sensor in self.subsystem.sensors.values():
            if sensor.controller_type == "can":
                id_str = f"CAN[{sensor.can_id}]"
            else:
                ports_str = ",".join(str(p) for p in sensor.hal_ports)
                id_str = f"DIO[{ports_str}]"
            print(f"  - {sensor.name}: {sensor.sensor_type} {id_str} ({sensor.ticks_per_revolution} ticks/rev) -> {sensor.joint_name}")

        undefined = self._get_undefined_parts()
        print(f"\nUndefined parts ({len(undefined)}): {undefined}")
        print(f"Static parent link: {self.subsystem.static_parent_link}")
        print("="*60 + "\n")

    # =========================================================================
    # Output Generation
    # =========================================================================

    def generate_output(self, output_dir: Optional[str] = None):
        """Generate OBJ meshes, config.json, and URDF.

        If --output was specified on command line, uses that directory.
        After generation, closes the editor if launched from SimpleSim.
        """
        if not self.subsystem.links:
            print("[ERROR] No links defined. Define at least one link first.")
            return

        if not self.subsystem.static_parent_link:
            print("[WARNING] No static parent link set. Undefined parts will be ignored.")

        # Determine output directory (priority: parameter > command-line --output > default)
        if output_dir:
            out_path = Path(output_dir)
        elif self._output_dir:
            out_path = Path(self._output_dir)
        else:
            out_path = Path("generated_projects") / self.subsystem.name

        out_path.mkdir(parents=True, exist_ok=True)
        meshes_path = out_path / "meshes"
        meshes_path.mkdir(exist_ok=True)

        print(f"\nGenerating output to: {out_path}")

        # Export meshes for each link
        mesh_files = {}
        for link_name, link in self.subsystem.links.items():
            mesh_file = self._export_link_mesh(link, meshes_path)
            if mesh_file:
                mesh_files[link_name] = mesh_file

        # Export static geometry if parent link is set
        undefined_parts = self._get_undefined_parts()
        if undefined_parts and self.subsystem.static_parent_link:
            static_mesh = self._export_static_mesh(undefined_parts, meshes_path)
            if static_mesh:
                # Add static parts to parent link's mesh list
                print(f"[OK] Static geometry attached to {self.subsystem.static_parent_link}")

        # Generate config.json
        config_file = self._generate_config(out_path, mesh_files)

        # Generate URDF from config
        urdf_file = self._generate_urdf(out_path, config_file)

        print(f"\n" + "="*60)
        print("OUTPUT GENERATED SUCCESSFULLY!")
        print("="*60)
        print(f"  Output directory: {out_path}")
        print(f"  - Meshes: {meshes_path}")
        print(f"  - Config: {config_file}")
        if urdf_file:
            print(f"  - URDF:   {urdf_file}")

        print(f"\n--- DEVICE MAPPING ---")
        print("Make sure your robot code uses these IDs:")
        print("\nMotors:")
        for motor in self.subsystem.motors.values():
            if motor.controller_type == "pwm":
                id_str = f"PWM[{motor.device_id}]"
            else:
                id_str = f"CAN ID {motor.device_id}"
            inv_str = " (INVERTED)" if motor.inverted else ""
            print(f"  {id_str} -> {motor.name} ({motor.motor_type}, {motor.gear_ratio}:1){inv_str} -> {motor.joint_name}")

        print("\nSensors:")
        for sensor in self.subsystem.sensors.values():
            if sensor.controller_type == "can":
                id_str = f"CAN ID {sensor.can_id}"
            else:
                ports_str = ", ".join(str(p) for p in sensor.hal_ports)
                id_str = f"DIO[{ports_str}]"
            print(f"  {id_str} -> {sensor.name} ({sensor.sensor_type}, {sensor.ticks_per_revolution} ticks/rev) -> {sensor.joint_name}")

        print(f"\n--- HOW TO RUN SIMULATION ---")
        print(f"1. Start your robot code with HAL Sim WebSocket extension")
        print(f"2. Run: python -m subsystemsim.hal_bridge.websocket_bridge {config_file}")
        print("="*60)

        # If launched from SimpleSim (with --output), close the editor after generation
        if self._output_dir and self._main_window:
            print("\nClosing CAD editor (launched from SimpleSim)...")
            # Use QTimer to close after a short delay so user can see the success message
            from PyQt5.QtCore import QTimer
            QTimer.singleShot(1500, self._main_window.close)

    def _export_link_mesh(self, link: LinkDefinition, output_dir: Path) -> Optional[Path]:
        """Export a link's parts as a single STL/OBJ mesh, scaled to meters."""
        from OCC.Core.BRepBuilderAPI import BRepBuilderAPI_Copy, BRepBuilderAPI_Transform
        from OCC.Core.TopoDS import TopoDS_Compound
        from OCC.Core.BRep import BRep_Builder
        from OCC.Core.gp import gp_Trsf, gp_Pnt

        # Combine all parts into one compound
        builder = BRep_Builder()
        compound = TopoDS_Compound()
        builder.MakeCompound(compound)

        for part_name in link.part_names:
            if part_name in self.subsystem.parts:
                # Make a copy of the shape
                copier = BRepBuilderAPI_Copy(self.subsystem.parts[part_name].shape)
                builder.Add(compound, copier.Shape())

        # Apply unit scaling to convert to meters
        if self._unit_scale != 1.0:
            scale_transform = gp_Trsf()
            scale_transform.SetScale(gp_Pnt(0, 0, 0), self._unit_scale)
            scaler = BRepBuilderAPI_Transform(compound, scale_transform, True)
            compound = scaler.Shape()

        # Mesh the compound (use scaled tolerance)
        mesh_tolerance = 0.0001  # 0.1mm in meters
        mesh = BRepMesh_IncrementalMesh(compound, mesh_tolerance)
        mesh.Perform()

        # Export as STL (OBJ not directly supported, but we can convert later or use STL)
        output_file = output_dir / f"{link.name}.stl"

        writer = StlAPI_Writer()
        writer.SetASCIIMode(False)  # Binary STL is smaller
        success = writer.Write(compound, str(output_file))

        if success:
            print(f"  [OK] Exported: {output_file.name} (scaled to meters)")
            return output_file
        else:
            print(f"  [ERROR] Failed to export: {link.name}")
            return None

    def _export_static_mesh(self, part_names: List[str], output_dir: Path) -> Optional[Path]:
        """Export undefined parts as static geometry, scaled to meters."""
        from OCC.Core.BRepBuilderAPI import BRepBuilderAPI_Copy, BRepBuilderAPI_Transform
        from OCC.Core.TopoDS import TopoDS_Compound
        from OCC.Core.BRep import BRep_Builder
        from OCC.Core.gp import gp_Trsf, gp_Pnt

        builder = BRep_Builder()
        compound = TopoDS_Compound()
        builder.MakeCompound(compound)

        for part_name in part_names:
            if part_name in self.subsystem.parts:
                copier = BRepBuilderAPI_Copy(self.subsystem.parts[part_name].shape)
                builder.Add(compound, copier.Shape())

        # Apply unit scaling to convert to meters
        if self._unit_scale != 1.0:
            scale_transform = gp_Trsf()
            scale_transform.SetScale(gp_Pnt(0, 0, 0), self._unit_scale)
            scaler = BRepBuilderAPI_Transform(compound, scale_transform, True)
            compound = scaler.Shape()

        # Mesh the compound (use scaled tolerance)
        mesh_tolerance = 0.0001  # 0.1mm in meters
        mesh = BRepMesh_IncrementalMesh(compound, mesh_tolerance)
        mesh.Perform()

        output_file = output_dir / "static_geometry.stl"

        writer = StlAPI_Writer()
        writer.SetASCIIMode(False)
        success = writer.Write(compound, str(output_file))

        if success:
            print(f"  [OK] Exported static geometry: {output_file.name} (scaled to meters)")
            return output_file
        else:
            print(f"  [ERROR] Failed to export static geometry")
            return None

    def _generate_config(self, output_dir: Path, mesh_files: Dict[str, Path]) -> Path:
        """
        Generate config.json file in the format expected by subsystemsim.core.config.

        This format is compatible with:
        - load_config() for loading into SubsystemModel
        - generate_urdf() for creating URDF files
        - HALWebSocketBridge for motor/sensor HAL mapping
        """
        config = {
            "name": self.subsystem.name,
            "links": [],
            "joints": [],
            "motors": [],
            "sensors": []
        }

        # Add links - format must match config.py expectations
        for link_name, link in self.subsystem.links.items():
            mesh_path = mesh_files.get(link_name)
            # Calculate proper inertia matrix (3x3)
            inertia_val = link.mass * 0.01  # Simple approximation
            inertia_matrix = [
                [inertia_val, 0.0, 0.0],
                [0.0, inertia_val, 0.0],
                [0.0, 0.0, inertia_val]
            ]

            link_config = {
                "name": link.name,
                "mesh": f"meshes/{mesh_path.name}" if mesh_path else "",
                "mass": link.mass,
                "center_of_mass": list(link.center_of_mass),  # Correct field name
                "inertia": inertia_matrix
            }
            config["links"].append(link_config)

        # Add joints - format must match config.py expectations
        for joint in self.subsystem.joints.values():
            joint_config = {
                "name": joint.name,
                "type": joint.joint_type,  # "revolute", "prismatic", "fixed"
                "parent": joint.parent_link,
                "child": joint.child_link,
                "axis": list(joint.axis),
                "origin": list(joint.origin),
                "limits": list(joint.limits) if joint.limits else None,
                "velocity_limit": 10.0,  # Default: 10 rad/s
                "effort_limit": 100.0    # Default: 100 Nm
            }
            config["joints"].append(joint_config)

        # Add motors - format must match config.py expectations
        for motor in self.subsystem.motors.values():
            motor_config = {
                "name": motor.name,
                "type": motor.motor_type,  # "neo", "cim", "falcon500", etc.
                "joint": motor.joint_name,
                "gear_ratio": motor.gear_ratio,
                "controller_type": motor.controller_type,  # "pwm" or "can"
                "hal_port": motor.device_id,  # PWM port or CAN ID
                "inverted": motor.inverted
            }
            config["motors"].append(motor_config)

        # Add sensors - format must match config.py expectations
        for sensor in self.subsystem.sensors.values():
            sensor_config = {
                "name": sensor.name,
                "type": sensor.sensor_type,  # "encoder", "cancoder", etc.
                "joint": sensor.joint_name,
                "controller_type": sensor.controller_type,  # "dio" or "can"
                "hal_ports": sensor.hal_ports,  # DIO ports for quadrature encoder
                "can_id": sensor.can_id,  # CAN ID for CANcoder
                "ticks_per_rev": sensor.ticks_per_revolution,
                "offset": 0.0
            }
            config["sensors"].append(sensor_config)

        # Write config file
        # If launched from SimpleSim (with --output), use "config.json" to match project expectations
        # Otherwise use the subsystem name for standalone usage
        if self._output_dir:
            config_file = output_dir / "config.json"
        else:
            config_file = output_dir / f"{self.subsystem.name}_config.json"

        with open(config_file, 'w') as f:
            json.dump(config, f, indent=2)

        print(f"  [OK] Generated: {config_file.name}")
        return config_file

    def _generate_urdf(self, output_dir: Path, config_file: Path) -> Optional[Path]:
        """Generate URDF file from the config using existing URDF generator."""
        try:
            # Import the existing subsystemsim modules
            import sys
            project_root = Path(__file__).parent.parent.parent
            if str(project_root) not in sys.path:
                sys.path.insert(0, str(project_root))

            from subsystemsim.core.config import load_config
            from subsystemsim.physics.urdf_generator import generate_urdf

            # Load the config we just created
            model = load_config(config_file)

            # Generate URDF
            urdf_file = output_dir / f"{self.subsystem.name}.urdf"
            generate_urdf(model, urdf_file)

            print(f"  [OK] Generated: {urdf_file.name}")
            return urdf_file

        except Exception as e:
            print(f"  [WARNING] Could not generate URDF: {e}")
            print("           You can generate it later with: python -m subsystemsim.physics.urdf_generator <config.json>")
            return None


def main():
    """Main entry point for CAD editor."""
    import sys
    import argparse
    from pathlib import Path

    # Add project root to path so imports work when running directly
    project_root = Path(__file__).parent.parent.parent
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))

    # Parse command line arguments
    parser = argparse.ArgumentParser(description="SubsystemSim CAD Editor")
    parser.add_argument("step_file", nargs="?", help="Path to STEP file to load")
    parser.add_argument("--output", "-o", type=str, help="Output directory for generated files")
    args = parser.parse_args()

    print("="*60)
    print("SubsystemSim CAD Editor")
    print("="*60)

    editor = CADEditor()

    # Store output directory if provided
    if args.output:
        editor._output_dir = args.output
        print(f"Output directory: {args.output}")

    # Get STEP file path
    if args.step_file:
        step_file = args.step_file
    else:
        step_file = input("Enter STEP file path: ").strip()
        if not step_file:
            print("No file specified. Exiting.")
            return

    # Remove quotes if user included them
    step_file = step_file.strip('"').strip("'")

    if editor.load_step_file(step_file):
        editor.start_viewer()
    else:
        print("Failed to load STEP file.")


if __name__ == "__main__":
    main()
