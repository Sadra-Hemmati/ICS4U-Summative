"""
CAD processing utilities for SubsystemSim.
"""

from .step_converter import (
    convert_step_to_obj,
    check_freecad_available,
    get_freecad_install_instructions,
    batch_convert_step_files
)

from .cad_editor import (
    CADEditor,
    PartInfo,
    LinkDefinition,
    JointDefinition,
    MotorDefinition,
    SensorDefinition,
    SubsystemDefinition
)

__all__ = [
    # Legacy FreeCAD converter
    'convert_step_to_obj',
    'check_freecad_available',
    'get_freecad_install_instructions',
    'batch_convert_step_files',
    # New PythonOCC editor
    'CADEditor',
    'PartInfo',
    'LinkDefinition',
    'JointDefinition',
    'MotorDefinition',
    'SensorDefinition',
    'SubsystemDefinition'
]
