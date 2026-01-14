"""
STEP to OBJ Converter using FreeCAD.

Converts STEP CAD files to OBJ mesh files for use in PyBullet physics simulation.
Requires FreeCAD to be installed.
"""

import sys
from pathlib import Path
from typing import List, Optional, Tuple


def check_freecad_available() -> Tuple[bool, str]:
    """
    Check if FreeCAD is available.

    Returns:
        Tuple of (is_available, message)
    """
    try:
        import FreeCAD
        return True, f"FreeCAD {FreeCAD.Version()[0]}.{FreeCAD.Version()[1]} found"
    except ImportError:
        # Try common FreeCAD installation paths
        common_paths = [
            r"C:\Program Files\FreeCAD 0.21\bin",
            r"C:\Program Files\FreeCAD 0.20\bin",
            r"C:\Program Files (x86)\FreeCAD 0.21\bin",
            r"C:\Program Files (x86)\FreeCAD 0.20\bin",
            r"/usr/lib/freecad/lib",
            r"/usr/lib/freecad-python3/lib",
            r"/Applications/FreeCAD.app/Contents/Resources/lib",
        ]

        for path in common_paths:
            if Path(path).exists():
                sys.path.append(path)
                try:
                    import FreeCAD
                    return True, f"FreeCAD found at {path}"
                except ImportError:
                    continue

        return False, "FreeCAD not found. Please install FreeCAD or add it to system PATH."


def convert_step_to_obj(step_file: Path, output_dir: Optional[Path] = None) -> List[Path]:
    """
    Convert a STEP file to OBJ file(s).

    If the STEP file contains multiple parts, creates multiple OBJ files.

    Args:
        step_file: Path to input STEP file
        output_dir: Directory for output OBJ files (default: same as input)

    Returns:
        List of paths to created OBJ files

    Raises:
        ImportError: If FreeCAD is not available
        FileNotFoundError: If input file doesn't exist
        Exception: If conversion fails
    """
    # Check FreeCAD availability
    is_available, message = check_freecad_available()
    if not is_available:
        raise ImportError(message)

    import FreeCAD
    import Mesh

    # Validate input
    if not step_file.exists():
        raise FileNotFoundError(f"STEP file not found: {step_file}")

    # Set output directory
    if output_dir is None:
        output_dir = step_file.parent
    output_dir.mkdir(parents=True, exist_ok=True)

    print(f"\nConverting STEP to OBJ:")
    print(f"  Input: {step_file}")
    print(f"  Output: {output_dir}")

    # Create new FreeCAD document
    doc = FreeCAD.newDocument("StepImport")

    try:
        # Import STEP file
        print(f"  Loading STEP file...")
        import Part
        Part.insert(str(step_file), doc.Name)

        # Get all imported objects
        objects = doc.Objects
        print(f"  Found {len(objects)} object(s)")

        if len(objects) == 0:
            raise Exception("No objects found in STEP file")

        created_files = []

        # Convert each object to OBJ
        for i, obj in enumerate(objects):
            # Get object name (sanitize for filename)
            obj_name = obj.Label if hasattr(obj, 'Label') else f"part_{i}"
            obj_name = "".join(c if c.isalnum() or c in "-_" else "_" for c in obj_name)

            # Generate output filename
            if len(objects) == 1:
                # Single object: use original filename
                output_file = output_dir / f"{step_file.stem}.obj"
            else:
                # Multiple objects: append part name/number
                output_file = output_dir / f"{step_file.stem}_{obj_name}.obj"

            print(f"  Converting {obj.Label} -> {output_file.name}...")

            try:
                # Create mesh from shape
                if hasattr(obj, 'Shape'):
                    # Mesh the shape with reasonable quality
                    # Deviation: 0.1 (lower = more detailed, higher = simpler)
                    # Angular: 0.5 (angular deviation in radians)
                    mesh = doc.addObject("Mesh::Feature", f"Mesh_{obj.Label}")
                    mesh.Mesh = Mesh.Mesh(obj.Shape.tessellate(0.1))

                    # Export as OBJ
                    Mesh.export([mesh], str(output_file))

                    # Remove temporary mesh object
                    doc.removeObject(mesh.Name)

                    created_files.append(output_file)
                    print(f"    [OK] Created: {output_file.name}")
                else:
                    print(f"    [WARNING] Skipped: {obj.Label} (no shape)")

            except Exception as e:
                print(f"    [FAILED] Failed: {obj.Label} - {e}")

        print(f"\n[OK] Conversion complete! Created {len(created_files)} OBJ file(s)\n")

        return created_files

    finally:
        # Clean up document
        FreeCAD.closeDocument(doc.Name)


