from interfaces.automation.base import BaseAutomation
from interfaces.automation.range import RangeAutomation
from interfaces.automation.interval import IntervalAutomation
from interfaces.automation.target import TargetAutomation
from interfaces.automation.factory import create_automation

__all__ = [
    'BaseAutomation',
    'RangeAutomation',
    'IntervalAutomation',
    'TargetAutomation',
    'create_automation'
] 