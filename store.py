from typing import List

from interfaces.Machine import BaseMachine
from interfaces.SwitchResponse import SwitchResponse
from resources import http
from interfaces.Section import Section


class Store:
    def __init__(self, s: Section):
        self.environments = [http.get_environments(e) for e in s.e_sections]
        self.switches: List[SwitchResponse] = [SwitchResponse(machine_section=_switch['machineSection'], machine=_switch['machine'], status=_switch['status']) for _switch in http.get_switches(s.m_section)]
        self.automations = http.get_automations(s.m_section)
        self.automated_switches: List[BaseMachine] = []
