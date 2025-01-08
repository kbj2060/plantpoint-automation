import paho.mqtt.client as mqtt
from logger.custom_logger import custom_logger
from constants import MQTT_HOST, MQTT_PORT, MQTT_ID

class GpioMQTTClient:
    def __init__(self):
        self.client = mqtt.Client(client_id=f"{MQTT_ID}_gpio")
        self.connected = False
        
        try:
            self.client.connect(MQTT_HOST, int(MQTT_PORT))
            custom_logger.info("MQTT 클라이언트 초기화 중...")
        except Exception as e:
            custom_logger.error(f"MQTT 연결 실패: {str(e)}")
            raise

    def connect(self):
        """MQTT 브로커 연결"""
        try:
            self.client.connect(MQTT_HOST, int(MQTT_PORT))
            return True
        except Exception as e:
            custom_logger.error(f"MQTT 연결 실패: {str(e)}")
            return False

    def run_forever(self):
        """MQTT 루프 영구 실행"""
        try:
            self.client.loop_forever()
        except Exception as e:
            custom_logger.error(f"MQTT 루프 실행 실패: {str(e)}")
            raise

    def disconnect(self):
        """MQTT 브로커 연결 종료"""
        try:
            self.client.disconnect()
            custom_logger.info("MQTT 클라이언트 종료")
        except Exception as e:
            custom_logger.error(f"MQTT 연결 종료 실패: {str(e)}")

# 싱글톤 인스턴스 생성
gpio_mqtt = GpioMQTTClient() 