def get_freecad_install_instructions() -> str:
    """Get platform-specific FreeCAD installation instructions."""
    import platform

    system = platform.system()

    if system == "Windows":
        return """
FreeCAD Installation Instructions (Windows):

1. Download FreeCAD:
   https://www.freecad.org/downloads.php
   - Click "Windows 64-bit installer"
   - Download the latest stable version (0.21+)

2. Run the installer:
   - Follow installation wizard
   - Default options are fine
   - Install to: C:\\Program Files\\FreeCAD 0.21

3. Restart SubsystemSim after installation

Alternative - Portable Version:
   - Download "Windows 64-bit portable"
   - Extract to any folder
   - Add to PATH or move to known location
"""

    elif system == "Darwin":  # macOS
        return """
FreeCAD Installation Instructions (macOS):

1. Download FreeCAD:
   https://www.freecad.org/downloads.php
   - Click "macOS 64-bit dmg"
   - Download the latest stable version (0.21+)

2. Install:
   - Open the .dmg file
   - Drag FreeCAD to Applications folder

3. Restart SubsystemSim after installation

Alternative - Homebrew:
   brew install --cask freecad
"""

    else:  # Linux
        return """
FreeCAD Installation Instructions (Linux):

Ubuntu/Debian:
   sudo apt update
   sudo apt install freecad freecad-python3

Fedora:
   sudo dnf install freecad

Arch:
   sudo pacman -S freecad

Other distros:
   https://www.freecad.org/downloads.php

After installation, restart SubsystemSim.
"""


def batch_convert_step_files(step_files: List[Path], output_dir: Path) -> List[Path]:
    """
    Convert multiple STEP files to OBJ.

    Args:
        step_files: List of STEP file paths
        output_dir: Output directory for all OBJ files

    Returns:
        List of all created OBJ files
    """
    all_obj_files = []

    for step_file in step_files:
        try:
            obj_files = convert_step_to_obj(step_file, output_dir)
            all_obj_files.extend(obj_files)
        except Exception as e:
            print(f"Error converting {step_file.name}: {e}")

    return all_obj_files


# For standalone testing
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Convert STEP files to OBJ for SubsystemSim")
    parser.add_argument("step_file", type=str, help="Input STEP file")
    parser.add_argument("-o", "--output", type=str, help="Output directory (default: same as input)")
    parser.add_argument("--check", action="store_true", help="Check if FreeCAD is available")

    args = parser.parse_args()

    if args.check:
        is_available, message = check_freecad_available()
        print(message)
        if not is_available:
            print("\n" + get_freecad_install_instructions())
        sys.exit(0 if is_available else 1)

    # Convert file
    step_path = Path(args.step_file)
    output_path = Path(args.output) if args.output else None

    try:
        obj_files = convert_step_to_obj(step_path, output_path)
        print(f"\nSuccess! Created {len(obj_files)} OBJ file(s):")
        for obj_file in obj_files:
            print(f"  - {obj_file}")
    except Exception as e:
        print(f"\nError: {e}")
        if isinstance(e, ImportError):
            print(get_freecad_install_instructions())
        sys.exit(1)
