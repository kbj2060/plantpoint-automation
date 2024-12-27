from abc import ABC, abstractmethod
from datetime import datetime
from typing import Optional, Tuple
from dataclasses import dataclass
from logger.custom_logger import custom_logger
from interfaces.Machine import BaseMachine
from resources import mqtt, ws, redis
from interfaces.Message import MQTTPayload, WSPayload, SwitchData
from constants import SWITCH_SOCKET_ADDRESS, WS_SWITCH_EVENT


@dataclass
class TimeConfig:
    """시간 설정을 관리하는 클래스"""
    value: int
    unit: str = 's'

    def to_seconds(self) -> int:
        """시간 단위를 초 단위로 변환"""
        units = {
            's': 1,           # 초
            'm': 60,          # 분
            'h': 3600,        # 시간
            'd': 86400        # 일
        }
        return self.value * units.get(self.unit, 1)


@dataclass
class IntervalState:
    """인터벌 자동화의 상태를 관리하는 클래스"""
    last_start_time: Optional[datetime] = None
    last_toggle_time: Optional[datetime] = None

    def start_new_cycle(self, now: datetime) -> None:
        """새로운 주기 시작"""
        self.last_start_time = now
        self.last_toggle_time = now

    def update_toggle_time(self, now: datetime) -> None:
        """토글 시간 업데이트"""
        self.last_toggle_time = now

    def get_elapsed_times(self, now: datetime) -> Tuple[float, float]:
        """경과 시간 계산"""
        if not self.last_start_time or not self.last_toggle_time:
            return 0.0, 0.0
        return (
            (now - self.last_start_time).total_seconds(),
            (now - self.last_toggle_time).total_seconds()
        )


