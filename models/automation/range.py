from datetime import datetime, timedelta
from threading import Timer
from typing import Optional
from models.Machine import BaseMachine
from models.automation.base import BaseAutomation

class RangeTimerManager:
    """Range 타이머 관리 클래스"""
    def __init__(self):
        self._start_timer: Optional[Timer] = None
        self._end_timer: Optional[Timer] = None
        self._start_scheduled_time: Optional[datetime] = None
        self._end_scheduled_time: Optional[datetime] = None

    def schedule_start(self, delay: float, callback) -> None:
        """시작 타이머 예약"""
        if self._start_timer and self._start_timer.is_alive():
            self._start_timer.cancel()

        self._start_timer = Timer(delay, callback)
        self._start_timer.daemon = True
        self._start_timer.start()
        self._start_scheduled_time = datetime.now() + timedelta(seconds=delay)

    def schedule_end(self, delay: float, callback) -> None:
        """종료 타이머 예약"""
        if self._end_timer and self._end_timer.is_alive():
            self._end_timer.cancel()

        self._end_timer = Timer(delay, callback)
        self._end_timer.daemon = True
        self._end_timer.start()
        self._end_scheduled_time = datetime.now() + timedelta(seconds=delay)

    def cancel_all(self) -> None:
        """모든 타이머 취소"""
        for timer in [self._start_timer, self._end_timer]:
            if timer and timer.is_alive():
                timer.cancel()
        self._start_timer = None
        self._end_timer = None
        self._start_scheduled_time = None
        self._end_scheduled_time = None

    def get_scheduled_time(self, is_on: bool = True) -> Optional[datetime]:
        """예약된 시간 반환 (is_on=True: 시작 타이머, False: 종료 타이머)"""
        timer = self._start_timer if is_on else self._end_timer
        scheduled_time = self._start_scheduled_time if is_on else self._end_scheduled_time

        if timer and timer.is_alive() and scheduled_time:
            return scheduled_time
        return None

