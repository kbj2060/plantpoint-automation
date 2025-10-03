from abc import ABC, abstractmethod
from typing import Optional, Dict
from logger.custom_logger import CustomLogger
from models.Machine import BaseMachine
from resources import mqtt
from models.automation.models import (
    MQTTMessage,
    SwitchMessage,
    MQTTPayloadData,
    TopicType,
    MessageHandler
)

class BaseAutomation(ABC):
    def __init__(self, device_id: int, category: str, active: bool, updated_at: str, settings: dict):
        self.device_id = device_id
        self.category = category
        self.active = active
        self.updated_at = updated_at
        self.name: Optional[str] = None
        self.mqtt_topic: Optional[str] = None
        self.pin: Optional[int] = None
        self.status: Optional[bool] = None
        self.switch_created_at: Optional[str] = None
        self.mqtt_subscribed = False
        self.sensor_name: Optional[str] = None
        # 임시 로거 생성 (초기화 단계용)
        self.logger = CustomLogger()
                
        # 기본 메시지 핸들러 등록
        self.message_handlers: Dict[TopicType, MessageHandler] = {
            TopicType.AUTOMATION: MessageHandler(
                topic_type=TopicType.AUTOMATION,
                handler=self._handle_automation_message,
                description="자동화 설정 메시지 처리"
            ),
            TopicType.SWITCH: MessageHandler(
                topic_type=TopicType.SWITCH,
                handler=self._handle_switch_message,
                description="스위치 상태 메시지 처리"
            )
        }
        self._settings = settings
        

    def set_machine(self, machine: BaseMachine) -> None:
        """기기 정보 설정 및 GPIO 초기화"""
        self.name = machine.name
        self.pin = int(machine.pin)
        self.status = machine.status
        self.mqtt_topic = f"switch/{self.name}"
        self.switch_created_at = machine.switch_created_at
        self.sensor_name = self.name
        
        # 이름이 설정된 후에 로거 초기화
        self.logger = self.logger.set_machine(self.name)
        
        # MQTT 구독 설정
        self._setup_mqtt_subscription()
        
        # 설정 초기화 (로거 설정 후)
        self._init_from_settings(self._settings)
        
    def _setup_mqtt_subscription(self) -> None:
        """MQTT 토픽 구독 설정"""
        try:
            if self.name and not self.mqtt_subscribed:
                # 자동화 토픽 구독
                self.automation_topic = f"automation/{self.name}"
                mqtt.client.message_callback_add(self.automation_topic, self._on_mqtt_message)
                
                # 센서값 토픽 구독
                self.sensor_topic = f"environment/{self.name}"
                mqtt.client.message_callback_add(self.sensor_topic, self._on_mqtt_message)

                # 스위치 토픽 구독
                self.switch_topic = f"switch/{self.name}"
                mqtt.client.message_callback_add(self.switch_topic, self._on_mqtt_message)
                
                self.mqtt_subscribed = True
                # self.logger.info(
                #     f"MQTT 콜백 등록 성공: {self.automation_topic}, "
                #     f"{self.sensor_topic}, {self.switch_topic}"
                # )
        except Exception as e:
            self.logger.error(f"MQTT 콜백 등록 실패: {str(e)}")

    def _on_mqtt_message(self, client, userdata, message) -> None:
        """MQTT 메시지 수신 처리 (기본)"""
        try:
            # MQTT 메시지를 객체로 변환
            mqtt_message = MQTTMessage.from_message(message)
            topic_type = TopicType.from_topic(mqtt_message.topic)
            
            if not topic_type:
                self.logger.warning(f"알 수 없는 토픽: {mqtt_message.topic}")
                return
                
            # 해당하는 핸들러 실행
            handler = self.message_handlers.get(topic_type)
            if handler:
                # self.logger.debug(
                #     f"메시지 핸들러 실행: {handler.description} "
                #     f"(토픽: {topic_type.value})"
                # )
                handler.handler(mqtt_message)

        except Exception as e:
            self.logger.error(f"MQTT 메시지 처리 실패: {str(e)}")

    def filter_settings_dict(self, data: dict) -> dict:
        """
        id, active, updated_at 키를 제거한 settings 딕셔너리 반환
        """
        return {k: v for k, v in data.items() if k not in ('id', 'active', 'updated_at')}
    
    def _handle_automation_message(self, mqtt_message: MQTTMessage) -> None:
        """자동화 설정 메시지 처리"""
        try:
            payload_data = MQTTPayloadData(
                pattern=mqtt_message.topic,
                data=SwitchMessage(
                    name=mqtt_message.topic_parts[1],
                    value=mqtt_message.payload['data']['value']
                )
            )

            if payload_data.data.name == self.name:
                # 자동화 설정 업데이트
                self.active = payload_data.data.value.get('active', False)
                new_settings = self.filter_settings_dict(payload_data.data.value)

                if new_settings:
                    self._init_from_settings(new_settings)
                    self.control()
                    
                self.logger.info(
                    f"Device {self.name}: 자동화 설정 업데이트 "
                    f"(활성화: {self.active}, 설정: {new_settings})"
                )

        except Exception as e:
            self.logger.error(f"자동화 설정 메시지 처리 실패: {str(e)}")

    def _handle_switch_message(self, mqtt_message: MQTTMessage) -> None:
        """스위치 상태 메시지 처리 및 GPIO 제어"""
        try:
            payload_data = MQTTPayloadData(
                pattern=mqtt_message.topic,
                data=SwitchMessage(
                    name=mqtt_message.topic_parts[1],
                    value=mqtt_message.payload['data']['value']
                )
            )

            if payload_data.data.name == self.name:
                new_status = bool(payload_data.data.value)
                if new_status != self.status:
                    self.status = new_status

        except Exception as e:
            self.logger.error(f"스위치 상태 메시지 처리 실패: {str(e)}")

    def send_mqtt_message(self, new_status: bool) -> None:
        """MQTT 메시지 전송"""
        try:
            # 스위치 메시지 생성
            switch_message = SwitchMessage(
                name=self.name,
                value=new_status
            )
            
            # MQTT 페이로드 생성
            mqtt_payload = MQTTPayloadData(
                pattern=self.mqtt_topic,
                data=switch_message
            )
            
            # 메시지 전송
            mqtt.publish_message(self.mqtt_topic, mqtt_payload.to_dict())
            self.logger.info(f"MQTT 메시지 전송 성공: {self.name} = {new_status}")
        except Exception as e:
            self.logger.error(f"MQTT 메시지 전송 실패: {str(e)}")
            raise

    def update_device_status(self, new_status: bool) -> None:
        """디바이스 상태 업데이트 및 GPIO 제어"""
        try:
            self.send_mqtt_message(new_status)
            self.status = new_status
            self.logger.info(f"상태 업데이트 성공: {self.name} / {self.device_id} = {new_status}")
        except Exception as e:
            self.logger.error(f"상태 업데이트 실패: {str(e)}")
            raise

    def get_machine(self) -> BaseMachine:
        """현재 상태의 BaseMachine 객체 생성"""
        return BaseMachine(
            machine_id=self.device_id,
            name=self.name,
            pin=self.pin,
            status=self.status,
            switch_created_at=self.switch_created_at
        )

    @abstractmethod
    def _init_from_settings(self, settings: dict) -> None:
        """각 자동화 타입별 설정 초기화"""
        pass

    @abstractmethod
    def control(self) -> Optional[BaseMachine]:
        """자동화 제어 실행"""
        # 나중에 자동화 활성화하게 될 경우 mqtt로 변경값 받아와서 self.active 값 변경
        if not self.active:
            self.logger.debug(f"자동화 비활성화: {self.name}")

        return self.get_machine() 