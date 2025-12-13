from datetime import datetime, timedelta
from typing import Optional
import threading
from models.Machine import BaseMachine
from models.automation.base import BaseAutomation
from models.automation.models import MQTTMessage

class RangeAutomation(BaseAutomation):
    def __init__(self, device_id: int, category: str, active: bool, start_time: str, end_time: str, updated_at: str):
        self.settings = { 'start_time': start_time, 'end_time': end_time }
        super().__init__(device_id, category, active, updated_at, self.settings)

    def update_settings(self, settings: dict) -> None:
        """설정 업데이트"""
        self._init_from_settings(settings)
        # Timer thread가 자동으로 제어하므로 여기서는 control() 호출하지 않음

    def _parse_time_string(self, time_str: str) -> tuple[int, int]:
        """시간 문자열 파싱 (HH:MM 형식)"""
        try:
            hour, minute = map(int, time_str.split(':'))
            return hour, minute
        except ValueError as e:
            self.logger.error(f"시간 파싱 실패: {time_str}, 오류: {str(e)}")
            raise

    def _calculate_time_range(self, reference_time: Optional[datetime] = None) -> tuple[datetime, datetime]:
        """
        시작/종료 시간 범위 계산
        
        Args:
            reference_time: 기준 시간 (None이면 현재 시간 사용)
            
        Returns:
            (start_time, end_time) 튜플
        """
        if reference_time is None:
            reference_time = datetime.now()
        
        today = reference_time.date()
        
        # 시작/종료 시간 파싱
        start_hour, start_minute = self._parse_time_string(self.start_time)
        end_hour, end_minute = self._parse_time_string(self.end_time)
        
        start_time = datetime.combine(today, datetime.min.time().replace(
            hour=start_hour, minute=start_minute
        ))
        end_time = datetime.combine(today, datetime.min.time().replace(
            hour=end_hour, minute=end_minute
        ))
        
        # 종료 시간이 시작 시간보다 이전인 경우 다음날로 설정
        if end_time <= start_time:
            end_time += timedelta(days=1)
        
        # 현재 시간이 범위를 벗어난 경우 다음 주기로 설정
        if reference_time > end_time:
            start_time += timedelta(days=1)
            end_time += timedelta(days=1)
        
        return start_time, end_time

    def _should_be_on(self, reference_time: Optional[datetime] = None) -> bool:
        """현재 시간 기준으로 ON 상태여야 하는지 확인"""
        if reference_time is None:
            reference_time = datetime.now()
        start_time, end_time = self._calculate_time_range(reference_time)
        return start_time <= reference_time < end_time

    def _init_from_settings(self, settings: dict) -> None:
        """Range 설정 초기화"""
        try:
            self.start_time = settings.get('start_time', '00:00')
            self.end_time = settings.get('end_time', '00:00')

            # 자동화가 활성화되어 있을 때만
            if self.name and self.active:  # machine이 설정되고 자동화가 활성화된 경우에만 실행
                should_be_on = self._should_be_on()
                
                if should_be_on != self.status:
                    self.update_device_status(should_be_on)
            
        except Exception as e:
            self.logger.error(f"설정 초기화 실패: {str(e)}")
            raise

    def _handle_switch_message(self, mqtt_message: MQTTMessage) -> None:
        """스위치 상태 메시지 처리 (Range 전용 - 스케줄 확인)"""
        super()._handle_switch_message(mqtt_message)
        # 수동 제어 후 스케줄 상태 확인 (즉시 스케줄 적용)
        self.control()

    def control(self) -> Optional[BaseMachine]:
        """Range 제어 실행"""
        try:
            if not self.active:
                # self.logger.debug(f"자동화 비활성화: {self.name}")
                return None

            should_be_on = self._should_be_on()
            
            if should_be_on != self.status:
                self.update_device_status(should_be_on)
                return self.get_machine()
                
            return None
            
        except Exception as e:
            self.logger.error(f"Range 제어 실패: {str(e)}")
            # 에러 발생 시 안전하게 OFF
            if self.status:
                self.logger.info(f"에러 발생으로 {self.name} 안전하게 끄기")
                self.update_device_status(False)
            return None

    def _calculate_next_control_time(self) -> Optional[datetime]:
        """다음 제어 시간 계산"""
        try:
            if not self.active or not self.name:
                return None

            now = datetime.now()
            start_time, end_time = self._calculate_time_range(now)
            should_be_on = self._should_be_on(now)
            
            # 다음 제어 시간 결정
            if should_be_on:
                # 현재 ON 상태이면 종료 시간에 OFF
                return end_time
            else:
                # 현재 OFF 상태이면 시작 시간에 ON
                if now < start_time:
                    return start_time
                else:
                    # 이미 종료 시간을 지났으므로 다음 시작 시간
                    return start_time + timedelta(days=1)
                    
        except Exception as e:
            self.logger.error(f"다음 제어 시간 계산 실패: {str(e)}")
            return None

    def start_timer_thread(self) -> None:
        """Timer thread 시작"""
        if not self.name:
            return
            
        # 기존 thread가 있으면 종료
        self.stop_timer_thread()
        
        # Stop event 생성
        self.timer_stop_event = threading.Event()
        
        def timer_loop():
            """Timer thread 루프"""
            try:
                while not self.timer_stop_event.is_set():
                    if not self.active:
                        # 비활성화 상태면 1분마다 체크
                        self.timer_stop_event.wait(60)
                        continue
                    
                    # 다음 제어 시간 계산
                    next_time = self._calculate_next_control_time()
                    if not next_time:
                        self.timer_stop_event.wait(60)
                        continue
                    
                    now = datetime.now()
                    wait_seconds = (next_time - now).total_seconds()
                    
                    if wait_seconds <= 0:
                        # 이미 시간이 지났으면 즉시 제어
                        self.control()
                        continue
                    
                    # 최대 1초 단위로 체크 (정확도 향상)
                    check_interval = min(wait_seconds, 1.0)
                    
                    # 다음 제어 시간까지 대기
                    if self.timer_stop_event.wait(check_interval):
                        # Stop event가 설정되었으면 종료
                        break
                    
                    # 제어 시간이 되었는지 확인
                    now = datetime.now()
                    if now >= next_time:
                        self.control()
                        
            except Exception as e:
                self.logger.error(f"Timer thread 오류: {str(e)}")
        
        self.timer_thread = threading.Thread(
            target=timer_loop,
            name=f"RangeTimer-{self.name}",
            daemon=True
        )
        self.timer_thread.start()
        self.logger.info(f"Range timer thread 시작: {self.name}")
