import logger.banner
from collector.machine_collector import MachineCollector
from collector.section_collector import SectionCollector
from constants import ON
from logger.custom_logger import custom_logger
from logger.explainer import Explainer
from manger.class_manager import get_machine, get_manager, get_controller
from store import Store
from resources import ws, db


if __name__ == '__main__':
    machines_ref = MachineCollector().collect_machines()
    sections_ref = SectionCollector().collect_sections()

    for section_ref in sections_ref:
        store = Store(section_ref)

        for automation in store.automations:
            machine = get_machine(automation['machine'])(section=section_ref.m_section.section)
            manager = get_manager(automation['automationType'])
            manager(store.automations, store.switches).fit(machine)
            controller = get_controller(machine.__str__())(machine, store.environments)
            controller.control()
            store.machines.append(machine)

        explainer = Explainer(machines=store.machines, prev_machines=store.switches, section=section_ref.m_section.section)
        explainer.explain_automation()
        explainer.explain_switch()

    ws.disconnect()
    db.disconnect()
