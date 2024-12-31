import threading
from typing import List, Optional
from logger.custom_logger import custom_logger
from store import Store
from resources import redis, mqtt
from interfaces.Machine import BaseMachine
from interfaces.automation import create_automation
from interfaces.automation.base import BaseAutomation
from constants import TREAD_DURATION_LIMIT


def create_automation_thread(automation: BaseAutomation) -> threading.Thread:
    """자동화 스레드 생성 (백업용 체크)"""
    def run_automation():
        try:
            while True:
                controlled_machine = automation.control()
                if controlled_machine:
                    custom_logger.info(f"자동화 실행 성공: {automation.name}")
                else:
                    custom_logger.debug(f"자동화 대기 중: {automation.name}")
                threading.Event().wait(60)  # 1분마다 백업 체크
        except Exception as e:
            custom_logger.error(f"자동화 스레드 오류 발생: {str(e)}")

    thread = threading.Thread(
        target=run_automation,
        name=f"Automation-{automation.name}",
        daemon=True
    )
    return thread

def start_automation_threads(store: Store) -> List[threading.Thread]:
    """모든 자동화 스레드 시작"""
    threads = []
    
    custom_logger.info(f"자동화 설정 개수: {len(store.automations)}")
    
    if not store.automations:
        custom_logger.warning("자동화 설정이 없습니다.")
        return threads
    
    for automation_data in store.automations:
        try:
            custom_logger.info(f"자동화 설정 처리 중:")
            
            # 자동화 객체 생성
            automation = create_automation(automation_data)
            
            # 해당하는 machine 찾기 (객체 속성으로 접근)
            machine = next(
                (m for m in store.machines if m.machine_id == automation.device_id), 
                None
            )
            
            if machine:
                custom_logger.info(f"{machine.name} / {automation_data['category']} /{automation_data['settings']}")
                
                # machine 정보 설정 (이때 MQTT 구독도 설정됨)
                automation.set_machine(machine)
                
                # 스레드 생성 및 시작
                thread = create_automation_thread(automation)
                thread.start()
                threads.append(thread)
                
                custom_logger.info(
                    f"자동화 스레드 시작: {automation.name} "
                    f"(category: {automation.category})"
                )
            else:
                custom_logger.error(
                    f"Device ID {automation.device_id}에 해당하는 "
                    f"machine을 찾을 수 없습니다."
                )
                
        except Exception as e:
            custom_logger.error(f"자동화 스레드 생성 중 오류 발생: {str(e)}")
            custom_logger.exception(e)  # 상세 오류 로깅
    
    custom_logger.info(f"생성된 자동화 스레드 수: {len(threads)}")
    return threads

def main():
    try:        
        # 2. 리소스 초기화 (순서 중요)
        custom_logger.info("리소스 초기화 중...")
        
        # MQTT 초기화
        mqtt.client.loop_start()
        custom_logger.info("MQTT 브로커 연결 완료")
        
        # Redis 초기화
        custom_logger.info("Redis 연결 완료")
        
        # 3. Store 초기화
        store = Store()
        custom_logger.info("=== Store 초기화 완료 ===")
        custom_logger.info(f"- Machines: {len(store.machines)}")
        custom_logger.info(f"- Automations: {len(store.automations)}")
        custom_logger.info(f"- Switches: {len(store.switches)}")
        
        # 4. 자동화 스레드 시작
        custom_logger.info("\n=== 자동화 스레드 초기화 중 ===")
        threads = start_automation_threads(store)
        
        if not threads:
            custom_logger.warning("실행 중인 자동화 스레드가 없습니다.")
            return
            
        custom_logger.info(f"자동화 스레드 {len(threads)}개 시작 완료")
        
        # 5. 메인 루프
        previous_threads = set(threads)
        try:
            while True:
                active_threads = set(t for t in threads if t.is_alive())
                terminated_threads = previous_threads - active_threads
                
                if terminated_threads:
                    for thread in terminated_threads:
                        custom_logger.warning(f"자동화 스레드 종료: {thread.name}")
                
                previous_threads = active_threads
                threading.Event().wait(TREAD_DURATION_LIMIT)
                
        except KeyboardInterrupt:
            custom_logger.info("\n프로그램 종료 요청")
        finally:
            redis.disconnect()
            mqtt.disconnect()
            
    except Exception as e:
        custom_logger.error(f"메인 프로세스 오류: {str(e)}")

if __name__ == '__main__':
    main()
