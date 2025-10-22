from typing import Optional
from logger.custom_logger import custom_logger
from managers.automation_manager import AutomationManager
from managers.nutrient_manager import NutrientManager
from managers.current_monitor_manager import CurrentMonitorManager
from managers.thread_manager import ThreadManager
from managers.resource_manager import ResourceManager
from store import Store


def main() -> None:
    try:
        # 리소스 매니저 초기화
        resource_manager = ResourceManager()
        if not resource_manager.initialize():
            custom_logger.error("리소스 매니저 초기화 실패")
            return
            
        # Store 초기화
        store = Store()
        
        # ThreadManager 초기화
        thread_manager = ThreadManager()
        
        # 자동화 매니저 초기화 및 실행
        automation_manager = AutomationManager(store, thread_manager)
        if not automation_manager.initialize():
            custom_logger.error("자동화 매니저 초기화 실패")
            return

        # NutrientManager 초기화 및 스레드 시작
        nutrient_manager = NutrientManager(store, thread_manager)
        if nutrient_manager.initialize():
            nutrient_manager.start()  # 센서 모니터링 스레드 시작
        else:
            custom_logger.warning("센서 모니터링 초기화 실패")

        # CurrentMonitorManager 초기화 및 스레드 시작
        current_monitor_manager = CurrentMonitorManager(store)
        current_monitor_thread = thread_manager.create_current_monitor_thread(current_monitor_manager)
        thread_manager.current_monitor_threads.append(current_monitor_thread)
        current_monitor_thread.start()
        custom_logger.info("전류 모니터 스레드 시작 완료")

        # 자동화 실행
        automation_manager.run()
    except KeyboardInterrupt:
        custom_logger.info("\n프로그램 종료 요청")
    except Exception as e:
        custom_logger.error(f"프로그램 실행 중 오류 발생: {str(e)}")
    finally:
        # 종료 처리
        if 'automation_manager' in locals():
            automation_manager.stop()
        if 'nutrient_manager' in locals():
            nutrient_manager.stop()
        if 'current_monitor_manager' in locals():
            custom_logger.info("전류 모니터 종료")
        if 'resource_manager' in locals():
            resource_manager.cleanup()

if __name__ == '__main__':
    main()
