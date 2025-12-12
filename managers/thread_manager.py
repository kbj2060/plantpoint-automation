import threading
import time
from typing import List, Dict
from logger.custom_logger import custom_logger
from models.automation.base import BaseAutomation
from threading import Event
from tabulate import tabulate
from datetime import datetime
from config import settings

class ThreadManager:
    def __init__(self):
        self.nutrient_threads: List[threading.Thread] = []
        self.current_monitor_threads: List[threading.Thread] = []
        self.stop_event = Event()
        self.automation_instances: Dict[str, BaseAutomation] = {}
        self.last_status_report = time.time()

    def register_automation(self, automation: BaseAutomation) -> None:
        """자동화 인스턴스 등록 (모든 automation은 자체 timer thread 사용)"""
        self.automation_instances[automation.name] = automation

    def create_nutrient_thread(self, nutrient_manager) -> threading.Thread:
        """영양소 스레드 생성"""
        def run_nutrient():
            try:
                while not self.stop_event.is_set():
                    nutrient_manager.run()
                    self.stop_event.wait(settings.sensor_read_interval)
            except Exception as e:
                custom_logger.error(f"영양소 스레드 오류 발생: {str(e)}")

        return threading.Thread(
            target=run_nutrient,
            name="NutrientControl",
            daemon=True
        )

    def create_current_monitor_thread(self, current_monitor_manager) -> threading.Thread:
        """전류 모니터 스레드 생성"""
        def run_current_monitor():
            try:
                while not self.stop_event.is_set():
                    current_monitor_manager.run()
                    self.stop_event.wait(settings.current_monitor_interval)
            except Exception as e:
                custom_logger.error(f"전류 모니터 스레드 오류 발생: {str(e)}")

        return threading.Thread(
            target=run_current_monitor,
            name="CurrentMonitor",
            daemon=True
        )

    def monitor_threads(self):
        """스레드 상태 모니터링 및 상태 리포트"""
        # 1분마다 상태 리포트 출력
        current_time = time.time()
        if current_time - self.last_status_report >= 60:  # 1분 = 60초
            self._print_status_report()
            self.last_status_report = current_time

    def _print_status_report(self):
        """자동화 상태 리포트 출력"""
        if not self.automation_instances:
            return

        current_time = datetime.now().strftime("%H:%M:%S")
        status_data = []

        for name, automation in self.automation_instances.items():
            status = "ON" if automation.status else "OFF"
            active_status = "✓" if automation.active else "✗"
            next_change_time = self._get_next_change_time(automation)

            status_data.append([
                name,
                automation.category,
                active_status,
                status,
                next_change_time
            ])

        print(f"\n╔{'═' * 58}╗")
        print(f"║  자동화 상태 리포트 - {current_time}                           ║")
        print(f"╚{'═' * 58}╝\n")
        print(tabulate(
            status_data,
            headers=["Device", "Category", "Active", "Status", "Next Change"],
            tablefmt="grid"
        ))
        print()

    def _get_next_change_time(self, automation) -> str:
        """다음 상태 변경까지 남은 시간 계산"""
        try:
            # interval, range 타입은 _calculate_next_control_time() 메서드 사용
            if automation.category in ["interval", "range"]:
                if hasattr(automation, '_calculate_next_control_time'):
                    next_time = automation._calculate_next_control_time()
                    if next_time:
                        now = datetime.now()
                        remaining_seconds = (next_time - now).total_seconds()
                        if remaining_seconds < 0:
                            return "즉시"
                        elif remaining_seconds >= 60:
                            return f"{int(remaining_seconds / 60)}분"
                        else:
                            return f"{int(remaining_seconds)}초"

            # target 타입 - 센서값 기반이므로 예측 불가
            elif automation.category == "target":
                return "센서 기반"

            return "-"

        except Exception as e:
            return "-"

    def stop_automation_threads(self):
        """자동화 스레드만 종료"""
        # 모든 automation의 timer thread 종료
        for automation in self.automation_instances.values():
            if hasattr(automation, 'stop_timer_thread'):
                automation.stop_timer_thread()

    def stop_nutrient_threads(self):
        """영양소 스레드만 종료"""
        for thread in self.nutrient_threads:
            if thread.is_alive():
                thread.join()
        self.nutrient_threads.clear()

    def stop_current_monitor_threads(self):
        """전류 모니터 스레드만 종료"""
        for thread in self.current_monitor_threads:
            if thread.is_alive():
                thread.join()
        self.current_monitor_threads.clear()

    def stop_all(self):
        """모든 스레드 종료"""
        self.stop_event.set()
        self.stop_automation_threads()
        self.stop_nutrient_threads()
        self.stop_current_monitor_threads() 
