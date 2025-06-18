from typing import Optional
from models.automation.base import BaseAutomation
from models.Machine import BaseMachine
from logger.custom_logger import custom_logger
from models.automation.models import MQTTMessage, MQTTPayloadData, MessageHandler, SwitchMessage, TopicType

class TargetAutomation(BaseAutomation):
    def __init__(self, device_id: str, category: str, active: bool, target: float, margin: float, updated_at: str = None):
        self.settings = { 'target': target, 'margin': margin }
        super().__init__(device_id, category, active, updated_at, self.settings)
        
        self.message_handlers = {
            TopicType.AUTOMATION: MessageHandler(
                topic_type=TopicType.AUTOMATION,
                handler=self._handle_automation_message,
                description="자동화 설정 메시지 처리"
            ),
            TopicType.SWITCH: MessageHandler(
                topic_type=TopicType.SWITCH,
                handler=self._handle_switch_message,
                description="스위치 상태 메시지 처리"
            ),
            TopicType.ENVIRONMENT: MessageHandler(
                topic_type=TopicType.ENVIRONMENT,
                handler=self._handle_environment_message,
                description="환경 센서값 메시지 처리"
            )
        }
        
    def _init_from_settings(self, settings: dict) -> None:
        """Target 자동화 설정 초기화"""
        try:
            self.target = float(settings.get('target'))
            self.margin = float(settings.get('margin'))
            self.in_range_count = 0  # 초기화 시점에 0으로 설정
            self.required_count = 3  # 필요한 연속 카운트 수는 3
            self.value = None
            self.logger.info(f"Target 자동화 설정 초기화: target={self.target}, margin={self.margin}")
        except (TypeError, ValueError) as e:
            self.target = None
            self.margin = None
            self.logger.warning("Target 자동화 설정이 비어있습니다.")

    def control(self) -> Optional[BaseMachine]:
        """목표값 기반 제어 실행"""
        if not super().control():
            return None

        if not all([self.target is not None, self.margin is not None, self.pin, self.name]):
            self.logger.error(f"Device {self.name}: 필수 설정이 누락되었습니다.")
            raise ValueError(f"Device {self.name}: 필수 설정이 누락되었습니다.")
        
        if self.value is None:
            # 센서값이 없으면 제어하지 않고 종료
            self.logger.info(f"Device {self.name}: 센서값이 없어 제어하지 않습니다.")
            return None

        try:
            value_difference = abs(self.value - self.target)
            lower_bound = self.target - self.margin
            upper_bound = self.target + self.margin
            
            # 현재 상태 로깅
            self.logger.info(
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
                    self.logger.info(
                        f"Device {self.name}: 상태 변경 "
                        f"({'ON' if should_be_on else 'OFF'}으로 전환) "
                        f"현재값({self.value}), "
                        f"목표값({self.target}), "
                        f"허용범위({lower_bound} ~ {upper_bound})"
                    )
            else:
                # 허용 오차 범위 내에 있는 경우
                if self.in_range_count < self.required_count and self.status:
                    self.in_range_count += 1
                    self.logger.info(
                        f"Device {self.name}: 목표값 범위 내 "
                        f"(연속 카운트: {self.in_range_count}/{self.required_count})"
                    )
                
                # 연속 카운트가 목표에 도달하고 장치가 켜져 있다면 끄기
                if self.in_range_count >= self.required_count and self.status:
                    self.update_device_status(False)
                    self.in_range_count = 0  # 카운트 리셋
                    self.logger.info(
                        f"Device {self.name}: 목표값 {self.required_count}회 연속 도달로 OFF "
                        f"현재값({self.value}), "
                        f"목표값({self.target}), "
                        f"허용범위({lower_bound} ~ {upper_bound})"
                    )
            
            return self.get_machine()

        except Exception as e:
            self.logger.error(f"Device {self.name} 제어 중 오류 발생: {str(e)}")
            raise 

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
                
                self.logger.info(
                    f"Device {self.name}: 환경 센서값 수신 "
                    f"(값: {self.value})"
                )
                
                try:
                    controlled_machine = self.control()
                    if controlled_machine:
                        self.logger.info(
                            f"자동화 실행 성공: {self.name} "
                            f"(현재값: {self.value}, 상태: {self.status})"
                        )
                except Exception as e:
                    self.logger.error(f"자동화 실행 중 오류 발생: {str(e)}")

        except Exception as e:
            self.logger.error(f"환경 센서값 메시지 처리 실패: {str(e)}") 