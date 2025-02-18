import json
import paho.mqtt.client as mqtt
from resources import http
from logger.custom_logger import custom_logger
from models.Response import SwitchResponse
from constants import MQTT_HOST, MQTT_PORT
import sys

if sys.platform != "linux":
    from fake_rpi.RPi import GPIO
else:
    import RPi.GPIO as GPIO
    
class GPIOController:
    def __init__(self):
        self.initialized_pins = {}  # name: pin 매핑
        self.connected = False
        
        # GPIO 초기화
        GPIO.setmode(GPIO.BCM)
        GPIO.setwarnings(False)
        
        try:
            # 현재 스위치 상태 조회 및 GPIO 설정
            self._init_gpio_from_http()
            
            # MQTT 클라이언트 초기화
            self.client = mqtt.Client(client_id=f"gpio")
            self.client.on_connect = self._on_connect
            self.client.on_disconnect = self._on_disconnect
            self.client.message_callback_add('switch/#', self._on_message)
            
            # MQTT 연결
            self.client.connect(MQTT_HOST, int(MQTT_PORT))
            custom_logger.info("GPIO 컨트롤러 초기화 완료")
            
        except Exception as e:
            custom_logger.error(f"초기화 실패: {str(e)}")
            raise

    def _on_connect(self, client, userdata, flags, rc):
        """MQTT 연결 콜백"""
        if rc == 0:
            self.connected = True
            custom_logger.info("MQTT 브로커 연결 성공")
            client.subscribe("switch/#")
        else:
            self.connected = False
            custom_logger.error(f"MQTT 연결 실패 (code: {rc})")

    def _on_disconnect(self, client, userdata, rc):
        """MQTT 연결 해제 콜백"""
        self.connected = False
        custom_logger.info("MQTT 브로커 연결 종료")

    def loop_forever(self):
        """MQTT 루프 영구 실행"""
        try:
            if not self.client.is_connected():
                self.client.reconnect()
            self.client.loop_forever()
        except Exception as e:
            custom_logger.error(f"MQTT 루프 실행 실패: {str(e)}")
            return False

    def _init_gpio_from_http(self):
        """HTTP에서 현재 스위치 상태 조회하여 GPIO 초기화"""
        try:
            # 스위치 상태와 machine 정보 조회
            switches = {
                switch.name: switch 
                for switch in [SwitchResponse(**s) for s in http.get_switches()]
            }
            machines = http.get_machines()

            # machine 정보와 switch 상태 매칭하여 GPIO 설정
            for machine in machines:
                name = machine['name']
                pin = machine['pin']
                status = switches[name].status if name in switches else False

                GPIO.setup(pin, GPIO.OUT)
                self.initialized_pins[name] = pin
                
                custom_logger.info(
                    f"GPIO 설정 완료: {name} "
                    f"(pin={pin}, initial={'ON' if status else 'OFF'})"
                )
                
        except Exception as e:
            custom_logger.error(f"GPIO 초기화 실패: {str(e)}")
            raise

    def _on_message(self, client, userdata, message):
        """MQTT 메시지 수신 처리"""
        try:
            topic_parts = message.topic.split('/')
            if len_topic_parts := len(topic_parts) != 2:
                custom_logger.warning(f"잘못된 토픽 형식: {message.topic} (parts: {len_topic_parts})")
                return
                
            device_name = topic_parts[1]
            if device_name not in self.initialized_pins:
                custom_logger.warning(f"알 수 없는 디바이스: {device_name}")
                return
                
            # 메시지 디코딩
            payload = message.payload
            if isinstance(payload, bytes):
                payload = payload.decode()
            
            payload = json.loads(payload)
            new_state = bool(payload['data']['value'])
            pin = self.initialized_pins[device_name]
            
            GPIO.output(pin, GPIO.HIGH if new_state else GPIO.LOW)
            custom_logger.info(
                f"GPIO 상태 변경: {device_name} "
                f"(pin={pin}, status={'ON' if new_state else 'OFF'})"
            )
            
        except json.JSONDecodeError as e:
            custom_logger.error(f"JSON 파싱 실패: {str(e)}, payload: {payload}")
        except Exception as e:
            custom_logger.error(f"스위치 메시지 처리 실패: {str(e)}")

    def run(self):
        """GPIO 컨트롤러 실행"""
        try:
            custom_logger.info("GPIO 컨트롤러 시작")
            self.loop_forever()
        except KeyboardInterrupt:
            custom_logger.info("GPIO 컨트롤러 종료")
        finally:
            self.cleanup()

    def cleanup(self):
        """리소스 정리"""
        try:
            if self.client.is_connected():
                self.client.disconnect()
            GPIO.cleanup(list(self.initialized_pins.values()))
            custom_logger.info("GPIO 컨트롤러 정리 완료")
        except Exception as e:
            custom_logger.error(f"정리 중 오류 발생: {str(e)}")

if __name__ == "__main__":
    controller = GPIOController()
    controller.run() 
