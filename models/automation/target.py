from typing import Optional
from models.automation.base import BaseAutomation
from models.Machine import BaseMachine
from models.automation.models import MQTTMessage, MQTTPayloadData, MessageHandler, SwitchMessage, TopicType
from datetime import datetime
class TargetAutomation(BaseAutomation):
    def __init__(self, device_id: str, category: str, active: bool, target: float, margin: float,
                 increase_device_id: Optional[int] = None, decrease_device_id: Optional[int] = None,
                 updated_at: str = None):
        self.settings = {
            'target': target,
            'margin': margin,
            'increase_device_id': increase_device_id,
            'decrease_device_id': decrease_device_id
        }
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
            self.increase_device_id = settings.get('increase_device_id')  # 값을 올리는 장치 (heater)
            self.decrease_device_id = settings.get('decrease_device_id')  # 값을 내리는 장치 (cooler)
            self.in_range_count = 0  # 초기화 시점에 0으로 설정
            self.required_count = 3  # 필요한 연속 카운트 수는 3
            self.value = None
            self.increase_device = None  # Store에서 찾은 increase 장치
            self.decrease_device = None  # Store에서 찾은 decrease 장치
            self.led_time_range = None  # LED 시간 범위 설정
            # self.logger.info(f"Target 자동화 설정 초기화: target={self.target}, margin={self.margin}")
        except (TypeError, ValueError) as e:
            self.target = None
            self.margin = None
            self.logger.warning("Target 자동화 설정이 비어있습니다.")

    def _load_control_devices(self, store):
        """Store에서 increase/decrease 장치 찾기 및 LED range automation 설정 로드"""
        if self.increase_device_id:
            self.increase_device = next(
                (m for m in store.machines if m.machine_id == self.increase_device_id),
                None
            )
        if self.decrease_device_id:
            self.decrease_device = next(
                (m for m in store.machines if m.machine_id == self.decrease_device_id),
                None
            )

        # LED의 range automation 설정 찾기
        led_device = next((m for m in store.machines if m.name == 'led'), None)
        if led_device:
            # Store에서 LED의 automation 설정 찾기
            led_automation = next(
                (auto for auto in store.automations if auto.get('device_id', {}).get('name') == 'led'),
                None
            )

            if led_automation:
                self.led_time_range = {
                    'start_time': led_automation.get('start_time'),
                    'end_time': led_automation.get('end_time'),
                    'active': led_automation.get('active', False)
                }
            else:
                self.led_time_range = None
                self.logger.warning(f"Device {self.name}: LED automation 설정을 찾을 수 없습니다.")
        else:
            self.led_time_range = None
            self.logger.warning(f"Device {self.name}: LED 장치를 찾을 수 없습니다.")

    def _is_led_on(self) -> bool:
        """현재 시간이 LED 시간 범위 내에 있는지 판단

        Returns:
            bool: LED가 ON 상태여야 하면 True, 아니면 False
        """
        # LED 시간 범위 설정이 없거나 비활성화된 경우
        if not self.led_time_range or not self.led_time_range.get('active'):
            return False

        try:
            now = datetime.now()
            current_time = now.strftime('%H:%M')

            start_time = self.led_time_range.get('start_time')
            end_time = self.led_time_range.get('end_time')

            if not start_time or not end_time:
                return False

            # 시간 비교
            # 예: start_time='06:00', end_time='18:00', current_time='12:30'
            # 정상적인 경우: start <= current < end
            if start_time <= end_time:
                # 같은 날 범위 (예: 06:00 ~ 18:00)
                return start_time <= current_time < end_time
            else:
                # 자정을 넘는 범위 (예: 22:00 ~ 06:00)
                return current_time >= start_time or current_time < end_time

        except Exception as e:
            self.logger.error(f"LED 시간 범위 판단 실패: {str(e)}")
            return False

    def _calculate_effective_target(self) -> float:
        """LED 시간 범위에 따라 유효 목표값 계산

        Returns:
            float: 계산된 유효 목표값
                - LED 시간 범위 내 (ON): 데이터베이스의 target 값 사용
                - LED 시간 범위 외 (OFF): target - 5
                - LED 설정 없음: target 사용 (안전 모드)
        """
        if not self.led_time_range:
            # LED 시간 범위 설정이 없는 경우 기본 target 사용
            return self.target

        if self._is_led_on():
            # LED 시간 범위 내 (ON): 데이터베이스의 target 값 사용
            return self.target
        else:
            # LED 시간 범위 외 (OFF): target - 5
            return self.target - 5

    def control(self) -> Optional[BaseMachine]:
        """목표값 기반 제어 실행 (cooler/heater 구분)"""
        if not super().control():
            return None

        if not all([self.target is not None, self.margin is not None]):
            self.logger.error(f"Sensor {self.name}: 필수 설정이 누락되었습니다.")
            raise ValueError(f"Sensor {self.name}: 필수 설정이 누락되었습니다.")

        if self.value is None:
            # 센서값이 없으면 제어하지 않고 종료
            self.logger.debug(f"Sensor {self.name}: 센서값이 없어 제어하지 않습니다.")
            return None

        try:
            # LED 상태에 따라 동적으로 target 계산
            effective_target = self._calculate_effective_target()

            lower_bound = effective_target - self.margin
            upper_bound = effective_target + self.margin

            # 현재 온도가 목표보다 낮음 -> 값을 올려야 함 (heater)
            if self.value < lower_bound:
                # increase 장치 켜기 (heater)
                if self.increase_device:
                    self._turn_on_device(self.increase_device)
                    led_on = self._is_led_on()
                    self.logger.info(
                        f"Sensor {self.name}: {self.increase_device.name} ON "
                        f"(현재값: {self.value}, 유효목표: {effective_target}, LED: {'ON' if led_on else 'OFF'})"
                    )

                # decrease 장치 끄기 (cooler)
                if self.decrease_device:
                    self._turn_off_device(self.decrease_device)

                self.in_range_count = 0

            # 현재 온도가 목표보다 높음 -> 값을 내려야 함 (cooler)
            elif self.value > upper_bound:
                # decrease 장치 켜기 (cooler)
                if self.decrease_device:
                    self._turn_on_device(self.decrease_device)
                    led_on = self._is_led_on()
                    self.logger.info(
                        f"Sensor {self.name}: {self.decrease_device.name} ON "
                        f"(현재값: {self.value}, 유효목표: {effective_target}, LED: {'ON' if led_on else 'OFF'})"
                    )

                # increase 장치 끄기 (heater)
                if self.increase_device:
                    self._turn_off_device(self.increase_device)

                self.in_range_count = 0

            else:
                # 적정 범위 내
                led_on = self._is_led_on()
                if self.in_range_count < self.required_count:
                    self.in_range_count += 1
                    self.logger.info(
                        f"Sensor {self.name}: 목표값 범위 내 "
                        f"(연속 카운트: {self.in_range_count}/{self.required_count}, "
                        f"현재값: {self.value}, 유효목표: {effective_target}, LED: {'ON' if led_on else 'OFF'})"
                    )

                # 연속 카운트 도달 -> 모든 장치 끄기
                if self.in_range_count >= self.required_count:
                    if self.increase_device:
                        self._turn_off_device(self.increase_device)
                    if self.decrease_device:
                        self._turn_off_device(self.decrease_device)

                    self.logger.info(
                        f"Sensor {self.name}: 목표값 {self.required_count}회 연속 도달로 모든 장치 OFF "
                        f"(현재값: {self.value}, 유효목표: {effective_target}, LED: {'ON' if led_on else 'OFF'})"
                    )
                    self.in_range_count = 0

            return None

        except Exception as e:
            self.logger.error(f"Sensor {self.name} 제어 중 오류 발생: {str(e)}")
            raise

    def _turn_on_device(self, device):
        """장치 켜기"""
        if not device.status:
            device.update_status(True)

    def _turn_off_device(self, device):
        """장치 끄기"""
        if device.status:
            device.update_status(False) 

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

                # 자동화가 활성화되어 있을 때만 제어 실행
                if self.active:
                    try:
                        controlled_machine = self.control()
                        if controlled_machine:
                            self.logger.info(
                                f"자동화 실행 성공: {self.name} "
                                f"(현재값: {self.value}, 상태: {self.status})"
                            )
                    except Exception as e:
                        self.logger.error(f"자동화 실행 중 오류 발생: {str(e)}")
                else:
                    self.logger.debug(f"Device {self.name}: 자동화 비활성화 상태 - 제어 건너뛰기")

        except Exception as e:
            self.logger.error(f"환경 센서값 메시지 처리 실패: {str(e)}") 