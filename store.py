from Collector.MachineCollector import MachineCollector
from Collector.SectionCollector import SectionCollector
from MachineSetter import CycleSetter
from handler.DBHandler import DBHandler
from handler.HttpHandler import HttpHandler
from interfaces.Section import Section
from pprint import pprint

from machines import WaterPumpMachine


class Store:
    def __init__(self, section: Section):
        self.httpHandler = HttpHandler()
        self.db = DBHandler()
        self.environments = [self.httpHandler.get_environments(e) for e in section.e_sections]
        self.switches = self.httpHandler.get_switches(section.m_section)
        self.automations = self.httpHandler.get_automations(section.m_section)
        self.sections = self.db.get_sections()


sections = SectionCollector().collect_sections()
machines = MachineCollector().collect_machines()
pprint(vars(machines[0]))
pprint(vars(sections[0]))
# store = Store(sections[0])
# wt = WaterPumpMachine()
# CycleSetter(store.automations, store.switches).fit(wt)
# pprint(vars(wt))
