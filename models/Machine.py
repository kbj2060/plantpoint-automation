from typing import Optional, List
from datetime import datetime


class BaseMachine:
    """Base machine representation for automation system."""

    def __init__(
        self,
        machine_id: Optional[int] = None,
        pin: Optional[int] = None,
        name: Optional[str] = None,
        status: Optional[int] = None,
        switch_created_at: Optional[str] = None
    ) -> None:
        self.machine_id = machine_id
        self.name = name
        self.mqtt_topic = f'switch/{name}' if name else None
        self.pin = pin
        self.status = status
        self.switch_created_at = switch_created_at

    def __str__(self) -> str:
        """객체를 문자열로 표현할 때 사용"""
        return f"BaseMachine({', '.join(f'{k}={v}' for k, v in self.__dict__.items())})"

    def __repr__(self) -> str:
        """디버깅/개발용 출력"""
        return self.__str__()

    def set_status(self, status: int) -> None:
        """Set machine status."""
        self.status = status

    def check_machine_on(self) -> bool:
        """Check if machine is on (status == 1)."""
        return self.status == 1

    @staticmethod
    def merge_device_data(switch_data: List[dict], device_data: List[dict]) -> List[dict]:
        """
        스위치 데이터의 status와 created_at을 device_data에 추가

        Args:
            switch_data: List of switch status dictionaries
            device_data: List of device configuration dictionaries

        Returns:
            Merged device data with status and switch_created_at fields
        """
        # 스위치 데이터를 device_id를 키로 하는 딕셔너리로 변환
        switch_dict = {
            switch['device_id']: {
                'status': switch['status'],
                'created_at': switch['created_at']
            } for switch in switch_data
        }

        # 디바이스 데이터에 status와 switch_created_at 추가
        for device in device_data:
            device_switch = switch_dict.get(device['id'], {'status': 0, 'created_at': None})
            device['status'] = device_switch['status']
            device['switch_created_at'] = device_switch['created_at']

        return device_data
