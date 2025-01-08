import json
import RPi.GPIO as GPIO
from resources import mqtt, http
from logger.custom_logger import custom_logger
from models.Response import SwitchResponse

class GPIOController:
    def __init__(self):
        self.initialized_pins = {}  # name: pin 매핑
        
        # GPIO 초기화
        GPIO.setmode(GPIO.BCM)
        GPIO.setwarnings(False)
        
        try:
            # 현재 스위치 상태 조회 및 GPIO 설정
            self._init_gpio_from_http()
            
            # MQTT 메시지 핸들러 등록
            mqtt.client.message_callback_add('switch/#', self._on_message)
            custom_logger.info("GPIO 컨트롤러 초기화 완료")
            
        except Exception as e:
            custom_logger.error(f"초기화 실패: {str(e)}")
            raise

    def _init_gpio_from_http(self):
        """HTTP에서 현재 스위치 상태 조회하여 GPIO 초기화"""
        try:
            # 스위치 상태�� machine 정보 조회
            switches = {
                switch.name: switch 
                for switch in [SwitchResponse(**s) for s in http.get_switches()]
            }
            machines = http.get_machines()

            # machine 정보와 switch 상태 매칭하여 GPIO 설정
            for machine in machines:
                name = machine.name
                pin = machine.pin
                status = switches[name].status if name in switches else False

                GPIO.setup(pin, GPIO.OUT)
                GPIO.output(pin, GPIO.HIGH if status else GPIO.LOW)
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
            if len(topic_parts) != 2:
                return
                
            device_name = topic_parts[1]
            if device_name not in self.initialized_pins:
                return
                
            payload = json.loads(message.payload)
            new_state = bool(payload['data']['value'])
            pin = self.initialized_pins[device_name]
            
            GPIO.output(pin, GPIO.HIGH if new_state else GPIO.LOW)
            custom_logger.info(
                f"GPIO 상태 변경: {device_name} "
                f"(pin={pin}, status={'ON' if new_state else 'OFF'})"
            )
            
        except Exception as e:
            custom_logger.error(f"스위치 메시지 처리 실패: {str(e)}")

    def run(self):
        """GPIO 컨트롤러 실행"""
        try:
            custom_logger.info("GPIO 컨트롤러 시작")
            mqtt.run_forever()  # MQTT 클라이언트 영구 실행
        except KeyboardInterrupt:
            custom_logger.info("GPIO 컨트롤러 종료")
        finally:
            self.cleanup()

    def cleanup(self):
        """리소스 정리"""
        try:
            GPIO.cleanup(list(self.initialized_pins.values()))
            custom_logger.info("GPIO 컨트롤러 정리 완료")
        except Exception as e:
            custom_logger.error(f"정리 중 오류 발생: {str(e)}")

if __name__ == "__main__":
    controller = GPIOController()
    controller.run() 