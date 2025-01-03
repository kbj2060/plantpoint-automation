from typing import TYPE_CHECKING
from models.automation.range import RangeAutomation
from models.automation.interval import IntervalAutomation
from models.automation.target import TargetAutomation
from models.automation.base import BaseAutomation
from logger.custom_logger import custom_logger

if TYPE_CHECKING:
    from store import Store

def create_automation(automation_data: dict) -> BaseAutomation:
    """자동화 인스턴스 생성 팩토리 메서드"""
    automation_types = {
        'range': RangeAutomation,
        'interval': IntervalAutomation,
        'target': TargetAutomation
    }
    
    category = automation_data.get('category')
    automation_class = automation_types.get(category)
    if not automation_class:
        raise ValueError(f"Unknown automation category: {category}")

    return automation_class(
        device_id=automation_data.get('device_id'),
        category=category,
        active=automation_data.get('active', False),
        settings=automation_data.get('settings', {}),
        updated_at=automation_data.get('updated_at')
    ) 