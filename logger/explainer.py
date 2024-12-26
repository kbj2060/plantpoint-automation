from typing import List

from tabulate import tabulate

from constants import ON, BOUNDARY_ERROR_MSG
from interfaces.Machine import BaseMachine
from interfaces.Response import SwitchResponse
from logger.custom_logger import custom_logger
from utils import handle_arr_length


class Explainer:
    def __init__(self, machines: List[BaseMachine], prev_machines: List[SwitchResponse], section: str):
        self.machines: List[BaseMachine] = machines
        self.prev_machines: List[SwitchResponse] = prev_machines
        self.section: str = section
        self.header = BaseMachine.get_properties() + ['remarks']
        self.table: list = []

    def logging_disabled(self):
        return ["DISABLED"]

    def logging_switch(self, automated_m: BaseMachine, before_m: SwitchResponse):
        return [f"{before_m.status == ON} -> {automated_m.status == ON}"]

    def logging_stay(self):
        return ["STAY"]

    @staticmethod
    def logging_error():
        custom_logger.error(BOUNDARY_ERROR_MSG)
        return []

    def get_automated_result(self, machine, prev_m):
        if not machine.enable:
            return self.logging_disabled()
        elif machine.status != prev_m.status:
            return self.logging_switch(automated_m=machine, before_m=prev_m)
        elif machine.status == prev_m.status:
            return self.logging_stay()
        else:
            return self.logging_error()

    def result(self):
        if len(self.machines) == 0 or len(self.prev_machines) == 0:
            custom_logger.error("No Machines Data Error")
        for machine in self.machines:
            prev_m = handle_arr_length([_switch for _switch in self.prev_machines if _switch.name == machine.name])
            self.table.append(list(vars(machine).values()) + self.get_automated_result(machine=machine, prev_m=prev_m))

        custom_logger.info(f"\n------------------Automation {self.section} Information------------------\n"
                           + tabulate(self.table, self.header, tablefmt="fancy_grid"))
