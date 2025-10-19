from typing import List, Dict
from logger.custom_logger import custom_logger
from store import Store
from models.automation import create_automation
from managers.thread_manager import ThreadManager
from constants import TREAD_DURATION_LIMIT
from tabulate import tabulate

class AutomationManager:
    def __init__(self, store: Store, thread_manager: ThreadManager):
        self.store = store
        self.thread_manager = thread_manager

    def initialize(self):
        """자동화 초기화"""
        try:
            self._init_store()
            self._start_automation_threads()
            return True
        except Exception as e:
            custom_logger.error(f"초기화 실패: {str(e)}")
            return False

    def _init_store(self):
        """Store 데이터 초기화 로그"""
        store_data = [
            ["Machines", len(self.store.machines)],
            ["Automations", len(self.store.automations)],
            ["Switches", len(self.store.switches)]
        ]
        custom_logger.info("\n=== Store 초기화 완료 ===")
        custom_logger.info("\n" + tabulate(store_data, headers=["Type", "Count"], tablefmt="grid"))

    def _start_automation_threads(self):
        """자동화 스레드 시작"""
        custom_logger.info("\n=== 자동화 스레드 초기화 중 ===")

        automation_table = []

        for automation_data in self.store.automations:
            try:
                automation = create_automation(automation_data)
                machine = next(
                    (m for m in self.store.machines if m.machine_id == automation.device_id),
                    None
                )

                if not machine:
                    custom_logger.error(f"Device ID {automation.device_id}에 해당하는 machine을 찾을 수 없습니다.")
                    continue

                automation.set_machine(machine)

                # Target 자동화인 경우 제어 장치 로드
                if hasattr(automation, '_load_control_devices'):
                    automation._load_control_devices(self.store)

                thread = self.thread_manager.create_automation_thread(automation)
                thread.start()
                self.thread_manager.automation_threads.append(thread)

                # 테이블 데이터 추가
                automation_table.append([
                    machine.name,
                    automation.category,
                    "Active" if automation.active else "Inactive",
                    str(automation.settings)
                ])

            except Exception as e:
                custom_logger.error(f"자동화 스레드 생성 중 오류 발생: {str(e)}")

        if automation_table:
            custom_logger.info("\n" + tabulate(
                automation_table,
                headers=["Device", "Category", "Status", "Settings"],
                tablefmt="grid"
            ))

        custom_logger.info(f"\n✓ 생성된 자동화 스레드 수: {len(self.thread_manager.automation_threads)}")


    def run(self):
        """메인 루프 실행"""
        if not self.thread_manager.automation_threads:
            custom_logger.warning("실행 중인 자동화 스레드가 없습니다.")
            return

        custom_logger.info(f"\n✓ 자동화 스레드 {len(self.thread_manager.automation_threads)}개 시작 완료\n")

        try:
            while not self.thread_manager.stop_event.is_set():
                # 자동화 스레드 모니터링
                self.thread_manager.monitor_threads()
                self.thread_manager.stop_event.wait(TREAD_DURATION_LIMIT)
        except KeyboardInterrupt:
            self.stop()

    def stop(self):
        """자동화 매니저 종료"""
        custom_logger.info("\n자동화 매니저 종료 요청")
        self.thread_manager.stop_automation_threads() 