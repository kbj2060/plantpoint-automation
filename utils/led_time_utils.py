"""LED 자동화 시간 범위 체크 유틸리티"""
from datetime import datetime
from typing import Optional, Dict
import logging

logger = logging.getLogger(__name__)


def load_led_time_range(store, device_name: str) -> Optional[Dict]:
    """Store에서 LED의 range automation 설정 찾기

    Args:
        store: Store 객체
        device_name: 디바이스 이름 (로깅용)

    Returns:
        Dict: LED 시간 범위 설정 {'start_time', 'end_time', 'active'}
        None: LED 설정을 찾을 수 없는 경우
    """
    # LED 장치 찾기
    led_device = next((m for m in store.machines if m.name == 'led'), None)
    if not led_device:
        logger.warning(f"Device {device_name}: LED 장치를 찾을 수 없습니다.")
        return None

    # Store에서 LED의 automation 설정 찾기
    led_automation = next(
        (auto for auto in store.automations if auto.get('device_id', {}).get('name') == 'led'),
        None
    )

    if not led_automation:
        logger.warning(f"Device {device_name}: LED automation 설정을 찾을 수 없습니다.")
        return None

    return {
        'start_time': led_automation.get('start_time'),
        'end_time': led_automation.get('end_time'),
        'active': led_automation.get('active', False)
    }


def is_led_on(led_time_range: Optional[Dict]) -> bool:
    """현재 시간이 LED 시간 범위 내에 있는지 판단

    Args:
        led_time_range: LED 시간 범위 설정 {'start_time', 'end_time', 'active'}

    Returns:
        bool: LED가 ON 상태여야 하면 True, 아니면 False
    """
    # LED 시간 범위 설정이 없거나 비활성화된 경우
    if not led_time_range or not led_time_range.get('active'):
        return False

    try:
        now = datetime.now()
        current_time = now.strftime('%H:%M')

        start_time = led_time_range.get('start_time')
        end_time = led_time_range.get('end_time')

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
        logger.error(f"LED 시간 범위 판단 실패: {str(e)}")
        return False


def calculate_effective_target(target: float, led_time_range: Optional[Dict], offset: float = 5.0) -> float:
    """LED 시간 범위에 따라 유효 목표값 계산

    Args:
        target: 기본 목표값
        led_time_range: LED 시간 범위 설정
        offset: LED OFF 시 목표값에서 뺄 값 (기본값: 5.0)

    Returns:
        float: 계산된 유효 목표값
            - LED 시간 범위 내 (ON): target 값 사용
            - LED 시간 범위 외 (OFF): target - offset
            - LED 설정 없음: target 사용 (안전 모드)
    """
    if not led_time_range:
        # LED 시간 범위 설정이 없는 경우 기본 target 사용
        return target

    if is_led_on(led_time_range):
        # LED 시간 범위 내 (ON): target 값 사용
        return target
    else:
        # LED 시간 범위 외 (OFF): target - offset
        return target - offset
