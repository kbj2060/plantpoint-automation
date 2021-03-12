from typing import List

from collector.utils import grouping
from interfaces.Machine import Machines
from logger.custom_logger import custom_logger
from manger.class_manager import get_machine
from resources import db


class MachineCollector:
    def __init__(self):
        self.grouped_machines = grouping(db.get_machines())
        self.machine_holder = list()

    def collect_machines(self) -> List[Machines]:
        try:
            for ms in self.grouped_machines.keys():
                machine_names = self.grouped_machines[ms]
                machines = [get_machine(m) for m in machine_names]
                self.machine_holder.append(Machines(m_section=ms, machines=machines))
            custom_logger.success("Collecting The Machine Information Completed!")
        except Exception:
            custom_logger.exception("Cannot Collect The Machine Information")
        return self.machine_holder
