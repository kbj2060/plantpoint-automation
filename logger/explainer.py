from typing import List

from constants import ON, BOUNDARY_ERROR_MSG
from interfaces.Machine import BaseMachine
from interfaces.SwitchResponse import SwitchResponse
from logger.custom_logger import custom_logger
from utils import handle_arr_length


class Explainer:
    def __init__(self, machines: List[BaseMachine], prev_machines: List[SwitchResponse], section: str):
        self.machines: List[BaseMachine] = machines
        self.prev_machines: List[SwitchResponse] = prev_machines
        self.section = section

    @staticmethod
    def logging_disabled(automated_m: BaseMachine):
        custom_logger.log(
            "DISABLED",
            f"Section: {automated_m.section:3} | Machine: {automated_m.name.upper():10} | Status: DISABLED"
        )

    @staticmethod
    def logging_switch(automated_m: BaseMachine, before_m: SwitchResponse):
        custom_logger.log(
            "SWITCH",
            f"Section: {automated_m.section:3} | Machine: {automated_m.name.upper():10} | Status: {before_m.status == ON} -> {automated_m.status == ON}"
        )

    @staticmethod
    def logging_stay(automated_m: BaseMachine):
        custom_logger.log(
            "STAY",
            f"Section: {automated_m.section:3} | Machine: {automated_m.name.upper():10} | Status: STAY"
        )

    @staticmethod
    def logging_cycle(automated_m: BaseMachine):
        custom_logger.info(
            f"Section: {automated_m.section:3} | Machine: {automated_m.name.upper():10} | Status: {automated_m.status == ON} "
            f"| Start: {automated_m.start}시 | End: {automated_m.end}시 | Term: {automated_m.term}일"
        )

    @staticmethod
    def logging_time_range(automated_m: BaseMachine):
        custom_logger.info(
            f"Section: {automated_m.section:3} | Machine: {automated_m.name.upper():10} | Status: {automated_m.status == ON} "
            f"| Start: {automated_m.start}시 | End: {automated_m.end}시"
        )

    @staticmethod
    def logging_temp_range(automated_m: BaseMachine):
        custom_logger.info(
            f"Section: {automated_m.section:3} | Machine: {automated_m.name.upper():10} | Status: {automated_m.status == ON} "
            f"| Start: {automated_m.start}°C | End: {automated_m.end}°C"
        )

    @staticmethod
    def logging_error():
        custom_logger.error(BOUNDARY_ERROR_MSG)

    def explain_automation(self):
        custom_logger.info(f"------------------Automation {self.section} Information------------------")
        for machine in self.machines:
            if machine.__str__() == "CycleMachine":
                self.logging_cycle(machine)
            elif machine.__str__() == "TemperatureRangeMachine":
                self.logging_temp_range(machine)
            elif machine.__str__() == "TimeRangeMachine":
                self.logging_time_range(machine)
            else:
                self.logging_error()

    def explain_switch(self):
        custom_logger.info(f"-------------------Switches {self.section} Information-------------------")
        for automated_m in self.machines:
            before_m = handle_arr_length([_switch for _switch in self.prev_machines if _switch.name == automated_m.name])

            if not automated_m.enable:
                self.logging_disabled(automated_m=automated_m)
            elif automated_m.status != before_m.status:
                self.logging_switch(automated_m=automated_m, before_m=before_m)
            elif automated_m.status == before_m.status:
                self.logging_stay(automated_m=automated_m)
            else:
                self.logging_error()

        custom_logger.info("-------------------------------------------------------------")
