from pprint import pprint
from logger.custom_logger import custom_logger
from managers.automation_manager import AutomationManager
from managers.current_manager import CurrentManager
from managers.thread_manager import ThreadManager
from managers.resource_manager import ResourceManager
from store import Store

def main():
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
            
        # 전류 모니터링 매니저 초기화 및 실행
        current_manager = CurrentManager(store, thread_manager)
        if not current_manager.initialize():
            custom_logger.warning("전류 모니터링 초기화 실패")
            
        # 자동화 실행
        automation_manager.run()
        
    except KeyboardInterrupt:
        custom_logger.info("\n프로그램 종료 요청")
    except Exception as e:
        custom_logger.error(f"프로그램 실행 중 오류 발생: {str(e)}")
    finally:
        # 종료 처리
        if 'current_manager' in locals():
            current_manager.stop()
        if 'automation_manager' in locals():
            automation_manager.stop()
        if 'resource_manager' in locals():
            resource_manager.cleanup()

if __name__ == '__main__':
    main()
