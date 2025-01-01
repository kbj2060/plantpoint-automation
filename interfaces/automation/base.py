from abc import ABC, abstractmethod
from typing import Optional, Dict
from logger.custom_logger import CustomLogger
from interfaces.Machine import BaseMachine
from resources import mqtt, ws, redis
from constants import SWITCH_SOCKET_ADDRESS, WS_SWITCH_EVENT
from interfaces.automation.models import (
    MQTTMessage, 
    SwitchMessage,
    MQTTPayloadData,
    WebSocketMessage,
    TopicType,
    MessageHandler
)

class BaseAutomation(ABC):
    def __init__(self, device_id: int, category: str, active: bool, settings: dict, updated_at: str):
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
            TopicType.CURRENT: MessageHandler(
                topic_type=TopicType.CURRENT,
                handler=self._handle_current_message,
                description="전류값 메시지 처리"
            )
        }
        
        # 설정은 set_machine 이후에 초기화
        self._settings = settings  # 설정 임시 저장

    def set_machine(self, machine: BaseMachine) -> None:
        """기기 정보 설정"""
        self.name = machine.name
        self.pin = machine.pin
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
                
                # 전류값 토픽 구독
                self.current_topic = f"current/{self.name}"
                mqtt.client.message_callback_add(self.current_topic, self._on_mqtt_message)
                
                self.mqtt_subscribed = True
                self.logger.info(
                    f"MQTT 콜백 등록 성공: {self.automation_topic}, "
                    f"{self.sensor_topic}, {self.current_topic}"
                )
        except Exception as e:
            self.logger.error(f"MQTT 콜백 등록 실패: {str(e)}")

    def _on_mqtt_message(self, client, userdata, message) -> None:
        """MQTT 메시지 수신 처리 (기본)"""
        try:
            if not self.active:
                return
            
            # MQTT 메시지를 객체로 변환
            mqtt_message = MQTTMessage.from_message(message)
            topic_type = TopicType.from_topic(mqtt_message.topic)
            
            if not topic_type:
                self.logger.warning(f"알 수 없는 토픽: {mqtt_message.topic}")
                return
                
            # 해당하는 핸들러 실행
            handler = self.message_handlers.get(topic_type)
            if handler:
                self.logger.debug(
                    f"메시지 핸들러 실행: {handler.description} "
                    f"(토픽: {topic_type.value})"
                )
                handler.handler(mqtt_message)

        except Exception as e:
            self.logger.error(f"MQTT 메시지 처리 실패: {str(e)}")

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
                new_settings = payload_data.data.value.get('settings', {})
                
                if new_settings:
                    self._init_from_settings(new_settings)
                    
                self.logger.info(
                    f"Device {self.name}: 자동화 설정 업데이트 "
                    f"(활성화: {self.active}, 설정: {new_settings})"
                )

        except Exception as e:
            self.logger.error(f"자동화 설정 메시지 처리 실패: {str(e)}")

    def _handle_current_message(self, mqtt_message: MQTTMessage) -> None:
        """전류값 메시지 처리"""
        try:
            payload_data = MQTTPayloadData(
                pattern=mqtt_message.topic,
                data=SwitchMessage(
                    name=mqtt_message.topic_parts[1],
                    value=mqtt_message.payload['data']['value']
                )
            )

            if payload_data.data.name == self.name:
                redis_key = f"current/{self.name}"
                current_value = float(payload_data.data.value)
                redis.set(redis_key, str(current_value))
                
                is_running = current_value > 0.1
                if is_running != self.status:
                    self.logger.info(
                        f"Device {self.name}: 전류 기반 상태 감지 "
                        f"(전류: {current_value}A, 상태: {'ON' if is_running else 'OFF'})"
                    )
                    self.status = is_running

        except Exception as e:
            self.logger.error(f"전류값 메시지 처리 실패: {str(e)}")

    def _handle_switch_message(self, mqtt_message: MQTTMessage) -> None:
        """스위치 상태 메시지 처리"""
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
                    self.logger.info(
                        f"Device {self.name}: 스위치 상태 변경 감지 "
                        f"({'ON' if new_status else 'OFF'})"
                    )
                    self.status = new_status
                    
                    # Redis에 상태 저장
                    redis_key = f"switch/{self.name}"
                    redis.set(redis_key, str(int(new_status)))

        except Exception as e:
            self.logger.error(f"스위치 상태 메시지 처리 실패: {str(e)}")

    def _handle_environment_message(self, mqtt_message: MQTTMessage) -> None:
        """환경 센서값 메시지 처리"""
        try:
            payload_data = MQTTPayloadData(
                pattern=mqtt_message.topic,
                data=SwitchMessage(
                    name=mqtt_message.topic_parts[1],
                    value=mqtt_message.payload['data']['value']
                )
            )

            if payload_data.data.name == self.name:
                redis_key = mqtt_message.topic
                env_value = float(payload_data.data.value)
                redis.set(redis_key, str(env_value))
                
                self.logger.info(
                    f"Device {self.name}: 환경 센서값 수신 "
                    f"(값: {env_value})"
                )

        except Exception as e:
            self.logger.error(f"환경 센서값 메시지 처리 실패: {str(e)}")

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

    def send_websocket_message(self, new_status: bool) -> None:
        """WebSocket 메시지 전송"""
        try:
            # WebSocket 메시지 생성
            ws_payload = WebSocketMessage.from_switch(
                name=self.name,
                value=new_status,
                event=WS_SWITCH_EVENT
            )
            
            # WebSocket 클라이언트 생성 및 메시지 전송
            ws_client = ws(url=f'{SWITCH_SOCKET_ADDRESS}/{self.name}')    
            ws_client.send_message(**ws_payload.to_dict())
            ws_client.disconnect()
            self.logger.info(f"WebSocket 메시지 전송 성공: {self.name} = {new_status}")
        except Exception as e:
            self.logger.error(f"WebSocket 메시지 전송 실패: {str(e)}")
            raise

    def update_device_status(self, new_status: bool) -> None:
        """디바이스 상태 업데이트 및 메시지 전송"""
        try:
            self.send_mqtt_message(new_status)
            self.send_websocket_message(new_status)
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

    def get_sensor_value(self, sensor_name: str) -> Optional[float]:
        """Redis에서 센서값 조회 (기본 - 전류값만)"""
        try:
            # 전류값 조회만 처리
            if sensor_name.startswith('current/'):
                redis_key = sensor_name
                value = redis.get(redis_key)
                if value is None:
                    return None
                return float(value)
            return None
        except ValueError as e:
            self.logger.error(f"센서값 변환 실패: {str(e)}")
            return None
        except Exception as e:
            self.logger.error(f"센서값 조회 실패: {str(e)}")
            return None

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
        