from abc import ABC, abstractmethod
from typing import Optional
from logger.custom_logger import custom_logger
from interfaces.Machine import BaseMachine
from resources import mqtt, ws, redis
from constants import SWITCH_SOCKET_ADDRESS, WS_SWITCH_EVENT
from interfaces.automation.models import (
    MQTTMessage, 
    SwitchMessage,
    MQTTPayloadData,
    WebSocketMessage
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
        self._init_from_settings(settings)

    def set_machine(self, machine: BaseMachine) -> None:
        """기기 정보 설정"""
        self.name = machine.name
        self.pin = machine.pin
        self.status = machine.status
        self.mqtt_topic = f"switch/{self.name}"
        self.switch_created_at = machine.switch_created_at
        self.sensor_name = self.name
        self._setup_mqtt_subscription()

    def _setup_mqtt_subscription(self) -> None:
        """MQTT 토픽 구독 설정"""
        try:
            if self.name and not self.mqtt_subscribed:
                # 센서값 토픽 구독
                self.sensor_topic = f"environment/{self.name}"
                mqtt.client.message_callback_add(self.sensor_topic, self._on_mqtt_message)
                
                # 전류값 토픽 구독
                self.current_topic = f"current/{self.name}"
                mqtt.client.message_callback_add(self.current_topic, self._on_mqtt_message)
                
                self.mqtt_subscribed = True
                custom_logger.info(f"MQTT 콜백 등록 성공: {self.sensor_topic}, {self.current_topic}")
        except Exception as e:
            custom_logger.error(f"MQTT 콜백 등록 실패: {str(e)}")

    def _on_mqtt_message(self, client, userdata, message) -> None:
        """MQTT 메시지 수신 처리 (기본)"""
        try:
            # MQTT 메시지를 객체로 변환
            mqtt_message = MQTTMessage.from_message(message)
            sensor_data = mqtt_message.to_sensor_data()
            
            if sensor_data:
                # 전류값 메시지 처리
                if mqtt_message.topic.startswith('current/'):
                    try:
                        current_value = float(sensor_data.value)
                        # 전류 임계값 (0.1A) 이상이면 작동 중으로 판단
                        is_running = current_value > 0.1
                        
                        if is_running != self.status:
                            self.status = is_running
                            custom_logger.info(
                                f"Device {self.name}: 전류 기반 상태 감지로 상태 업데이트 "
                                f"(전류: {current_value}A, 상태: {'ON' if is_running else 'OFF'})"
                            )
                    except ValueError as e:
                        custom_logger.error(f"전류값 변환 실패: {str(e)}")
                    
        except Exception as e:
            custom_logger.error(f"MQTT 메시지 처리 실패: {str(e)}")

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
            custom_logger.info(f"MQTT 메시지 전송 성공: {self.name} = {new_status}")
        except Exception as e:
            custom_logger.error(f"MQTT 메시지 전송 실패: {str(e)}")
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
            custom_logger.info(f"WebSocket 메시지 전송 성공: {self.name} = {new_status}")
        except Exception as e:
            custom_logger.error(f"WebSocket 메시지 전송 실패: {str(e)}")
            raise

    def update_device_status(self, new_status: bool) -> None:
        """디바이스 상태 업데이트 및 메시지 전송"""
        try:
            self.send_mqtt_message(new_status)
            self.send_websocket_message(new_status)
            self.status = new_status
            custom_logger.info(f"상태 업데이트 성공: {self.name} / {self.device_id} = {new_status}")
        except Exception as e:
            custom_logger.error(f"상태 업데이트 실패: {str(e)}")
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
            custom_logger.error(f"센서값 변환 실패: {str(e)}")
            return None
        except Exception as e:
            custom_logger.error(f"센서값 조회 실패: {str(e)}")
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
            custom_logger.debug(f"자동화 비활성화: {self.name}")

        return self.get_machine() 