from typing import List, Optional
from logger.custom_logger import custom_logger
from store import Store
from resources import db, redis
from interfaces.Automation import BaseAutomation
from interfaces.Machine import BaseMachine
# import RPi.GPIO as GPIO
# GPIO 설정
# GPIO.setmode(GPIO.BCM)
# GPIO.setup(self.pin, GPIO.OUT)

def search_by_id(data: List[BaseMachine], id: int) -> Optional[BaseMachine]:
    """ID로 기기 검색"""
    try:
        return next(d for d in data if d.machine_id == id)
    except StopIteration:
        custom_logger.error(f"ID가 {id}인 장치를 찾을 수 없습니다.")
        return None

def process_automations(store: Store) -> None:
    """자동화 처리"""
    for automation_data in store.automations:
        try:
            # Store 인스턴스 전달
            automation = BaseAutomation.create_automation(automation_data, store)
            
            if machine := search_by_id(store.machines, automation.device_id):
                automation.set_machine(machine)

                if automation.control():
                    custom_logger.success(f"자동화 실행 성공: {automation.name}")
                else:
                    custom_logger.error(f"자동화 실행 실패: {automation.name}")
                
        except Exception as e:
            custom_logger.error(f"자동화 처리 중 오류 발생: {str(e)}")

def main():
    try:
        store = Store()
        store.update_machines(store.switches, store.machines)
        process_automations(store)
        
    except Exception as e:
        custom_logger.error(f"메인 프로세스 오류: {str(e)}")
        
    finally:
        db.disconnect()
        redis.disconnect()
        # GPIO.cleanup()

if __name__ == '__main__':
    main()
