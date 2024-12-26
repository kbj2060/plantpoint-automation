from typing import List, Dict, Optional
from datetime import datetime
from dataclasses import dataclass
from interfaces.Machine import BaseMachine
from interfaces.Response import (
    AutomationResponse, 
    AutomationSwitchResponse, 
    EnvironmentResponse, 
    EnvironmentTypeResponse, 
    MachineResponse, 
    SensorResponse, 
    SwitchResponse
)
from resources import http


@dataclass
class DeviceTimeState:
    """디바이스의 시간 상태를 저장하는 클래스"""
    on_time: Optional[datetime] = None
    off_time: Optional[datetime] = None

    def update_time(self, new_time: datetime, is_on: bool) -> None:
        """시간 상태 업데이트"""
        if is_on:
            if not self.on_time or new_time > self.on_time:
                self.on_time = new_time
        else:
            if not self.off_time or new_time > self.off_time:
                self.off_time = new_time

    def to_dict(self) -> dict:
        """상태 정보를 딕셔너리로 변환"""
        return {
            'last_start_time': self.on_time,
            'last_toggle_time': self.off_time
        }


class Store:
    def __init__(self):
        self.environment_types: List[EnvironmentTypeResponse] = http.get_environment_types()
        self.environments: List[EnvironmentResponse] = http.get_environments()
        self.switches: List[SwitchResponse] = http.get_switches()
        self.machines: List[MachineResponse] = http.get_machines()
        self.sensors: List[SensorResponse] = http.get_sensors()
        self.automations: List[AutomationResponse] = http.get_automations()
        self.automated_switches: List[AutomationSwitchResponse] = http.get_automated_switches()
        
        self.automation_states: Dict[str, Dict] = self._process_automated_switches()

    def _parse_datetime(self, date_str: str) -> datetime:
        """ISO 형식의 문자열을 datetime으로 변환"""
        return datetime.fromisoformat(date_str.replace('Z', '+00:00'))

    def _process_automated_switches(self) -> Dict[str, Dict]:
        """자동화된 스위치 데이터를 디바이스별 상태 정보로 변환"""
        device_times: Dict[str, DeviceTimeState] = {}
        
        # 스위치 데이터 처리
        for switch in self.automated_switches:
            device_name = switch['name']
            if device_name not in device_times:
                device_times[device_name] = DeviceTimeState()
            
            created_at = self._parse_datetime(switch['created_at'])
            device_times[device_name].update_time(created_at, switch['status'])
        
        # DeviceTimeState 객체를 딕셔너리로 변환
        return {
            name: time_state.to_dict() 
            for name, time_state in device_times.items()
        }

    def get_automation_state(self, device_name: str) -> dict:
        """특정 디바이스의 자동화 상태 정보 반환"""
        state = self.automation_states.get(device_name, {})
        return {
            'last_start_time': state.get('last_start_time').isoformat() if state.get('last_start_time') else None,
            'last_toggle_time': state.get('last_toggle_time').isoformat() if state.get('last_toggle_time') else None
        }

    def update_machines(self, switch_data: list, device_data: list) -> None:
        """기기 정보 업데이트"""
        merged_data = BaseMachine.merge_device_data(switch_data, device_data)
        
        self.machines = [
            BaseMachine(
                machine_id=data['id'],
                name=data['name'],
                pin=data['pin'],
                status=data['status'],
                switch_created_at=data['switch_created_at']
            )
            for data in merged_data
        ]