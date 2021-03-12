from art import *
from collector.machine_collector import MachineCollector
from collector.section_collector import SectionCollector
from manger.class_manager import get_machine, get_manager, get_controller
from store import Store
from resources import ws, db
from logger.custom_logger import custom_logger


banner = text2art("AUTOMATION", "larry3d")
custom_logger.log("BANNER", '\n'
                            '---------------------------------------------------------------------------------------------------------------\n'+banner)

# custom_logger.log("ON", "Here we go!")
# custom_logger.log("OFF", "Here we go!")
# custom_logger.log("STAY", "Here we go!")
machines_ref = MachineCollector().collect_machines()
sections_ref = SectionCollector().collect_sections()

for section_ref in sections_ref:
    store = Store(section_ref)
    for automation in store.automations:
        manager = get_manager(automation['automationType'])
        machine = get_machine(automation['machine'])(section=section_ref.m_section.section)
        manager(store.automations, store.switches).fit(machine)
        controller = get_controller(machine.__str__())(machine, store.environments)
        controller.control()

ws.disconnect()
db.disconnect()
