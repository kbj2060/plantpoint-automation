import json
import paho.mqtt.client as mqtt
from logger.custom_logger import custom_logger
from constants import MQTT_HOST, MQTT_PORT, MQTT_ID


class MQTTClient:
    def __init__(self):
        self.client = mqtt.Client(client_id=MQTT_ID)
        self.client.on_connect = self.on_connect
        self.client.on_disconnect = self.on_disconnect
        
        try:
            self.client.connect(MQTT_HOST, int(MQTT_PORT))
            self.client.loop_start()
            custom_logger.info("MQTT 클라이언트 초기화 중...")
        except Exception as e:
            custom_logger.error(f"MQTT 연결 실패: {str(e)}")
            raise

    def on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            custom_logger.info("MQTT 브로커 연결 성공")
            self.client.subscribe([
                ("environment/#", 0),
                ("automation/#", 0),
                ("switch/#", 0),
            ])
            custom_logger.info("MQTT 토픽 구독: environment/#, automation/#, current/#, switch/#")
        else:
            custom_logger.error(f"MQTT 브로커 연결 실패 (code: {rc})")

    def on_disconnect(self, client, userdata, rc):
        if rc != 0:
            custom_logger.warning("MQTT 브로커 연결이 예기치 않게 종료됨")
        else:
            custom_logger.info("MQTT 브로커 연결 종료")

    def publish_message(self, topic: str, payload: dict) -> bool:
        """
        MQTT 메시지 발행
        Args:
            topic: MQTT 토픽
            payload: 전송할 데이터 {name: str, value: int}
        Returns:
            bool: 발행 성공 여부
        """
        try:
            info = self.client.publish(topic, json.dumps(payload))
            if info.rc == mqtt.MQTT_ERR_SUCCESS:
                return True
            else:
                custom_logger.error(f"MQTT 메시지 발행 실패: {mqtt.error_string(info.rc)}")
                return False
        except Exception as e:
            custom_logger.error(f"MQTT 메시지 발행 중 오류: {str(e)}")
            return False

    def disconnect(self):
        """MQTT 브로커 연결 종료"""
        try:
            self.client.loop_stop()
            self.client.disconnect()
            custom_logger.info("MQTT 클라이언트 종료")
        except Exception as e:
            custom_logger.error(f"MQTT 연결 종료 실패: {str(e)}") 


