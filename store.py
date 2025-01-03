from typing import List, Dict, Optional
from datetime import datetime
from dataclasses import dataclass
from models.Machine import BaseMachine
from models.Response import (
    AutomationResponse, 
    AutomationSwitchResponse,
    CurrentResponse, 
    EnvironmentResponse, 
    EnvironmentTypeResponse, 
    MachineResponse, 
    SensorResponse, 
    SwitchResponse
)
from resources import http, redis
from logger.custom_logger import custom_logger


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
        try:
            # HTTP에서 데이터 가져오기
            self.environment_types: List[EnvironmentTypeResponse] = http.get_environment_types()
            self.environments: List[EnvironmentResponse] = http.get_environments()
            self.switches: List[SwitchResponse] = http.get_switches()
            self.machines: List[MachineResponse] = http.get_machines()
            self.sensors: List[SensorResponse] = http.get_sensors()
            self.automations: List[AutomationResponse] = http.get_automations()
            self.interval_automated_switches: List[AutomationSwitchResponse] = http.get_interval_device_states()
            self.currents: List[CurrentResponse] = http.get_currents()

            custom_logger.info(f"Store 데이터 로드 완료:")
            custom_logger.info(f"- Machines: {len(self.machines)}")
            custom_logger.info(f"- Automations: {len(self.automations)}")
            custom_logger.info(f"- Currents: {len(self.currents)}")

            # 기기 정보 업데이트
            self._update_machines()

            # Redis에 데이터 저장
            self._save_to_redis()


        except Exception as e:
            custom_logger.error(f"Store 초기화 실패: {str(e)}")
            raise

    def _save_to_redis(self) -> None:
        """데이터를 Redis에 저장"""
        try:
            # 각 데이터 타입별로 저장
            redis.set('environment_types', self.environment_types)
            redis.set('environments', self.environments)
            redis.set('switches', self.switches)
            redis.set('machines', self.machines)
            redis.set('sensors', self.sensors)
            redis.set('automations', self.automations)
            redis.set('interval_automated_switches', self.interval_automated_switches)
            redis.set('currents', self.currents)
            custom_logger.info("Redis에 데이터 저장 완료")

        except Exception as e:
            custom_logger.error(f"Redis 데이터 저장 실패: {str(e)}")
            raise

    def _parse_datetime(self, date_str: str) -> datetime:
        """ISO 형식의 문자열을 datetime으로 변환"""
        return datetime.fromisoformat(date_str.replace('Z', '+00:00'))

    def _update_machines(self) -> None:
        """기기 정보 업데이트"""
        merged_data = BaseMachine.merge_device_data(self.switches, self.machines)
        
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