class BaseAutomation(ABC):
    def __init__(self, device_id: int, category: str, active: bool, settings: dict, updated_at: str):
        self.device_id = device_id
        self.category = category
        self.active = active
        self.updated_at = updated_at
        self.name: Optional[str] = None
        self.mqtt_topic: Optional[str] = None
        self.pin: Optional[int] = None
        self.status: Optional[bool] = None
        self.switch_created_at: Optional[str] = None
        self._init_from_settings(settings)

    def send_mqtt_message(self, new_status: bool) -> None:
        """MQTT 메시지 전송"""
        try:
            mqtt_data: SwitchData = {
                'name': self.name,
                'value': new_status
            }
            mqtt_payload: MQTTPayload = {
                'pattern': self.mqtt_topic,
                'data': mqtt_data
            }
            mqtt.publish_message(self.mqtt_topic, mqtt_payload)
            custom_logger.info(f"MQTT 메시지 전송 성공: {self.name} = {new_status}")
        except Exception as e:
            custom_logger.error(f"MQTT 메시지 전송 실패: {str(e)}")
            raise

    def send_websocket_message(self, new_status: bool) -> None:
        """WebSocket 메시지 전송"""
        try:
            ws_payload: WSPayload = {
                'event': WS_SWITCH_EVENT,
                'data': { self.name: new_status }
            }
            ws_client = ws(url=f'{SWITCH_SOCKET_ADDRESS}/{self.name}')    
            ws_client.send_message(**ws_payload)
            ws_client.disconnect()
            custom_logger.info(f"WebSocket 메시지 전송 성공: {self.name} = {new_status}")
        except Exception as e:
            custom_logger.error(f"WebSocket 메시지 전송 실패: {str(e)}")
            raise

    def update_device_status(self, new_status: bool) -> None:
        """디바이스 상태 업데이트 및 메시지 전송"""
        try:
            self.send_mqtt_message(new_status)
            self.send_websocket_message(new_status)
            self.status = new_status
            custom_logger.success(f"상태 업데이트 성공: {self.name} = {new_status}")
        except Exception as e:
            custom_logger.error(f"상태 업데이트 실패: {str(e)}")
            raise

    def set_machine(self, machine: BaseMachine) -> None:
        """기기 정보 설정"""
        self.name = machine.name
        self.pin = machine.pin
        self.status = machine.status
        self.mqtt_topic = f"switch/{self.name}"
        self.switch_created_at = machine.switch_created_at

    def get_machine(self) -> BaseMachine:
        """현재 상태의 BaseMachine 객체 생성"""
        return BaseMachine(
            machine_id=self.device_id,
            name=self.name,
            pin=self.pin,
            status=self.status,
            switch_created_at=self.switch_created_at
        )

    @abstractmethod
    def _init_from_settings(self, settings: dict) -> None:
        """각 자동화 타입별 설정 초기화"""
        pass

    @abstractmethod
    def control(self) -> Optional[BaseMachine]:
        """자동화 로직 실행"""
        if not self.active:
            custom_logger.info(f"Device {self.name}: 자동화가 비활성화되어 있습니다.")
            return None
        return self.get_machine()  # BaseMachine 객체 반환

    @staticmethod
    def create_automation(automation_data: dict, store: 'Store') -> 'BaseAutomation':
        """자동화 인스턴스 생성 팩토리 메서드"""
        automation_types = {
            'range': RangeAutomation,
            'interval': IntervalAutomation,
            'target': TargetAutomation
        }
        
        category = automation_data.get('category')
        automation_class = automation_types.get(category)
        
        if not automation_class:
            raise ValueError(f"Unknown automation category: {category}")

        settings = automation_data.get('settings', {})
        if category == 'interval':
            device = next((d for d in store.machines if d.machine_id == automation_data.get('device_id')), None)
            if device:
                state = store.get_automation_state(device.name)
                settings.update(state)

        return automation_class(
            device_id=automation_data.get('device_id'),
            category=category,
            active=automation_data.get('active', False),
            settings=settings,
            updated_at=automation_data.get('updated_at')
        )

    def get_redis_key(self, name: str) -> str:
        """Redis 키 생성"""
        return f"environment/{name}"

    def get_sensor_value(self, sensor_name: str) -> Optional[float]:
        """Redis에서 센서값 조회"""
        try:
            value = redis.get(self.get_redis_key(sensor_name))
            return float(value) if value else None
        except (ValueError, TypeError) as e:
            custom_logger.error(f"센서값 조회 실패: {str(e)}")
            return None


class RangeAutomation(BaseAutomation):
    def _init_from_settings(self, settings: dict) -> None:
        self.start = settings.get('start')
        self.end = settings.get('end')

    def is_time_in_range(self, current_time: str) -> bool:
        """시간이 설정된 범위 내에 있는지 확인"""
        if self.start > self.end:  # 자정을 걸치는 경우 (예: 22:00 ~ 06:00)
            return current_time >= self.start or current_time <= self.end
        return self.start <= current_time <= self.end  # 일반적인 경우

    def control(self) -> Optional[BaseMachine]:
        """시간 기반 제어 실행"""
        if not super().control():
            return None

        if not all([self.start, self.end, self.pin]):
            custom_logger.error(f"Device {self.name}: 필수 설정이 누락되었습니다.")
            raise ValueError(f"Device {self.name}: 필수 설정이 누락되었습니다.")

        try:
            now = datetime.now().strftime('%H:%M')
            should_be_on = self.is_time_in_range(now)
            current_status = bool(self.status)
            
            if should_be_on != current_status:
                self.update_device_status(should_be_on)
                
            return self.get_machine()

        except Exception as e:
            custom_logger.error(f"Device {self.name} 제어 중 오류 발생: {str(e)}")
            raise


