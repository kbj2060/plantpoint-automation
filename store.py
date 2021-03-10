from collector.MachineCollector import MachineCollector
from collector.SectionCollector import SectionCollector
from handler.DBHandler import DBHandler
from handler.HttpHandler import HttpHandler
from interfaces.Section import Section
from pprint import pprint
from manger.ClassManager import get_machine, get_manager


class Store:
    httpHandler = HttpHandler()
    db = DBHandler()

    def __init__(self, s: Section):
        self.environments = [self.httpHandler.get_environments(e) for e in s.e_sections]
        self.switches = self.httpHandler.get_switches(s.m_section)
        self.automations = self.httpHandler.get_automations(s.m_section)


sections = SectionCollector().collect_sections()
machines = MachineCollector().collect_machines()

for section in sections:
    store = Store(section)
    for automation in store.automations:
        manager = get_manager(automation['automationType'])
        machine = get_machine(automation['machine'])(section=section.m_section)
        manager(store.automations, store.switches).fit(machine)
        pprint(vars(machine))
