from threading import Thread
import time
# import RPi.GPIO as GPIO
from typing import Dict, List
from collections import defaultdict
from resources import mqtt, ws
from constants import CURRENT_SOCKET_ADDRESS, SEND_CURRENT_TO_SERVER
from logger.custom_logger import custom_logger

class CurrentThread(Thread):
    def __init__(self, current_configs: List[Dict]):
        """
        current_configs: [
            {
                'device': 'device_name',
                'pin': gpio_pin_number
            },
            ...
        ]
        """
        super().__init__()
        self.current_configs = current_configs
        self.active = True
        self.threshold = 1.0  # 작동 중 판단 임계값
        self.previous_states = {}  # 이전 상태 저장
        self.reading_buffer = defaultdict(list)  # 디바이스별 읽기 버퍼
        self.BUFFER_SIZE = 5  # 5초 동안의 데이터 수집
        
        # GPIO 설정
        # GPIO.setmode(GPIO.BCM)
        # for config in current_configs:
        #     GPIO.setup(config['pin'], GPIO.IN)
        #     self.previous_states[config['device']] = 0  # 초기값 설정
            
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
                # raw_value = GPIO.input(config['pin'])
                # current_value = self._convert_to_current(raw_value)
                
                # 버퍼에 현재 값 추가
                # self.reading_buffer[device].append(current_value)
                
                # 버퍼가 가득 차면 처리
                if len(self.reading_buffer[device]) >= self.BUFFER_SIZE:
                    stable_value = self._process_buffer(device)
                    if stable_value is not None:
                        self._handle_current_change(device, stable_value)
                    # 버퍼 초기화
                    self.reading_buffer[device] = []
                    
            except Exception as e:
                custom_logger.error(f"전류 체크 실패 (device: {config['device']}): {str(e)}")
    
    def _process_buffer(self, device: str) -> float:
        """버퍼의 값들을 분석하여 안정적인 값 반환"""
        buffer = self.reading_buffer[device]
        
        # 모든 값이 동일한지 확인
        if len(set(buffer)) == 1:
            return buffer[0]
        
        # 값이 다르면 None 반환 (무시)
        return None
    
    def _handle_current_change(self, device: str, current_value: float):
        """안정적인 전류값 변경 처리"""
        # 이전 값과 비교하여 변경된 경우만 전송
        if current_value != self.previous_states.get(device):
            self.previous_states[device] = current_value
            
            is_running = current_value > self.threshold
            custom_logger.debug(
                f"전류 변경 감지: {device} "
                f"(값: {current_value}A, 상태: {'ON' if is_running else 'OFF'})"
            )
            
            # MQTT로 전송
            self._send_mqtt_message(device, current_value)
            
            # WebSocket으로 전송
            self._send_websocket_message(device, current_value)
    
    def _convert_to_current(self, raw_value: int) -> float:
        """GPIO 값을 전류값으로 변환"""
        # TODO: 실제 하드웨어에 맞게 변환 로직 구현
        return float(raw_value)
        
    def _send_mqtt_message(self, device: str, value: float):
        """MQTT로 전류값 전송"""
        try:
            topic = f"current/{device}"
            payload = {
                "pattern": topic,
                "data": {
                    "name": device,
                    "value": value
                }
            }
            mqtt.publish_message(topic, payload)
            
        except Exception as e:
            custom_logger.error(f"MQTT 메시지 전송 실패: {str(e)}")
            
    def _send_websocket_message(self, device: str, value: float):
        """WebSocket으로 전류값 전송"""
        try:
            payload = {
                "event": SEND_CURRENT_TO_SERVER,
                "data": {
                    "name": device,
                    "value": value
                }
            }
            
            ws_client = ws(url=f"{CURRENT_SOCKET_ADDRESS}/{device}")
            ws_client.send_message(**payload)
            ws_client.disconnect()
            
        except Exception as e:
            custom_logger.error(f"WebSocket 메시지 전송 실패: {str(e)}")
            
    def stop(self):
        """모니터링 종료"""
        self.active = False
        # GPIO.cleanup([config['pin'] for config in self.current_configs])