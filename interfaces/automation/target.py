from typing import Optional
from interfaces.automation.base import BaseAutomation
from interfaces.Machine import BaseMachine
from logger.custom_logger import custom_logger
from interfaces.automation.models import MQTTMessage, MQTTPayloadData, MessageHandler, SwitchMessage, TopicType
from resources import redis

class TargetAutomation(BaseAutomation):
    def __init__(self, device_id: str, category: str, active: bool, settings: dict, updated_at: str = None):
        super().__init__(device_id, category, active, settings, updated_at)
        
        # Target 자동화는 environment 토픽도 처리
        self.message_handlers[TopicType.ENVIRONMENT] = MessageHandler(
            topic_type=TopicType.ENVIRONMENT,
            handler=self._handle_environment_message,
            description="환경 센서값 메시지 처리"
        )

    def _init_from_settings(self, settings: dict) -> None:
        """Target 자동화 설정 초기화"""
        try:
            self.target = float(settings.get('target'))
            self.margin = float(settings.get('margin'))
            self.in_range_count = 0  # 초기화 시점에 0으로 설정
            self.required_count = 3  # 필요한 연속 카운트 수는 3
            self.current_threshold = 0.1
            self.value = None
            custom_logger.info(f"Target 자동화 설정 초기화: target={self.target}, margin={self.margin}")
        except (TypeError, ValueError) as e:
            self.target = None
            self.margin = None
            custom_logger.warning("Target 자동화 설정이 비어있습니다.")

    def get_device_status(self) -> bool:
        """전류값으로 장치 상태 확인"""
        try:
            current_value = self.get_sensor_value(self.current_topic)  # 저장된 전류값 토픽 사용
            if current_value is None:
                # 전류값을 못 받아올 경우 기존 상태 반환
                return bool(self.status)
            
            # 전류값이 임계값보다 크면 작동 중
            is_running = current_value > self.current_threshold
            
            if is_running != bool(self.status):
                custom_logger.info(
                    f"Device {self.name}: 전류 기반 상태 변경 감지 "
                    f"(전류: {current_value}A, 상태: {'ON' if is_running else 'OFF'})"
                )
            
            return is_running
        except Exception as e:
            custom_logger.error(f"전류값 확인 중 오류 발생: {str(e)}")
            return bool(self.status)

    def control(self) -> Optional[BaseMachine]:
        """목표값 기반 제어 실행"""
        if not super().control():
            return None

        if not all([self.target is not None, self.margin is not None, self.pin, self.name]):
            custom_logger.error(f"Device {self.name}: 필수 설정이 누락되었습니다.")
            raise ValueError(f"Device {self.name}: 필수 설정이 누락되었습니다.")
        
        if self.value is None:
            # 센서값이 없으면 제어하지 않고 종료
            custom_logger.info(f"Device {self.name}: 센서값이 없어 제어하지 않습니다.")
            return None

        try:
            value_difference = abs(self.value - self.target)
            lower_bound = self.target - self.margin
            upper_bound = self.target + self.margin
            
            # 현재 상태 로깅
            custom_logger.info(
                f"Device {self.name} 상태 체크: "
                f"현재값={self.value}, "
                f"목표값={self.target}, "
                f"허용범위={lower_bound} ~ {upper_bound}, "
                f"현재상태={'ON' if self.status else 'OFF'}, "
                f"연속 카운트={self.in_range_count}/{self.required_count}"
            )
            
            # 목표값과의 차이가 허용 오차를 벗어난 경우
            if value_difference > self.margin:
                # 범위를 벗어나면 카운트 리셋
                self.in_range_count = 0
                should_be_on = self.value < self.target
                
                if should_be_on != self.status:
                    self.update_device_status(should_be_on)
                    custom_logger.info(
                        f"Device {self.name}: 상태 변경 "
                        f"({'ON' if should_be_on else 'OFF'}으로 전환) "
                        f"현재값({self.value}), "
                        f"목표값({self.target}), "
                        f"허용범위({lower_bound} ~ {upper_bound})"
                    )
            else:
                # 허용 오차 범위 내에 있는 경우
                if self.in_range_count < self.required_count:
                    self.in_range_count += 1
                    custom_logger.info(
                        f"Device {self.name}: 목표값 범위 내 "
                        f"(연속 카운트: {self.in_range_count}/{self.required_count})"
                    )
                
                # 연속 카운트가 목표에 도달하고 장치가 켜져 있다면 끄기
                if self.in_range_count >= self.required_count and self.status:
                    self.update_device_status(False)
                    self.in_range_count = 0  # 카운트 리셋
                    custom_logger.info(
                        f"Device {self.name}: 목표값 {self.required_count}회 연속 도달로 OFF "
                        f"현재값({self.value}), "
                        f"목표값({self.target}), "
                        f"허용범위({lower_bound} ~ {upper_bound})"
                    )
            
            return self.get_machine()

        except Exception as e:
            custom_logger.error(f"Device {self.name} 제어 중 오류 발생: {str(e)}")
            raise 

    def _on_mqtt_message(self, client, userdata, message) -> None:
        """MQTT 메시지 수신 처리 (Target 자동화)"""
        try:
            if not self.active:
                custom_logger.warning(f"Device {self.name}: 비활성화되어 메시지 처리 건너뜀")
                return
        
            # MQTT 메시지를 객체로 변환
            mqtt_message = MQTTMessage.from_message(message)
            topic_type = TopicType.from_topic(mqtt_message.topic)
            
            if not topic_type:
                custom_logger.warning(f"알 수 없는 토픽: {mqtt_message.topic}")
                return
            
            # automation, current, environment 토픽만 처리
            if topic_type in [TopicType.AUTOMATION, TopicType.CURRENT, TopicType.ENVIRONMENT]:
                handler = self.message_handlers.get(topic_type)
                if handler:
                    custom_logger.debug(
                        f"메시지 핸들러 실행: {handler.description} "
                        f"(토픽: {topic_type.value})"
                    )
                    handler.handler(mqtt_message)
                
        except Exception as e:
            custom_logger.error(f"MQTT 메시지 처리 실패: {str(e)}") 

    def get_sensor_value(self, sensor_name: str) -> Optional[float]:
        """Redis에서 센서값 조회 (Target 자동화 - 환경 센서값 + 전류값)"""
        try:
            # 전류값 조회는 부모 클래스 메서드 사용
            if sensor_name.startswith('current/'):
                return super().get_sensor_value(sensor_name)
            
            # 환경 센서값 조회
            redis_key = self.sensor_topic
            value = redis.get(redis_key)
            if value is None:
                custom_logger.info(f"Device {self.name}: 센서값 수신 대기 중... (키: {redis_key})")
                return None
            
            return float(value)
        except ValueError as e:
            custom_logger.error(f"센서값 변환 실패: {str(e)}")
            return None
        except Exception as e:
            custom_logger.error(f"센서값 조회 실패: {str(e)}")
            return None 

    def _handle_environment_message(self, mqtt_message: MQTTMessage) -> None:
        """환경 센서값 메시지 처리 (Target 자동화)"""
        try:
            payload_data = MQTTPayloadData(
                pattern=mqtt_message.topic,
                data=SwitchMessage(
                    name=mqtt_message.topic_parts[1],
                    value=mqtt_message.payload['data']['value']
                )
            )

            if payload_data.data.name == self.name:
                self.value = float(payload_data.data.value)
                redis_key = f"environment/{self.name}"
                redis.set(redis_key, str(self.value))
                
                custom_logger.info(
                    f"Device {self.name}: 환경 센서값 수신 "
                    f"(값: {self.value})"
                )
                
                try:
                    controlled_machine = self.control()
                    if controlled_machine:
                        custom_logger.info(
                            f"자동화 실행 성공: {self.name} "
                            f"(현재값: {self.value}, 상태: {self.status})"
                        )
                except Exception as e:
                    custom_logger.error(f"자동화 실행 중 오류 발생: {str(e)}")

        except Exception as e:
            custom_logger.error(f"환경 센서값 메시지 처리 실패: {str(e)}") 