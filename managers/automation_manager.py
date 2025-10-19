from typing import List, Dict
from logger.custom_logger import custom_logger
from store import Store
from models.automation import create_automation
from managers.thread_manager import ThreadManager
from constants import TREAD_DURATION_LIMIT
from tabulate import tabulate
import requests
import os

class AutomationManager:
    def __init__(self, store: Store, thread_manager: ThreadManager):
        self.store = store
        self.thread_manager = thread_manager
        self.backend_url = os.getenv('BACKEND_URL', 'http://backend:3000')

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

    def _check_auto_control_status(self) -> bool:
        """자동 제어 상태 확인 - API를 통해 automation 상태 확인"""
        try:
            response = requests.get(f"{self.backend_url}/automations/status", timeout=5)
            if response.status_code == 200:
                data = response.json()
                return data.get('hasActiveAutomations', False)
            else:
                custom_logger.warning(f"자동화 상태 확인 실패: {response.status_code}")
                return True  # 실패 시 기본값으로 True 반환 (기존 동작 유지)
        except Exception as e:
            custom_logger.error(f"자동화 상태 확인 중 오류: {str(e)}")
            return True  # 실패 시 기본값으로 True 반환 (기존 동작 유지)

    def _pause_automations(self):
        """자동화 일시 정지 - 메모리에서만 비활성화"""
        for automation in self.thread_manager.automation_instances.values():
            if automation.active:
                automation.active = False
                custom_logger.info(f"자동화 일시 정지: {automation.name}")

    def run(self):
        """메인 루프 실행"""
        if not self.thread_manager.automation_threads:
            custom_logger.warning("실행 중인 자동화 스레드가 없습니다.")
            return

        custom_logger.info(f"\n✓ 자동화 스레드 {len(self.thread_manager.automation_threads)}개 시작 완료\n")
        
        try:
            while not self.thread_manager.stop_event.is_set():
                # 자동 제어 상태 확인
                auto_control_enabled = self._check_auto_control_status()
                
                if not auto_control_enabled:
                    # 자동 제어가 비활성화된 경우 자동화 일시 정지
                    self._pause_automations()
                    custom_logger.info("자동 제어가 비활성화되어 자동화를 일시 정지합니다.")
                else:
                    # 자동 제어가 활성화된 경우 자동화 실행
                    self.thread_manager.monitor_threads()
                
                self.thread_manager.stop_event.wait(TREAD_DURATION_LIMIT)
        except KeyboardInterrupt:
            self.stop()

    def stop(self):
        """자동화 매니저 종료"""
        custom_logger.info("\n자동화 매니저 종료 요청")
        self.thread_manager.stop_automation_threads() 