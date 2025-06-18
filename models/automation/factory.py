from typing import TYPE_CHECKING, Dict, Any
from models.automation.range import RangeAutomation
from models.automation.interval import IntervalAutomation
from models.automation.target import TargetAutomation
from models.automation.base import BaseAutomation
from logger.custom_logger import custom_logger

if TYPE_CHECKING:
    from store import Store

def create_automation(automation_data: Dict[str, Any]) -> BaseAutomation:
    """
    자동화 인스턴스 생성 팩토리 메서드
    Args:
        automation_data (dict): 자동화 설정 데이터. 반드시 'device_id'와 'id' 키를 포함해야 함.
    Returns:
        BaseAutomation: 생성된 자동화 인스턴스
    Raises:
        ValueError: category가 잘못되었거나 필수 키가 없을 때
    """
    automation_types = {
        'range': RangeAutomation,
        'interval': IntervalAutomation,
        'target': TargetAutomation
    }

    device_info = automation_data.get('device_id')
    if not device_info or 'automation_type' not in device_info or 'id' not in device_info:
        raise ValueError("automation_data['device_id']에 'automation_type' 또는 'id'가 없습니다.")

    category = device_info['automation_type'].get('name')
    device_id = device_info['id']
    if not category or category not in automation_types:
        raise ValueError(f"Unknown automation category: {category}")

    # args에 device_id, category, 나머지 automation_data(불필요한 키 제거 후) 포함
    args = {
        'device_id': device_id,
        'category': category,
        **{k: v for k, v in automation_data.items() if k not in ('device_id', 'id')}
    }
    automation_class = automation_types[category]
    return automation_class(**args)