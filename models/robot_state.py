"""Robot state model contracts."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class PIDConstants:
    """Container for PID gains."""

    kp: float = 1.0
    ki: float = 0.05
    kd: float = 0.1


@dataclass
class RobotState:
    """Minimal RobotState placeholder for integration imports."""

    pid: PIDConstants = field(default_factory=PIDConstants)