class RangeAutomation(BaseAutomation):
    def __init__(self, device_id: int, category: str, active: bool, start_time: str, end_time: str, updated_at: str):
        self.settings = { 'start_time': start_time, 'end_time': end_time }
        super().__init__(device_id, category, active, updated_at, self.settings)

        self.timers = RangeTimerManager()

    def update_settings(self, settings: dict) -> None:
        """설정 업데이트 및 타이머 재시작"""
        self._init_from_settings(settings)
        if self.timers:
            self.timers.cancel_all()  # 기존 타이머 취소
        self.control()  # 새로운 설정으로 제어 시작

    def _init_from_settings(self, settings: dict) -> None:
        """Range 설정 초기화"""
        try:
            self.start_time = settings.get('start_time', '00:00')
            self.end_time = settings.get('end_time', '00:00')

            # self.logger.info(
            #     f"Range 자동화 설정 초기화: "
            #     f"시작={self.start_time}, 종료={self.end_time}"
            # )

            # 타이머 초기 설정
            if self.name:  # machine이 설정된 후에만 실행
                now = datetime.now()
                today = now.date()
                
                # 시작/종료 시간 파싱
                try:
                    start_hour, start_minute = map(int, self.start_time.split(':'))
                    end_hour, end_minute = map(int, self.end_time.split(':'))
                    
                    # self.logger.debug(
                    #     f"시간 파싱 결과: "
                    #     f"시작={start_hour}:{start_minute}, "
                    #     f"종료={end_hour}:{end_minute}"
                    # )
                    
                    start_time = datetime.combine(today, datetime.min.time().replace(
                        hour=start_hour, minute=start_minute
                    ))
                    end_time = datetime.combine(today, datetime.min.time().replace(
                        hour=end_hour, minute=end_minute
                    ))
                    
                    # self.logger.debug(
                    #     f"datetime 변환 결과: "
                    #     f"시작={start_time.strftime('%Y-%m-%d %H:%M:%S')}, "
                    #     f"종료={end_time.strftime('%Y-%m-%d %H:%M:%S')}"
                    # )
                    
                    # 종료 시간이 시작 시간보다 이전인 경우 다음날로 설정
                    if end_time <= start_time:
                        end_time += timedelta(days=1)
                        # self.logger.debug(f"종료 시간을 다음날로 조정: {end_time.strftime('%Y-%m-%d %H:%M:%S')}")
                    
                    # 현재 시간이 범위를 벗어난 경우 다음 주기로 설정
                    if now > end_time:
                        start_time += timedelta(days=1)
                        end_time += timedelta(days=1)
                        # self.logger.debug(
                        #     f"다음 주기로 조정: "
                        #     f"시작={start_time.strftime('%Y-%m-%d %H:%M:%S')}, "
                        #     f"종료={end_time.strftime('%Y-%m-%d %H:%M:%S')}"
                        # )
                    
                    # 타이머 설정
                    self._schedule_timers(now, start_time, end_time)
                    
                    # 현재 상태 설정
                    should_be_on = start_time <= now < end_time
                    # self.logger.debug(
                    #     f"상태 계산: now={now.strftime('%Y-%m-%d %H:%M:%S')}, "
                    #     f"should_be_on={should_be_on}"
                    # )
                    
                    if should_be_on != self.status:
                        self.update_device_status(should_be_on)
                        
                except ValueError as e:
                    self.logger.error(f"시간 파싱 실패: {str(e)}")
                    raise
            
        except Exception as e:
            self.logger.error(f"설정 초기화 실패: {str(e)}")
            raise

    def control(self) -> Optional[BaseMachine]:
        """Range 제어 실행"""
        try:
            if not self.active:
                self.logger.debug(f"자동화 비활성화: {self.name}")
                return None

            now = datetime.now()
            today = now.date()
            
            # 시작/종료 시간 파싱
            start_hour, start_minute = map(int, self.start_time.split(':'))
            end_hour, end_minute = map(int, self.end_time.split(':'))
            
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
            if now > end_time:
                # 상태가 켜져있으면 끄기
                if self.status:
                    self.logger.info(f"시간 범위 종료로 {self.name} 끄기")
                    self.update_device_status(False)
                start_time += timedelta(days=1)
                end_time += timedelta(days=1)
            elif now < start_time and self.status:
                # 시작 시간 이전인데 켜져있으면 끄기
                self.logger.info(f"시작 시간 이전이므로 {self.name} 끄기")
                self.update_device_status(False)
            
            # 타이머 설정
            self._schedule_timers(now, start_time, end_time)
            
            # 현재 상태 확인 및 업데이트
            should_be_on = start_time <= now < end_time
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

    def _schedule_timers(self, now: datetime, start_time: datetime, end_time: datetime):

        #TODO 시작 종료 타이머 제대로 설정이 되지 않음. MQTT 에서 받은 automation 설정 확인 필요
        """시작/종료 타이머 예약"""
        # 시작 타이머
        start_delay = (start_time - now).total_seconds()
        if start_delay > 0:
            self.timers.schedule_start(start_delay, lambda: self._handle_timer_event(True))
            # self.logger.info(
            #     f"시작 타이머 예약: {start_time.strftime('%Y-%m-%d %H:%M:%S')} "
            #     f"({start_delay:.0f}초 후)"
            # )
            
        # 종료 타이머
        end_delay = (end_time - now).total_seconds()
        if end_delay > 0:
            self.timers.schedule_end(end_delay, lambda: self._handle_timer_event(False))
            # self.logger.info(
            #     f"종료 타이머 예약: {end_time.strftime('%Y-%m-%d %H:%M:%S')} "
            #     f"({end_delay:.0f}초 후)"
            # )

    def _handle_timer_event(self, turn_on: bool):
        """타이머 이벤트 처리"""
        try:
            # 자동화가 비활성화되어 있으면 타이머 이벤트 무시
            if not self.active:
                self.logger.debug(f"자동화 비활성화 상태 - 타이머 이벤트 무시: {self.name}")
                return

            self.update_device_status(turn_on)
            self.logger.info(
                f"Range 타이머 실행: {self.name} "
                f"({'ON' if turn_on else 'OFF'})"
            )

            # 다음 주기 타이머 설정
            if not turn_on:  # 종료 타이머 실행 후
                now = datetime.now()
                today = now.date()
                
                start_hour, start_minute = map(int, self.start_time.split(':'))
                end_hour, end_minute = map(int, self.end_time.split(':'))
                
                next_start = datetime.combine(today + timedelta(days=1),
                    datetime.min.time().replace(hour=start_hour, minute=start_minute)
                )
                next_end = datetime.combine(today + timedelta(days=1),
                    datetime.min.time().replace(hour=end_hour, minute=end_minute)
                )
                
                if next_end <= next_start:
                    next_end += timedelta(days=1)
                    
                self._schedule_timers(now, next_start, next_end)
                
        except Exception as e:
            self.logger.error(f"타이머 이벤트 처리 실패: {str(e)}")

    def __del__(self):
        """객체 소멸 시 정리"""
        if hasattr(self, 'timers'):
            self.timers.cancel_all() 
