import threading
import time
from typing import List, Dict
from logger.custom_logger import custom_logger
from models.automation.base import BaseAutomation
from threading import Event
from tabulate import tabulate
from datetime import datetime

class ThreadManager:
    def __init__(self):
        self.automation_threads: List[threading.Thread] = []
        self.nutrient_threads: List[threading.Thread] = []
        self.stop_event = Event()
        self.automation_instances: Dict[str, BaseAutomation] = {}
        self.last_status_report = time.time()

    def create_automation_thread(self, automation: BaseAutomation) -> threading.Thread:
        """자동화 스레드 생성"""
        # 자동화 인스턴스 저장
        self.automation_instances[automation.name] = automation

        def run_automation():
            try:
                while not self.stop_event.is_set():
                    automation.control()
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
        """스레드 상태 모니터링 및 상태 리포트"""
        # 죽은 스레드 확인
        active_threads = [t for t in self.automation_threads if t.is_alive()]
        terminated = len(self.automation_threads) - len(active_threads)

        if terminated > 0:
            custom_logger.warning(f"{terminated}개의 자동화 스레드가 종료됨")

        self.automation_threads = active_threads

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

            # 남은 시간 계산
            next_change_time = self._get_next_change_time(automation)

            status_data.append([
                name,
                automation.category,
                active_status,
                status,
                next_change_time
            ])

        header = f"자동화 상태 리포트 - {current_time}"
        border_length = len(header) + 4

        custom_logger.info(f"\n╔{'═' * border_length}╗")
        custom_logger.info(f"║  {header}  ║")
        custom_logger.info(f"╚{'═' * border_length}╝\n")
        custom_logger.info(tabulate(
            status_data,
            headers=["Device", "Category", "Active", "Status", "Next Change"],
            tablefmt="grid"
        ) + "\n")

    def _get_next_change_time(self, automation) -> str:
        """다음 상태 변경까지 남은 시간 계산"""
        try:
            # interval 타입 - 타이머 확인
            if automation.category == "interval" and hasattr(automation, 'state') and automation.state:
                if hasattr(automation.state, 'timers'):
                    now = datetime.now()

                    # 현재 상태에 따라 다음 타이머 확인
                    # ON 상태면 OFF 타이머, OFF 상태면 ON 타이머
                    is_on = bool(automation.status)
                    scheduled_time = automation.state.timers.get_scheduled_time(is_on=not is_on)

                    if scheduled_time and scheduled_time > now:
                        remaining_seconds = (scheduled_time - now).total_seconds()
                        if remaining_seconds >= 60:
                            return f"{int(remaining_seconds / 60)}분"
                        else:
                            return f"{int(remaining_seconds)}초"

            # range 타입 - 시작/종료 타이머 확인
            elif automation.category == "range" and hasattr(automation, 'timers'):
                now = datetime.now()

                # 시작/종료 타이머 확인
                for is_on in [True, False]:
                    scheduled_time = automation.timers.get_scheduled_time(is_on=is_on)
                    if scheduled_time and scheduled_time > now:
                        remaining_seconds = (scheduled_time - now).total_seconds()
                        if remaining_seconds >= 60:
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

    def stop_all(self):
        """모든 스레드 종료"""
        self.stop_event.set()
        self.stop_automation_threads()
        self.stop_nutrient_threads() 