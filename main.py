from typing import List, Optional
from logger.custom_logger import custom_logger
from store import Store
from resources import redis
from interfaces.Automation import BaseAutomation
from interfaces.Machine import BaseMachine
from logger.AutomationLogger import AutomationLogger

# import RPi.GPIO as GPIO
# GPIO.setmode(GPIO.BCM)
# GPIO.setup(self.pin, GPIO.OUT)

def search_by_id(data: List[BaseMachine], id: int) -> Optional[BaseMachine]:
    """ID로 기기 검색"""
    try:
        return next(d for d in data if d.machine_id == id)
    except StopIteration:
        custom_logger.error(f"ID가 {id}인 장치를 찾을 수 없습니다.")
        return None

def process_automations(store: Store) -> List[BaseMachine]:
    """자동화 처리 및 변경된 장치 반환"""
    changed_machines = []
    
    for automation_data in store.automations:
        try:
            automation = BaseAutomation.create_automation(automation_data, store)
            
            if machine := search_by_id(store.machines, automation.device_id):
                automation.set_machine(machine)
                controlled_machine = automation.control()
                
                if controlled_machine:
                    changed_machines.append(controlled_machine)
                    custom_logger.success(f"자동화 실행 성공: {automation.name}")
                else:
                    custom_logger.error(f"자동화 실행 실패: {automation.name}")
                
        except Exception as e:
            custom_logger.error(f"자동화 처리 중 오류 발생: {str(e)}")
    
    return changed_machines

def main():
    store = Store()
    store.update_machines(store.switches, store.machines)
    
    # 자동화 실행 전 상태 저장
    prev_machines = store.switches.copy()
    
    # 자동화 실행 및 변경된 장치 추적
    changed_machines = process_automations(store)
    
    # 변경된 장치들만 로깅
    AutomationLogger(changed_machines, prev_machines).result()
        
    redis.disconnect()
    # GPIO.cleanup()

if __name__ == '__main__':
    main()
