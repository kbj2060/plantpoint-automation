"""매 주기마다 DB의 automation 설정과 메모리 상태를 비교하여 동기화하는 매니저."""

import threading
from typing import Dict, Any
from logger.custom_logger import custom_logger
from resources import http
from managers.thread_manager import ThreadManager
from config import settings


class AutomationSyncManager:
    """DB(API)의 automation 설정이 메모리와 다르면 적용하는 매니저. 기본 5분마다 실행."""

    def __init__(self, thread_manager: ThreadManager):
        self.thread_manager = thread_manager
        self._stop_event = threading.Event()

    def run(self) -> None:
        """주기적으로 DB와 automation 설정을 비교하고, 다르면 적용한다."""
        interval = getattr(settings, 'automation_sync_interval', 300)
        custom_logger.info(
            f"AutomationSyncManager: DB 동기화 주기 {interval}초로 시작"
        )
        while not self._stop_event.is_set():
            try:
                self._sync_automations_from_db()
            except Exception as e:
                custom_logger.error(f"Automation DB 동기화 중 오류: {str(e)}", exc_info=True)
            self._stop_event.wait(interval)

    def _sync_automations_from_db(self) -> None:
        """API에서 automation 목록을 가져와 현재 인스턴스와 비교 후, 다르면 적용."""
        if not self.thread_manager.automation_instances:
            return
        try:
            automations_data = http.get_automations()
        except Exception as e:
            custom_logger.warning(f"Automation API 조회 실패 (동기화 스킵): {str(e)}")
            return
        synced_count = 0
        for auto_data in automations_data:
            device_info = auto_data.get('device_id')
            if not device_info:
                continue
            device_name = device_info.get('name') if isinstance(device_info, dict) else None
            if not device_name:
                continue
            automation = self.thread_manager.automation_instances.get(device_name)
            if not automation:
                continue
            api_active = bool(auto_data.get('active', False))
            api_settings = auto_data.get('settings') or {}
            value_for_apply = {'active': auto_data.get('active'), **api_settings}
            if self._is_different(automation, api_active, api_settings):
                try:
                    automation.apply_settings_from_dict(value_for_apply)
                    synced_count += 1
                except Exception as e:
                    custom_logger.error(
                        f"Automation DB 동기화 적용 실패 ({device_name}): {str(e)}"
                    )
        if synced_count > 0:
            custom_logger.info(f"Automation DB 동기화 완료: {synced_count}개 적용")
        else:
            custom_logger.debug("Automation DB 동기화: 변경 사항 없음")

    @staticmethod
    def _is_different(automation, api_active: bool, api_settings: Dict[str, Any]) -> bool:
        """메모리 상태와 API 설정이 다른지 비교한다."""
        if automation.active != api_active:
            return True
        filtered_current = automation.filter_settings_dict(dict(automation._settings))
        filtered_api = automation.filter_settings_dict(dict(api_settings))
        return filtered_current != filtered_api

    def stop(self) -> None:
        """동기화 스레드 종료."""
        self._stop_event.set()
