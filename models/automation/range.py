from datetime import datetime, timedelta
from typing import Optional
from models.Machine import BaseMachine
from models.automation.base import BaseAutomation

class RangeAutomation(BaseAutomation):
    def __init__(self, device_id: int, category: str, active: bool, start_time: str, end_time: str, updated_at: str):
        self.settings = { 'start_time': start_time, 'end_time': end_time }
        super().__init__(device_id, category, active, updated_at, self.settings)

    def update_settings(self, settings: dict) -> None:
        """설정 업데이트"""
        self._init_from_settings(settings)
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

            # 자동화가 활성화되어 있을 때만
            if self.name and self.active:  # machine이 설정되고 자동화가 활성화된 경우에만 실행
                now = datetime.now()
                today = now.date()
                
                # 시작/종료 시간 파싱
                try:
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
                        start_time += timedelta(days=1)
                        end_time += timedelta(days=1)
                    
                    # 현재 상태 설정
                    should_be_on = start_time <= now < end_time
                    
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
                # self.logger.debug(f"자동화 비활성화: {self.name}")
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
            
            # 종료 시간이 시작 시간보다 이전인 경우 다음날로 설정 (예: 22:00 ~ 06:00)
            original_end_time = end_time
            if end_time <= start_time:
                end_time += timedelta(days=1)

            # 현재 시간이 제어 주기를 이미 지난 경우(예: 오늘 22:00 ~ 내일 06:00인데 현재는 내일 07:00), 다음 주기로 시간을 조정
            if now > end_time:
                start_time += timedelta(days=1)
                end_time += timedelta(days=1)
            
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
