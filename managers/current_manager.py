from typing import Dict, List
from logger.custom_logger import custom_logger
from models.Current import CurrentThread
from managers.thread_manager import ThreadManager

class CurrentManager:
    def __init__(self, store, thread_manager: ThreadManager):
        self.store = store
        self.thread_manager = thread_manager
        self.current_thread = None

    def initialize(self) -> bool:
        """전류 모니터링 초기화"""
        try:
            custom_logger.info("\n=== 전류 모니터링 초기화 중 ===")
            
            if not self.store.currents:
                custom_logger.warning("모니터링할 전류 설정이 없습니다.")
                return False
                
            self._start_monitoring()
            return True
            
        except Exception as e:
            custom_logger.error(f"전류 모니터링 초기화 실패: {str(e)}")
            return False

    def _start_monitoring(self):
        """전류 모니터링 스레드 시작"""
        try:
            current_thread = CurrentThread(self.store.currents)
            current_thread.start()
            self.thread_manager.current_threads['monitor'] = current_thread
            custom_logger.info("전류 모니터링 스레드 시작")
            
        except Exception as e:
            custom_logger.error(f"전류 모니터링 스레드 시작 실패: {str(e)}")
            raise

    def stop(self):
        """전류 모니터링 종료"""
        custom_logger.info("\n전류 모니터링 매니저 종료 요청")
        self.thread_manager.stop_current_threads()