
from resources import http
from interfaces.Section import Section


class Store:
    def __init__(self, s: Section):
        self.environments = [http.get_environments(e) for e in s.e_sections]
        self.switches = http.get_switches(s.m_section)
        self.automations = http.get_automations(s.m_section)

