"""Response models for API data structures."""

from dataclasses import dataclass
from datetime import datetime
from typing import Dict, Any


@dataclass
class SwitchResponse:
    """Switch device status response."""
    device_id: int
    name: str
    status: bool
    created_at: datetime


@dataclass
class AutomationSwitchResponse:
    """Automated switch status response."""
    name: str
    status: bool
    created_at: datetime
    controlled_by: str


@dataclass
class EnvironmentResponse:
    """Environment sensor reading response."""
    name: str
    value: float


@dataclass
class EnvironmentTypeResponse:
    """Environment type configuration response."""
    id: int
    name: str
    unit: str
    description: str
    created_at: datetime


@dataclass
class AutomationResponse:
    """Automation configuration response."""
    device_id: int
    category: str
    settings: Dict[str, Any]
    active: int
    updated_at: datetime


@dataclass
class MachineResponse:
    """Machine/device configuration response."""
    id: int
    pin: int
    name: str
    created_at: datetime


@dataclass
class SensorResponse:
    """Sensor configuration response."""
    id: int
    name: str
    created_at: datetime
    pin: int


@dataclass
class CurrentResponse:
    """Current monitoring response."""
    device: str
    current: bool
    created_at: datetime
