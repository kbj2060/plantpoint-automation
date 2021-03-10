from abc import ABCMeta, abstractmethod

from handler.DBHandler import DBHandler
from handler.HttpHandler import HttpHandler
from pprint import pprint
from interfaces.Machine import Machine
from machines import WaterPumpMachine


def handle_arr_length(arr):
    if len(arr) != 1:
        raise ValueError()
    else:
        return arr[0]


class Store:
    def __init__(self, machine_section: str):
        self.httpHandler = HttpHandler()
        self.db = DBHandler()
        self.environments = self.httpHandler.get_environments(machine_section)
        self.switches = self.httpHandler.get_switches(machine_section)
        self.automations = self.httpHandler.get_automations(machine_section)
        self.sections = self.db.get_sections()


class BaseMachineCollector(metaclass=ABCMeta):
    def __init__(self, automations, switches):
        self.switches = switches
        self.automations = automations

    @staticmethod
    def set_mqtt(machine: Machine):
        machine.set_mqtt(topic=f"switch/{machine.section}/{machine.name}")

    @abstractmethod
    def set_automation(self, machine: Machine):
        raise NotImplementedError()

    def set_status(self, machine: Machine):
        status = handle_arr_length(
            [x['status'] for x in self.switches if x['machine'] == machine.name]
        )
        machine.set_status(status=status)

    def fit(self, machine: Machine):
        self.set_automation(machine)
        self.set_mqtt(machine)
        self.set_status(machine)


class RangeCollector(BaseMachineCollector):
    def __init__(self, automations, switches):
        super().__init__(automations=automations, switches=switches)
        # super(RangeCollector, self).__init__(automations=automations, switches=switches)

    def set_automation(self, machine: Machine):
        automation = handle_arr_length(
            [x for x in self.automations if x['machine'] == machine.name]
        )

        machine.set_automation(
            _type=automation['automationType'],
            section=automation['machineSection'],
            enable=automation['enable'],
            start=automation['start'],
            end=automation['end'],
        )


class CycleCollector(BaseMachineCollector):
    def __init__(self, automations, switches):
        super().__init__(automations=automations, switches=switches)

    def set_automation(self, machine: Machine):
        automation = handle_arr_length(
            [x for x in self.automations if x['machine'] == machine.name]
        )

        machine.set_automation(
            _type=automation['automationType'],
            section=automation['machineSection'],
            enable=automation['enable'],
            start=automation['start'],
            end=automation['end'],
            term=automation['term'],
        )


store = Store('s1')
wt = WaterPumpMachine()
CycleCollector(store.automations, store.switches).fit(wt)
pprint(vars(wt))
