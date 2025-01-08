import datetime


class SwitchResponse:
    def __init__(self, device_id: int, name: str, status: bool, created_at: datetime.datetime):
        self.device_id = device_id
        self.name = name
        self.status = status
        self.created_at = created_at

class AutomationSwitchResponse:
    def __init__(self, name: str, status: bool, created_at: datetime.datetime, controlled_by: str):
        self.name = name
        self.status = status
        self.created_at = created_at
        self.controlled_by = controlled_by

class EnvironmentResponse:
    def __init__(self, name: str, value: float):
        self.name = name
        self.value = value

class EnvironmentTypeResponse:
    def __init__(self, id: int, name: str, unit: str, description: str, created_at: datetime.datetime):
        self.id = id
        self.name = name
        self.unit = unit
        self.description = description
        self.created_at = created_at

class AutomationResponse:
    def __init__(self, device_id: int, category: str, settings: dict, active: int, updated_at: datetime.datetime):
        self.device_id = device_id
        self.category = category
        self.settings = settings
        self.active = active
        self.updated_at = updated_at

class MachineResponse:
    def __init__(self, id: int, pin:int, name: str, created_at: datetime.datetime):
        self.id = id
        self.name = name
        self.created_at = created_at
        self.pin = pin
        
class SensorResponse:
    def __init__(self, id: int, name: str, created_at: datetime.datetime, pin: int):
        self.id = id
        self.name = name
        self.created_at = created_at
        self.pin = pin

class CurrentResponse:
    def __init__(self, device: str, current: float, created_at: datetime.datetime):
        self.device = device
        self.current = current
        self.created_at = created_at