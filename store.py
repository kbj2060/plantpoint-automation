from typing import List
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


class Store:
    def __init__(self):
        try:
            # HTTP에서 데이터 가져오기
            self.environment_type: List[EnvironmentTypeResponse] = http.get_environment_type()
            self.environments: List[EnvironmentResponse] = http.get_environments()
            self.switches: List[SwitchResponse] = http.get_switches()
            self.machines: List[MachineResponse] = http.get_machines()
            self.sensors: List[SensorResponse] = http.get_sensors()
            self.automations: List[AutomationResponse] = http.get_automations()
            self.interval_automated_switches: List[AutomationSwitchResponse] = http.get_interval_device_states()
            self.currents: List[CurrentResponse] = http.get_currents()

            custom_logger.info(f"Store 데이터 로드 완료:")
            custom_logger.info(f"- Machines: {len(self.machines)}")
            custom_logger.info(f"- Sensors: {len(self.sensors)}")
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
            redis.set('environment_type', self.environment_type)
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
