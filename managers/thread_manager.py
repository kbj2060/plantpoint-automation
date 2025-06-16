import threading
from typing import List, Dict
from logger.custom_logger import custom_logger
from models.automation.base import BaseAutomation
from models.Current import CurrentThread
from threading import Event

class ThreadManager:
    def __init__(self):
        self.automation_threads: List[threading.Thread] = []
        self.nutrient_threads: List[threading.Thread] = []
        self.current_threads: Dict[str, CurrentThread] = {}
        self.stop_event = Event()

    def create_automation_thread(self, automation: BaseAutomation) -> threading.Thread:
        """자동화 스레드 생성"""
        def run_automation():
            try:
                while not self.stop_event.is_set():
                    controlled_machine = automation.control()
                    if controlled_machine:
                        custom_logger.info(f"자동화 실행 성공: {automation.name}")
                    else:
                        custom_logger.debug(f"자동화 대기 중: {automation.name}")
                    self.stop_event.wait(60)
            except Exception as e:
                custom_logger.error(f"자동화 스레드 오류 발생: {str(e)}")

        return threading.Thread(
            target=run_automation,
            name=f"Automation-{automation.name}",
            daemon=True
        )

    def create_nutrient_thread(self, nutrient_manager) -> threading.Thread:
        """영양소 스레드 생성"""
        def run_nutrient():
            try:
                while not self.stop_event.is_set():
                    nutrient_manager.adjust_nutrients()
                    self.stop_event.wait(60)
            except Exception as e:
                custom_logger.error(f"영양소 스레드 오류 발생: {str(e)}")

        return threading.Thread(
            target=run_nutrient,
            name="NutrientControl",
            daemon=True
        )

    def monitor_threads(self):
        """스레드 상태 모니터링"""
        active_threads = [t for t in self.automation_threads if t.is_alive()]
        terminated = len(self.automation_threads) - len(active_threads)
        
        if terminated > 0:
            custom_logger.warning(f"{terminated}개의 자동화 스레드가 종료됨")
        
        self.automation_threads = active_threads

    def stop_automation_threads(self):
        """자동화 스레드만 종료"""
        self.stop_event.set()
        for thread in self.automation_threads:
            if thread.is_alive():
                thread.join()
        self.automation_threads.clear()

    def stop_nutrient_threads(self):
        """영양소 스레드만 종료"""
        self.stop_event.set()
        for thread in self.nutrient_threads:
            if thread.is_alive():
                thread.join()
        self.nutrient_threads.clear()

    def stop_current_threads(self):
        """전류 모니터링 스레드만 종료"""
        self.stop_event.set()
        for thread in self.current_threads.values():
            if thread.is_alive():
                thread.join()
        self.current_threads.clear()

    def stop_all(self):
        """모든 스레드 종료"""
        self.stop_event.set()
        self.stop_automation_threads()
        self.stop_current_threads()
        self.stop_nutrient_threads() 