class IntervalAutomation(BaseAutomation):
    def _init_from_settings(self, settings: dict) -> None:
        if not settings:
            self.duration = self.interval = None
            self.state = IntervalState()
            return

        # 시간 설정 초기화
        duration_config = TimeConfig(**settings.get('duration', {}))
        interval_config = TimeConfig(**settings.get('interval', {}))
        self.duration = duration_config.to_seconds()
        self.interval = interval_config.to_seconds()

        # 상태 초기화 - UTC 시간을 naive datetime으로 변환
        def parse_datetime(dt_str: Optional[str]) -> Optional[datetime]:
            if not dt_str:
                return None
            # UTC 시간을 파싱하고 timezone 정보 제거
            dt = datetime.fromisoformat(dt_str.replace('Z', '+00:00'))
            return dt.replace(tzinfo=None)

        self.state = IntervalState(
            last_start_time=parse_datetime(settings.get('last_start_time')),
            last_toggle_time=parse_datetime(settings.get('last_toggle_time'))
        )

    def control(self) -> Optional[BaseMachine]:
        """주기적 제어 실행 (5분마다 호출됨)"""
        if not super().control():
            return None

        if not all([self.duration, self.interval, self.pin]):
            custom_logger.error(f"Device {self.name}: 필수 설정이 누락되었습니다.")
            raise ValueError(f"Device {self.name}: 필수 설정이 누락되었습니다.")

        try:
            now = datetime.now()
            current_status = bool(self.status)
            elapsed_since_start, elapsed_since_toggle = self.state.get_elapsed_times(now)

            # 처음 시작하거나 이전 주기가 완료된 경우
            if not self.state.last_start_time or elapsed_since_start >= self.duration:
                self.state.start_new_cycle(now)
                if not current_status:
                    self.update_device_status(True)
                return self.get_machine()

            # 주기 진행 중
            if elapsed_since_start < self.duration:
                if elapsed_since_toggle >= self.interval:
                    self.state.update_toggle_time(now)
                    self.update_device_status(not current_status)
                return self.get_machine()

            # 주기 종료
            if current_status:
                self.update_device_status(False)
            return self.get_machine()

        except Exception as e:
            custom_logger.error(f"Device {self.name} 제어 중 오류 발생: {str(e)}")
            raise


class TargetAutomation(BaseAutomation):
    def _init_from_settings(self, settings: dict) -> None:
        if settings:
            # 기본값이 있는 설정 초기화
            self.target = float(settings.get('target', 0))  # 목표값을 float으로 변환
            self.margin = float(settings.get('margin', 0))  # 허용 오차를 float으로 변환
            self.sensor_name = None  
            
            custom_logger.info(
                f"Target 자동화 설정 초기화: target={self.target}, "
                f"margin={self.margin}"
            )
        else:
            self.target = None
            self.margin = None
            self.sensor_name = self.name
            custom_logger.warning("Target 자동화 설정이 비어있습니다.")

    def control(self) -> Optional[BaseMachine]:
        """목표값 기반 제어 실행"""
        if not super().control():
            return None

        if not all([self.target is not None, self.margin is not None, self.pin, self.name]):
            custom_logger.error(f"Device {self.name}: 필수 설정이 누락되었습니다.")
            raise ValueError(f"Device {self.name}: 필수 설정이 누락되었습니다.")

        self.sensor_name = self.name

        # Redis에서 현재 센서값 조회
        current_value = self.get_sensor_value(self.sensor_name)
        if current_value is None:
            custom_logger.warning(f"Device {self.name}: Redis에서 센서({self.sensor_name}) 값을 찾을 수 없습니다.")
            return None

        try:
            current_status = bool(self.status)
            value_difference = abs(current_value - self.target)
            
            # 목표값과의 차이가 허용 오차를 벗어난 경우
            if value_difference > self.margin:
                should_be_on = current_value < (self.target - self.margin)
                
                if should_be_on != current_status:
                    self.update_device_status(should_be_on)
                    custom_logger.info(
                        f"Device {self.name}: 센서({self.sensor_name})의 "
                        f"현재값({current_value}) "
                        f"목표값({self.target}) 오차범위({self.target - self.margin} ~ {self.target + self.margin})"
                    )
            
            return self.get_machine()

        except Exception as e:
            custom_logger.error(f"Device {self.name} 제어 중 오류 발생: {str(e)}")
            raise

