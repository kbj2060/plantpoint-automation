from typing import List

from collector.utils import grouping
from handler.DBHandler import DBHandler
from interfaces.Machine import Machines
from manger.ClassManager import get_machine


class MachineCollector:
    def __init__(self):
        self.db = DBHandler()
        self.grouped_machines = grouping(self.db.get_machines())
        self.machine_holder = list()

    def collect_machines(self) -> List[Machines]:
        for ms in self.grouped_machines.keys():
            machine_names = self.grouped_machines[ms]
            machines = [get_machine(m) for m in machine_names]
            self.machine_holder.append(Machines(section=ms, machines=machines))
        return self.machine_holder
