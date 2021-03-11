import socketio

from collector.machine_collector import MachineCollector
from collector.section_collector import SectionCollector
from handler.db_handler import DBHandler
from handler.http_handler import HttpHandler
from handler.websocket_handler import WebSocketHandler
from interfaces.Section import Section
from pprint import pprint
from manger.class_manager import get_machine, get_manager, get_controller


class Store:
    httpHandler = HttpHandler()
    db = DBHandler()

    def __init__(self, s: Section):
        self.environments = [self.httpHandler.get_environments(e) for e in s.e_sections]
        self.switches = self.httpHandler.get_switches(s.m_section)
        self.automations = self.httpHandler.get_automations(s.m_section)


machines_ref = MachineCollector().collect_machines()
sections_ref = SectionCollector().collect_sections()
ws = WebSocketHandler()
db = DBHandler()

for section_ref in sections_ref:
    store = Store(section_ref)
    for automation in store.automations:
        manager = get_manager(automation['automationType'])
        machine = get_machine(automation['machine'])(section=section_ref.m_section.section)
        manager(store.automations, store.switches).fit(machine)
        controller = get_controller(machine.__str__())(machine, store.environments, ws)
        controller.control()

ws.disconnect()
db.disconnect()
