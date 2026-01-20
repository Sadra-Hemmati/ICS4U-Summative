"""
Warning system for SubsystemSim.

Provides a modular way to track and report simulation warnings.
Designed to be consumed by both console output and GUI components.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import List, Callable, Optional, Dict, Any
from collections import deque
import time


class WarningType(Enum):
    """Types of simulation warnings."""
    JOINT_AT_UPPER_LIMIT = "joint_at_upper_limit"
    JOINT_AT_LOWER_LIMIT = "joint_at_lower_limit"
    FORCE_CLAMPED = "force_clamped"
    VELOCITY_LIMIT = "velocity_limit"
    COLLISION = "collision"


@dataclass
class SimWarning:
    """A simulation warning event."""
    warning_type: WarningType
    joint_name: str
    message: str
    timestamp: float = field(default_factory=time.time)
    data: Dict[str, Any] = field(default_factory=dict)

    def __str__(self) -> str:
        return f"[{self.warning_type.value}] {self.joint_name}: {self.message}"


class WarningSystem:
    """
    Centralized warning system for simulation events.

    Supports:
    - Console logging
    - Callback-based notification (for GUI integration)
    - Warning history with automatic cleanup
    - Rate limiting to prevent spam
    """

    def __init__(self, history_size: int = 100, rate_limit_seconds: float = 1.0):
        """
        Initialize the warning system.

        Args:
            history_size: Maximum number of warnings to keep in history
            rate_limit_seconds: Minimum time between repeated warnings of same type/joint
        """
        self._history: deque = deque(maxlen=history_size)
        self._callbacks: List[Callable[[SimWarning], None]] = []
        self._rate_limit = rate_limit_seconds
        self._last_warning_time: Dict[str, float] = {}  # (type, joint) -> timestamp
        self._console_enabled = True

    def add_callback(self, callback: Callable[[SimWarning], None]):
        """
        Register a callback to be notified of warnings.

        Useful for GUI integration - the GUI can register a callback
        to update visual indicators when warnings occur.

        Args:
            callback: Function that takes a SimWarning and handles it
        """
        self._callbacks.append(callback)

    def remove_callback(self, callback: Callable[[SimWarning], None]):
        """Remove a previously registered callback."""
        if callback in self._callbacks:
            self._callbacks.remove(callback)

    def set_console_output(self, enabled: bool):
        """Enable or disable console output of warnings."""
        self._console_enabled = enabled

    def warn(self, warning_type: WarningType, joint_name: str, message: str,
             data: Optional[Dict[str, Any]] = None) -> Optional[SimWarning]:
        """
        Issue a warning.

        Args:
            warning_type: Type of warning
            joint_name: Name of the joint involved
            message: Human-readable warning message
            data: Optional additional data (e.g., current position, force applied)

        Returns:
            The SimWarning if it was issued, None if rate-limited
        """
        # Rate limiting - prevent spam for repeated warnings
        key = f"{warning_type.value}:{joint_name}"
        now = time.time()

        if key in self._last_warning_time:
            if now - self._last_warning_time[key] < self._rate_limit:
                return None  # Rate limited, don't issue warning

        self._last_warning_time[key] = now

        # Create warning
        warning = SimWarning(
            warning_type=warning_type,
            joint_name=joint_name,
            message=message,
            timestamp=now,
            data=data or {}
        )

        # Store in history
        self._history.append(warning)

        # Console output
        if self._console_enabled:
            print(f"[WARNING] {warning}", flush=True)

        # Notify callbacks
        for callback in self._callbacks:
            try:
                callback(warning)
            except Exception as e:
                print(f"Warning callback error: {e}", flush=True)

        return warning

    def warn_joint_at_limit(self, joint_name: str, position: float, limit: float,
                            force: float, is_upper: bool) -> Optional[SimWarning]:
        """
        Convenience method for joint limit warnings.

        Args:
            joint_name: Name of the joint
            position: Current joint position
            limit: The limit value being hit
            force: Force being applied into the limit
            is_upper: True if upper limit, False if lower limit
        """
        warning_type = WarningType.JOINT_AT_UPPER_LIMIT if is_upper else WarningType.JOINT_AT_LOWER_LIMIT
        limit_name = "upper" if is_upper else "lower"

        message = f"At {limit_name} limit ({limit:.3f}) with {abs(force):.1f}N pushing into limit"

        return self.warn(
            warning_type=warning_type,
            joint_name=joint_name,
            message=message,
            data={
                "position": position,
                "limit": limit,
                "force": force,
                "is_upper": is_upper
            }
        )

    def warn_force_clamped(self, joint_name: str, requested: float,
                           clamped: float, limit: float) -> Optional[SimWarning]:
        """
        Convenience method for force clamping warnings.

        Args:
            joint_name: Name of the joint
            requested: Originally requested force
            clamped: Actual clamped force
            limit: The effort limit
        """
        message = f"Force clamped from {requested:.1f}N to {clamped:.1f}N (limit: {limit:.1f}N)"

        return self.warn(
            warning_type=WarningType.FORCE_CLAMPED,
            joint_name=joint_name,
            message=message,
            data={
                "requested_force": requested,
                "clamped_force": clamped,
                "effort_limit": limit
            }
        )

    def get_history(self, limit: Optional[int] = None,
                    warning_type: Optional[WarningType] = None) -> List[SimWarning]:
        """
        Get warning history.

        Args:
            limit: Maximum number of warnings to return (most recent first)
            warning_type: Filter by warning type (None for all)

        Returns:
            List of warnings, most recent first
        """
        warnings = list(self._history)
        warnings.reverse()  # Most recent first

        if warning_type:
            warnings = [w for w in warnings if w.warning_type == warning_type]

        if limit:
            warnings = warnings[:limit]

        return warnings

    def get_active_warnings(self, max_age_seconds: float = 2.0) -> Dict[str, SimWarning]:
        """
        Get currently active warnings (recent warnings by joint).

        Useful for GUI to show current state indicators.

        Args:
            max_age_seconds: Only include warnings newer than this

        Returns:
            Dict mapping joint_name to most recent warning for that joint
        """
        now = time.time()
        active = {}

        for warning in reversed(self._history):
            if now - warning.timestamp > max_age_seconds:
                break
            if warning.joint_name not in active:
                active[warning.joint_name] = warning

        return active

    def clear_history(self):
        """Clear all warning history."""
        self._history.clear()
        self._last_warning_time.clear()
