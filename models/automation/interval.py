from datetime import datetime, timedelta, timezone
from typing import Optional, Tuple, Dict, Callable
from threading import Timer
from models.automation.base import BaseAutomation
from models.Machine import BaseMachine
from models.automation.models import MessageHandler, TimeConfig, MQTTMessage, TopicType, MQTTPayloadData, SwitchMessage
from resources import redis
from constants import TREAD_DURATION_LIMIT

class TimerManager:
    """타이머 관리 클래스"""
    def __init__(self):
        self._on_timer: Optional[Timer] = None
        self._off_timer: Optional[Timer] = None

    def schedule(self, delay: float, callback: Callable, is_on: bool = True) -> None:
        """타이머 예약"""
        timer = self._on_timer if is_on else self._off_timer
        if timer and timer.is_alive():
            return  # 이미 실행 중인 타이머가 있으면 무시

        new_timer = Timer(delay, callback)
        new_timer.daemon = True
        new_timer.start()

        if is_on:
            self._on_timer = new_timer
        else:
            self._off_timer = new_timer

    def cancel_all(self) -> None:
        """모든 타이머 취소"""
        for timer in [self._on_timer, self._off_timer]:
            if timer and timer.is_alive():
                timer.cancel()
        self._on_timer = None
        self._off_timer = None

    def is_active(self, is_on: bool = True) -> bool:
        """타이머 활성화 상태 확인"""
        timer = self._on_timer if is_on else self._off_timer
        return bool(timer and timer.is_alive())

class IntervalState:
    def __init__(self, device_state: Dict = None):
        self.last_toggle_time = None
        self.timers = TimerManager()
        
        if device_state:
            self._init_from_device_state(device_state)

    def _init_from_device_state(self, device_state: Dict) -> None:
        """Redis 상태로부터 초기화"""
        on_state = device_state.get('on_state')
        off_state = device_state.get('off_state')

        if on_state and off_state:
            on_time = self._parse_datetime(on_state['created_at'])
            off_time = self._parse_datetime(off_state['created_at'])
            self.last_toggle_time = max(on_time, off_time)
        elif on_state:
            self.last_toggle_time = self._parse_datetime(on_state['created_at'])
        elif off_state:
            self.last_toggle_time = self._parse_datetime(off_state['created_at'])

    def _parse_datetime(self, date_str: str) -> datetime:
        """UTC 시간 파싱"""
        dt = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
        return dt.astimezone(timezone.utc).replace(tzinfo=None)

    def update_toggle_time(self, current_time: datetime) -> None:
        """토글 시간 업데이트"""
        self.last_toggle_time = current_time

    def reset(self) -> None:
        """상태 초기화"""
        self.timers.cancel_all()
        self.last_toggle_time = None

