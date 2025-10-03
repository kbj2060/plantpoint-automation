from threading import Thread
import time
from typing import Dict, List
from collections import defaultdict
from resources import mqtt
from constants import USE_REAL_GPIO
from logger.custom_logger import custom_logger
from models.Message import MQTTPayload


if not USE_REAL_GPIO:
    import fake_rpi
    fake_rpi.toggle_print(False)  # fake GPIO 디버그 출력 끄기
    from fake_rpi.RPi import GPIO
else:
    import RPi.GPIO as GPIO
    
class CurrentThread(Thread):
    def __init__(self, current_configs: List[Dict]):
        super().__init__()
        self.current_configs = current_configs
        self.active = True
        self.previous_states = {}  # 이전 상태 저장
        self.reading_buffer = defaultdict(list)  # 디바이스별 읽기 버퍼
        self.BUFFER_SIZE = 5  # 5초 동안의 데이터 수집
        
        # GPIO 설정
        GPIO.setmode(GPIO.BCM)
        for config in current_configs:
            GPIO.setup(config['pin'], GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
            self.previous_states[config['device']] = config['current']
            
        self.daemon = True
        
    def run(self):
        """전류 모니터링 실행"""
        custom_logger.info("전류 모니터링 시작")
        custom_logger.info(f"모니터링 대상: {[c['device'] for c in self.current_configs]}")
        
        while self.active:
            try:
                self._check_and_send_currents()
                time.sleep(1)  # 1초 간격으로 체크
                
            except Exception as e:
                custom_logger.error(f"전류 모니터링 오류: {str(e)}")
                time.sleep(5)  # 오류 발생시 5초 대기
                
    def _check_and_send_currents(self):
        """전류값 확인 및 변경사항 전송"""
        for config in self.current_configs:
            try:
                device = config['device']
                current_state: bool = GPIO.input(config['pin']) == GPIO.HIGH
                
                # 버퍼에 현재 상태 추가
                self.reading_buffer[device].append(current_state)
                
                # 버퍼가 가득 차면 처리
                if len(self.reading_buffer[device]) >= self.BUFFER_SIZE:
                    stable_state = self._process_buffer(device)
                    if stable_state is not None:
                        if stable_state != self.previous_states[device]:
                            self._handle_current_change(device, stable_state)
                            self.previous_states[device] = stable_state
                        else:
                            # MQTT로 전송 (백엔드가 웹소켓으로 브로드캐스트)
                            self._send_mqtt_message(device, stable_state)
                    
                    # 버퍼 초기화
                    self.reading_buffer[device] = []
                    
            except Exception as e:
                custom_logger.error(f"전류 체크 실패 (device: {config['device']}): {str(e)}")
    
    def _process_buffer(self, device: str) -> bool:
        """버퍼의 값들을 분석하여 안정적인 상태 반환"""
        buffer = self.reading_buffer[device]
        
        # 모든 값이 동일한지 확인
        if len(set(buffer)) == 1:
            return buffer[0]  # GPIO.HIGH 또는 GPIO.LOW 반환
        
        # 값이 다르면 None 반환 (무시)
        return None
    
    def _handle_current_change(self, device: str, state: int):
        """전류 상태 변경 처리"""
        try:
            custom_logger.debug(
                f"전류 상태 변경 감지: {device} "
                f"(상태: {'ON' if state == GPIO.HIGH else 'OFF'})"
            )
            
            # MQTT로 전송
            self._send_mqtt_message(device, state)
            
        except Exception as e:
            custom_logger.error(f"전류 상태 변경 처리 실패: {str(e)}")
    
    def _send_mqtt_message(self, device: str, state: int):
        """MQTT로 전류 상태 전송"""
        try:
            topic = f"current/{device}"
            payload: MQTTPayload = {
                "pattern": topic,
                "data": {
                    "name": device,
                    "value": True if state == GPIO.HIGH else False
                }
            }
            mqtt.publish_message(topic, payload)
            
        except Exception as e:
            custom_logger.error(f"MQTT 메시지 전송 실패: {str(e)}")

    def stop(self):
        """모니터링 종료"""
        self.active = False
        GPIO.cleanup([config['pin'] for config in self.current_configs])