from datetime import datetime
from typing import Optional
from interfaces.automation.base import BaseAutomation
from interfaces.Machine import BaseMachine
from interfaces.automation.models import MQTTMessage, TopicType

class RangeAutomation(BaseAutomation):
    def _init_from_settings(self, settings: dict) -> None:
        """Range 자동화 설정 초기화"""
        try:
            self.start = settings.get('start')
            self.end = settings.get('end')
            self.logger.info(f"Range 자동화 설정 초기화: start={self.start}, end={self.end}")
        except Exception as e:
            self.start = None
            self.end = None
            self.logger.warning("Range 자동화 설정이 비어있습니다.")

    def is_time_in_range(self, current_time: str) -> bool:
        """시간이 설정된 범위 내에 있는지 확인"""
        if self.start > self.end:  # 자정을 걸치는 경우 (예: 22:00 ~ 06:00)
            return current_time >= self.start or current_time <= self.end
        return self.start <= current_time <= self.end  # 일반적인 경우

    def control(self) -> Optional[BaseMachine]:
        """시간 기반 제어 실행"""
        if not super().control():
            return None

        if not all([self.start, self.end, self.pin]):
            self.logger.error(f"Device {self.name}: 필수 설정이 누락되었습니다.")
            raise ValueError(f"Device {self.name}: 필수 설정이 누락되었습니다.")

        try:
            now = datetime.now().strftime('%H:%M')
            should_be_on = self.is_time_in_range(now)
            current_status = bool(self.status)
            
            if should_be_on != current_status:
                self.update_device_status(should_be_on)
                
            return self.get_machine()

        except Exception as e:
            self.logger.error(f"Device {self.name} 제어 중 오류 발생: {str(e)}")
            raise 

    def _on_mqtt_message(self, client, userdata, message) -> None:
        """MQTT 메시지 수신 처리 (Range 자동화)"""
        try:
            if not self.active:
                self.logger.warning(f"Device {self.name}: 비활성화되어 메시지 처리 건너뜀")
                return
            
            # MQTT 메시지를 객체로 변환
            mqtt_message = MQTTMessage.from_message(message)
            topic_type = TopicType.from_topic(mqtt_message.topic)
            
            if not topic_type:
                self.logger.warning(f"알 수 없는 토픽: {mqtt_message.topic}")
                return
            
            # automation, current 토픽만 처리
            if topic_type in [TopicType.AUTOMATION, TopicType.CURRENT]:
                handler = self.message_handlers.get(topic_type)
                if handler:
                    self.logger.debug(
                        f"메시지 핸들러 실행: {handler.description} "
                        f"(토픽: {topic_type.value})"
                    )
                    handler.handler(mqtt_message)
                
        except Exception as e:
            self.logger.error(f"MQTT 메시지 처리 실패: {str(e)}") 