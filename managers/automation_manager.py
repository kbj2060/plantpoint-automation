from typing import List, Dict
from logger.custom_logger import custom_logger
from store import Store
from models.automation import create_automation
from managers.thread_manager import ThreadManager
from constants import TREAD_DURATION_LIMIT
from tabulate import tabulate
from resources import mqtt, http
from models.automation.models import MQTTMessage, MQTTPayloadData, SwitchMessage, TopicType

class AutomationManager:
    def __init__(self, store: Store, thread_manager: ThreadManager):
        self.store = store
        self.thread_manager = thread_manager

    def initialize(self):
        """자동화 초기화"""
        try:
            self._init_store()
            self._start_automation_threads()
            self._setup_mqtt_subscription()
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
        """자동화 인스턴스 생성 및 등록 (각 automation은 자체 timer thread 사용)"""
        custom_logger.info("\n=== 자동화 초기화 중 ===")

        automation_table = []

        for automation_data in self.store.automations:
            try:
                automation = create_automation(automation_data)
                
                # Machine 검색 (BaseMachine 객체는 machine_id 사용)
                device = next(
                    (m for m in self.store.machines if m.machine_id == automation.device_id),
                    None
                )

                if device:
                    automation.set_machine(device)
                else:
                    # Sensor 검색 (Sensor는 딕셔너리 형태이므로 id 사용)
                    device = next(
                        (s for s in self.store.sensors if s.get('id') == automation.device_id),
                        None
                    )
                    if device:
                        automation.set_sensor(device)

                if not device:
                    custom_logger.error(f"Device ID {automation.device_id}에 해당하는 Machine 또는 Sensor를 찾을 수 없습니다.")
                    continue

                # Target 자동화인 경우 제어 장치 로드
                if hasattr(automation, '_load_control_devices'):
                    automation._load_control_devices(self.store)

                # 자동화 인스턴스 등록 (자체 timer thread는 set_machine()에서 자동 시작)
                self.thread_manager.register_automation(automation)

                # 테이블 데이터 추가
                device_name = device.name if hasattr(device, 'name') else device.get('name')
                automation_table.append([
                    device_name,
                    automation.category,
                    "Active" if automation.active else "Inactive",
                    str(automation.settings)
                ])

            except Exception as e:
                custom_logger.error(f"자동화 초기화 중 오류 발생: {str(e)}")

        if automation_table:
            custom_logger.info("\n" + tabulate(
                automation_table,
                headers=["Device", "Category", "Status", "Settings"],
                tablefmt="grid"
            ))

        custom_logger.info(f"\n✓ 등록된 자동화 수: {len(self.thread_manager.automation_instances)}")

    def _setup_mqtt_subscription(self):
        """MQTT 구독 설정 - 새로운 automation 추가 감지"""
        try:
            # automation/# 토픽 구독하여 새로운 automation 추가 감지
            mqtt.client.message_callback_add("automation/+", self._on_automation_message)
            custom_logger.info("AutomationManager: MQTT 구독 설정 완료 (automation/+)")
        except Exception as e:
            custom_logger.error(f"MQTT 구독 설정 실패: {str(e)}")

    def _on_automation_message(self, client, userdata, message):
        """새로운 automation 메시지 처리"""
        try:
            mqtt_message = MQTTMessage.from_message(message)
            device_name = mqtt_message.topic_parts[1]  # automation/{name}에서 name 추출
            
            # 이미 등록된 automation인지 확인
            if device_name in self.thread_manager.automation_instances:
                # 이미 존재하면 기존 인스턴스가 처리하도록 함
                return
            
            # 새로운 automation이면 HTTP API에서 최신 데이터 가져와서 생성
            custom_logger.info(f"새로운 automation 감지: {device_name}, 최신 데이터 가져오는 중...")
            self._create_automation_from_api(device_name)
            
        except Exception as e:
            custom_logger.error(f"새로운 automation 처리 실패: {str(e)}")

    def _create_automation_from_api(self, device_name: str):
        """HTTP API에서 automation 데이터를 가져와서 인스턴스 생성"""
        try:
            # 최신 automation 데이터 가져오기
            automations_data = http.get_automations()
            machines_data = http.get_machines()
            
            # 해당 device_name에 해당하는 automation 찾기
            automation_data = None
            for auto_data in automations_data:
                device_info = auto_data.get('device_id')
                if device_info and device_info.get('name') == device_name:
                    automation_data = auto_data
                    break
            
            if not automation_data:
                custom_logger.warning(f"새로운 automation 데이터를 찾을 수 없습니다: {device_name}")
                return
            
            # Machine 정보 찾기
            device_info = automation_data.get('device_id', {})
            device_id = device_info.get('id') if isinstance(device_info, dict) else device_info
            machine_data = next(
                (m for m in machines_data if m.get('id') == device_id),
                None
            )
            
            if not machine_data:
                custom_logger.error(f"Device ID {device_id}에 해당하는 machine을 찾을 수 없습니다.")
                return
            
            # Automation 인스턴스 생성
            automation = create_automation(automation_data)
            
            # Machine 정보 설정
            from models.Machine import BaseMachine
            machine = BaseMachine(
                machine_id=machine_data.get('id'),
                name=machine_data.get('name'),
                pin=machine_data.get('pin'),
                status=machine_data.get('status', False),
                switch_created_at=machine_data.get('switch_created_at')
            )
            
            automation.set_machine(machine)
            
            # Target 자동화인 경우 제어 장치 로드
            if hasattr(automation, '_load_control_devices'):
                automation._load_control_devices(self.store)
            
            # 자동화 인스턴스 등록
            self.thread_manager.register_automation(automation)
            
            custom_logger.info(
                f"새로운 automation 등록 완료: {device_name} "
                f"(카테고리: {automation.category}, 활성화: {automation.active})"
            )
            
        except Exception as e:
            custom_logger.error(f"API에서 automation 생성 실패: {str(e)}")

    def run(self):
        """메인 루프 실행"""
        if not self.thread_manager.automation_instances:
            custom_logger.warning("등록된 자동화가 없습니다.")
            return

        custom_logger.info(f"\n✓ 자동화 {len(self.thread_manager.automation_instances)}개 시작 완료\n")

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