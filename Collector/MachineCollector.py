from typing import List

from Collector.utils import grouping
from handler.DBHandler import DBHandler
from interfaces.Machine import Machines
from machines import *


class MachineCollector:
    def __init__(self):
        self.db = DBHandler()
        self.grouped_machines = grouping(self.db.get_machines())
        self.machine_holder = list()

    @staticmethod
    def get_machine(name):
        if name == 'led':
            return LedMachine
        elif name == 'cooler':
            return CoolerMachine
        elif name == 'heater':
            return HeaterMachine
        elif name == 'waterpump':
            return WaterPumpMachine
        elif name == 'fan':
            return FanMachine
        elif name == 'roofFan':
            return RoofFanMachine

    def collect_machines(self):
        for ms in self.grouped_machines.keys():
            machine_names = self.grouped_machines[ms]
            machines = [self.get_machine(m) for m in machine_names]
            self.machine_holder.append(Machines(section=ms, machines=machines))
        return self.machine_holder
