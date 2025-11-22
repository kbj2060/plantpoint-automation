from datetime import datetime, timedelta, timezone
from typing import Optional, Dict
from models.automation.base import BaseAutomation
from models.Machine import BaseMachine
from resources import redis
from utils.led_time_utils import load_led_time_range, is_led_on

class IntervalState:
    def __init__(self):
        self.last_toggle_time: Optional[datetime] = None

    def _parse_datetime(self, date_str: str) -> datetime:
        """UTC 시간 파싱"""
        if not date_str:
            return None
        dt = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
        return dt.astimezone(timezone.utc).replace(tzinfo=None)

    def update_toggle_time(self, current_time: datetime) -> None:
        """토글 시간 업데이트"""
        self.last_toggle_time = current_time

    def reset(self) -> None:
        """상태 초기화"""
        self.last_toggle_time = None

class IntervalAutomation(BaseAutomation):
    def __init__(self, device_id: str, category: str, active: bool, duration: str, interval: str, updated_at: str = None):
        self.settings = { 'duration': duration, 'interval': interval }
        super().__init__(device_id, category, active, updated_at, self.settings)
        self.state = IntervalState()
        self.led_time_range = None
        # TimeConfig 변환을 위한 임시 변수
        self._temp_duration_settings = duration
        self._temp_interval_settings = interval

    def _init_from_settings(self, settings: dict) -> None:
        """Interval 자동화 설정 초기화"""
        try:
            # __init__에서 받은 문자열 설정을 TimeConfig로 변환
            from models.automation.models import TimeConfig
            
            duration_settings = settings.get('duration', self._temp_duration_settings)
            interval_settings = settings.get('interval', self._temp_interval_settings)

            self.duration = TimeConfig(
                duration_settings if isinstance(duration_settings, dict) else {'seconds': int(duration_settings)}
            ).to_seconds()

            self.base_interval = TimeConfig(
                interval_settings if isinstance(interval_settings, dict) else {'seconds': int(interval_settings)}
            ).to_seconds()

        except Exception as e:
            self.logger.error(f"설정 초기화 실패: {str(e)}")
            raise ValueError(f"설정 초기화 실패: {str(e)}")

    def _load_control_devices(self, store) -> None:
        """Store에서 LED 시간 범위 설정 로드 (waterspray 전용)"""
        if self.name == 'waterspray':
            self.led_time_range = load_led_time_range(store, self.name)

    def _calculate_effective_interval(self) -> float:
        """LED 상태에 따라 유효 interval 계산 (waterspray 전용)"""
        if self.name != 'waterspray' or not self.led_time_range:
            return self.base_interval

        return self.base_interval * 2 if not is_led_on(self.led_time_range) else self.base_interval

    def update_settings(self, settings: dict) -> None:
        """설정 업데이트"""
        self._init_from_settings(settings)
        self.state.reset()
        self.control()

    def control(self) -> Optional[BaseMachine]:
        """주기적 제어 실행"""
        if not self.active:
            return None

        try:
            now = datetime.now()

            if self.state.last_toggle_time is None:
                return self._handle_first_run(now)

            elapsed_seconds = (now - self.state.last_toggle_time).total_seconds()
            current_status = bool(self.status)

            # 현재 ON 상태일 때
            if current_status:
                if elapsed_seconds >= self.duration:
                    self.logger.info(f"Device {self.name}: duration({self.duration}초) 경과로 OFF")
                    self.update_device_status(False)
                    self.state.update_toggle_time(now)
            # 현재 OFF 상태일 때
            else:
                effective_interval = self._calculate_effective_interval()
                if elapsed_seconds >= effective_interval:
                    led_status = is_led_on(self.led_time_range) if self.led_time_range else None
                    log_msg = f"Device {self.name}: interval({effective_interval}초) 경과로 ON"
                    if self.name == 'waterspray' and led_status is not None:
                        log_msg += f" (LED: {'ON' if led_status else 'OFF'})"
                    self.logger.info(log_msg)
                    
                    self.update_device_status(True)
                    self.state.update_toggle_time(now)

            return self.get_machine()

        except Exception as e:
            self.logger.error(f"Device {self.name} 제어 중 오류 발생: {str(e)}")
            return None

    def _handle_first_run(self, current_time: datetime) -> Optional[BaseMachine]:
        """첫 실행 처리 - Redis의 마지막 상태와 경과 시간 기준"""
        try:
            interval_states = redis.get('interval_automated_switches') or []
            device_state = next((s for s in interval_states if s['name'] == self.name), None)

            if device_state:
                last_time = self.state._parse_datetime(device_state.get('created_at'))
                last_status = bool(device_state.get('status'))
                
                self.state.update_toggle_time(last_time if last_time else current_time)
                # Redis의 상태가 현재 장치 상태와 다를 경우에만 업데이트
                if last_status != self.status:
                    self.update_device_status(last_status)
                
                self.logger.info(
                    f"Device {self.name}: 첫 실행 상태 설정 "
                    f"({'ON' if self.status else 'OFF'}) "
                    f"(Redis 마지막 상태 기준)"
                )
            else:
                # 상태 기록이 없는 경우 OFF로 시작
                self.update_device_status(False)
                self.state.update_toggle_time(current_time)
                self.logger.info(f"Device {self.name}: 첫 실행, 기록 없음. OFF로 시작.")

            return self.get_machine()

        except Exception as e:
            self.logger.error(f"첫 실행 상태 설정 실패: {str(e)}")
            # 에러 발생 시 안전하게 OFF로 시작
            self.update_device_status(False)
            self.state.update_toggle_time(current_time)
            return None

    def __del__(self):
        """객체 소멸 시 정리"""
        pass