class IntervalAutomation(BaseAutomation):
    def __init__(self, device_id: str, category: str, active: bool, settings: dict, updated_at: str = None):
        """Interval 자동화 초기화"""
        super().__init__(device_id, category, active, settings, updated_at)

        self.state = IntervalState()  # 상태 초기화

    def _init_from_settings(self, settings: dict) -> None:
        """Interval 자동화 설정 초기화"""
        try:
            duration_settings = settings.get('duration', {})
            interval_settings = settings.get('interval', {})
            
            self.duration = TimeConfig(
                value=duration_settings.get('value', 0),
                unit=duration_settings.get('unit', 's')
            ).to_seconds()
            
            self.interval = TimeConfig(
                value=interval_settings.get('value', 0),
                unit=interval_settings.get('unit', 's')
            ).to_seconds()
            
            self.logger.info(
                f"Interval 자동화 설정 초기화: "
                f"duration={self.duration}s, interval={self.interval}s"
            )
            
        except Exception as e:
            self.logger.error(f"설정 초기화 실패: {str(e)}")
            raise ValueError(f"설정 초기화 실패: {str(e)}")

    def update_settings(self, settings: dict) -> None:
        """설정 업데이트 및 타이머 재시작"""
        self._init_from_settings(settings)
        if self.state:
            self.state.reset()  # 기존 타이머 취소 및 상태 초기화
        self.control()  # 새로운 설정으로 제어 시작

    def control(self) -> Optional[BaseMachine]:
        """주기적 제어 실행"""

        try:
            now = datetime.now()
            current_status = bool(self.status)

            if not self.state or not self.state.last_toggle_time:
                return self._handle_first_run(now)

            self._log_current_state(now, current_status)
            self._handle_timers(current_status)
            return self.get_machine()

        except Exception as e:
            self.logger.error(f"Device {self.name} 제어 중 오류 발생: {str(e)}")
            raise

    def _handle_timers(self, current_status: bool) -> None:
        """타이머 처리"""
        if current_status and not self.state.timers.is_active(is_on=False):
            self._schedule_off_timer()
        elif not current_status and not self.state.timers.is_active(is_on=True):
            self._schedule_on_timer()

    def _schedule_off_timer(self) -> None:
        """OFF 타이머 예약"""
        def off_callback():
            try:
                self.update_device_status(False)
                self.state.update_toggle_time(datetime.now())
                self.logger.info(f"Device {self.name}: duration({self.duration}초) 경과로 OFF")
                self._schedule_on_timer()
            except Exception as e:
                self.logger.error(f"OFF Timer callback 오류: {str(e)}")

        self.state.timers.schedule(self.duration, off_callback, is_on=False)
        self._log_timer_scheduled("OFF", self.duration)

    def _schedule_on_timer(self) -> None:
        """ON 타이머 예약"""
        def on_callback():
            try:
                self.update_device_status(True)
                self.state.update_toggle_time(datetime.now())
                self.logger.info(f"Device {self.name}: interval({self.interval}초) 경과로 ON")
                self._schedule_off_timer()
            except Exception as e:
                self.logger.error(f"ON Timer callback 오류: {str(e)}")

        self.state.timers.schedule(self.interval, on_callback, is_on=True)
        self._log_timer_scheduled("ON", self.interval)

    def _log_current_state(self, now: datetime, current_status: bool) -> None:
        """현재 상태 로깅"""
        self.logger.info(
            f"Device {self.name} 상태 체크: "
            f"현재시간={now.strftime('%H:%M:%S')}, "
            f"마지막토글={self.state.last_toggle_time.strftime('%H:%M:%S')}, "
            f"현재상태={'ON' if current_status else 'OFF'}, "
            f"OFF타이머={'활성' if self.state.timers.is_active(False) else '비활성'}, "
            f"ON타이머={'활성' if self.state.timers.is_active(True) else '비활성'}"
        )

    def _log_timer_scheduled(self, timer_type: str, delay: float) -> None:
        """타이머 예약 로깅"""
        scheduled_time = datetime.now() + timedelta(seconds=delay)
        self.logger.info(
            f"Device {self.name}: {delay}초 후 {timer_type} 예약됨 "
            f"(예정 시각: {scheduled_time.strftime('%H:%M:%S')})"
        )

    def _handle_first_run(self, current_time: datetime) -> BaseMachine:
        """첫 실행 처리 - Redis의 마지막 상태와 경과 시간 기준"""
        try:
            # Redis에서 interval 상태 가져오기
            interval_states = redis.get('interval_automated_switches') or []
            device_state = next(
                (state for state in interval_states if state['name'] == self.name),
                None
            )

            # 상태 초기화
            self.state = IntervalState() if not self.state else self.state

            if device_state:
                # 마지막 ON/OFF 상태 확인
                last_on = device_state.get('on_state', {}).get('created_at')
                last_off = device_state.get('off_state', {}).get('created_at')

                if last_on and last_off:
                    # 시간 파싱 (UTC naive datetime으로 변환)
                    on_time = self.state._parse_datetime(last_on)
                    off_time = self.state._parse_datetime(last_off)
                    
                    # 더 최근 상태와 경과 시간 계산
                    if on_time > off_time:
                        # 마지막 상태가 ON인 경우
                        self.state.update_toggle_time(on_time)
                        # duration 타이머 시작
                        self._schedule_off_timer()
                    else:
                        # 마지막 상태가 OFF인 경우
                        self.state.update_toggle_time(off_time)
                        # interval 타이머 시작
                        self._schedule_on_timer()
                else:
                    # 둘 중 하나만 있는 경우
                    initial_status = bool(last_on)
                    last_time = self.state._parse_datetime(last_on or last_off)
                    self.state.update_toggle_time(last_time)
                    if initial_status:
                        self._schedule_off_timer()
                    else:
                        self._schedule_on_timer()
            else:
                # 상태 기록이 없는 경우 OFF로 시작
                self.update_device_status(False)
                self.state.update_toggle_time(current_time)
                self._schedule_on_timer()

            self.logger.info(
                f"Device {self.name}: 첫 실행 상태 설정 "
                f"({'ON' if self.status else 'OFF'}) "
                f"(Redis 마지막 상태 기준)"
            )
            return self.get_machine()

        except Exception as e:
            self.logger.error(f"첫 실행 상태 설정 실패: {str(e)}")
            # 에러 발생 시 안전하게 OFF로 시작
            self.update_device_status(False)
            self.state.update_toggle_time(current_time)
            self._schedule_on_timer()
            return self.get_machine()

    def __del__(self):
        """객체 소멸 시 정리"""
        if hasattr(self, 'state') and self.state:
            self.state.timers.cancel_all() 