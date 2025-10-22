"""Current Monitor Manager for detecting mismatches between current sensor and switch status."""

from typing import Dict
from logger.custom_logger import custom_logger
from store import Store
from resources import mqtt
from resources.redis import redis_client


class CurrentMonitorManager:
    """Monitors current sensor values and compares them with switch status."""

    def __init__(self, store: Store):
        """
        Initialize CurrentMonitorManager.

        Args:
            store: Store instance containing device data
        """
        self.store = store
        self.last_warnings: Dict[str, bool] = {}  # Track last warning state to avoid spam
        self.mismatch_counts: Dict[str, int] = {}  # Track consecutive mismatch counts
        self.max_mismatch_count = 3  # 3번 연속 불일치 시 동기화
        custom_logger.info("CurrentMonitorManager 초기화 완료")

    def check_current_mismatch(self) -> None:
        """
        Check for mismatches between current sensor values and switch status.

        Logs warnings and publishes MQTT switch messages to sync status after 3 consecutive mismatches.
        """
        try:
            # Redis에서 개별 current와 switch 값을 가져옴
            # 형식: switch/<device_name> = "true" 또는 "false"
            #      current/<device_name> = "true" 또는 "false"

            # Store의 machines로부터 디바이스 목록 가져오기
            for machine in self.store.machines:
                device_name = machine.name

                # Redis에서 current 값 가져오기 (redis_client.get()는 직접 문자열 반환)
                current_key = f"current/{device_name}"
                current_str = redis_client.get(current_key)

                if current_str is None:
                    # current 센서가 없는 디바이스는 건너뜀
                    continue

                # 문자열을 boolean으로 변환
                current_value = current_str.lower() == 'true'

                # Redis에서 switch 상태 가져오기
                switch_key = f"switch/{device_name}"
                switch_str = redis_client.get(switch_key)

                # switch 값이 없으면 기본값 False 사용
                switch_value = switch_str.lower() == 'true' if switch_str else False

                # current 값과 switch 상태 비교
                if current_value != switch_value:
                    # 불일치 카운트 증가
                    if device_name not in self.mismatch_counts:
                        self.mismatch_counts[device_name] = 1
                    else:
                        self.mismatch_counts[device_name] += 1

                    mismatch_count = self.mismatch_counts[device_name]

                    # 첫 불일치 감지 시 로그
                    if mismatch_count == 1:
                        custom_logger.warning(
                            f"⚠️  전류 센서와 스위치 상태 불일치 감지 (1/{self.max_mismatch_count})\n"
                            f"   기기: {device_name}\n"
                            f"   전류 센서: {'ON (전류 감지됨)' if current_value else 'OFF (전류 없음)'}\n"
                            f"   스위치 상태: {'ON' if switch_value else 'OFF'}"
                        )
                    # 2번째 불일치
                    elif mismatch_count == 2:
                        custom_logger.warning(
                            f"⚠️  전류 센서와 스위치 상태 불일치 계속됨 (2/{self.max_mismatch_count})\n"
                            f"   기기: {device_name}"
                        )
                    # 3번째 불일치 시 동기화
                    elif mismatch_count >= self.max_mismatch_count:
                        custom_logger.warning(
                            f"🔄 전류 센서와 스위치 상태 불일치 {self.max_mismatch_count}번 연속 감지!\n"
                            f"   기기: {device_name}\n"
                            f"   전류 센서: {'ON (전류 감지됨)' if current_value else 'OFF (전류 없음)'}\n"
                            f"   스위치 상태: {'ON' if switch_value else 'OFF'}\n"
                            f"   → 스위치 상태를 전류 센서 값에 맞게 동기화합니다."
                        )
                        # switch 상태를 current 값에 맞게 동기화
                        self._sync_switch_status(machine, current_value)
                        # 카운트 초기화
                        self.mismatch_counts[device_name] = 0
                        self.last_warnings[device_name] = current_value
                else:
                    # 상태가 일치하면 카운트 초기화
                    if device_name in self.mismatch_counts:
                        # 불일치 카운트가 있었다면 일치 로그 출력
                        if self.mismatch_counts[device_name] > 0:
                            custom_logger.info(
                                f"✓ 전류 센서와 스위치 상태 일치 확인: {device_name}"
                            )
                        del self.mismatch_counts[device_name]
                    if device_name in self.last_warnings:
                        del self.last_warnings[device_name]

        except Exception as e:
            custom_logger.error(f"전류 센서 모니터링 중 오류 발생: {str(e)}")

    def _sync_switch_status(self, machine, target_status: bool) -> None:
        """
        Sync switch status with current sensor value by publishing MQTT message.

        Args:
            machine: BaseMachine object
            target_status: Target status from current sensor (True=ON, False=OFF)
        """
        try:
            # machine.mqtt_topic은 이미 "switch/{name}" 형식
            topic = machine.mqtt_topic

            # MQTT payload 형식: {"pattern":"switch/{name}","data":{"name":"device","value":bool}}
            payload = {
                "pattern": topic,
                "data": {
                    "name": machine.name,
                    "value": target_status  # boolean 값 사용
                }
            }

            if mqtt.publish_message(topic, payload):
                custom_logger.info(
                    f"✓ 스위치 동기화 MQTT 발행 성공: {machine.name} → "
                    f"{'ON' if target_status else 'OFF'}"
                )
                # 로컬 machine 상태도 업데이트 (1 for ON, 0 for OFF)
                machine.set_status(1 if target_status else 0)
            else:
                custom_logger.error(
                    f"✗ 스위치 동기화 MQTT 발행 실패: {machine.name}"
                )

        except Exception as e:
            custom_logger.error(
                f"스위치 동기화 중 오류 발생 ({machine.name}): {str(e)}"
            )

    def run(self) -> None:
        """Run current monitoring check."""
        self.check_current_mismatch()
