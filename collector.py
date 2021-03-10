from handler.HttpHandler import HttpHandler
from interfaces import Machine
from pprint import pprint


class Collector:
    def __init__(self, machine_section: str):
        self.httpHandler = HttpHandler()
        self.environments = self.httpHandler.get_environments(machine_section)
        self.switches = self.httpHandler.get_switches(machine_section)
        self.automations = self.httpHandler.get_automations(machine_section)


class LedCollector:
    def __init__(self, automations, switches):
        self.switches = switches
        self.automations = automations

    @staticmethod
    def handle_arr_length(arr):
        if len(arr) != 1:
            raise ValueError()
        else:
            return arr[0]

    def set_automation(self, machine: Machine.LEDMachine):
        automation = self.handle_arr_length(
            [x for x in self.automations if x['machine'] == machine.machine_name]
        )

        machine.set_automation(
            _type=automation['automationType'],
            section=automation['machineSection'],
            enable=automation['enable'],
            start=automation['start'],
            end=automation['end'],
        )

    def set_status(self, machine: Machine.LEDMachine):
        status = self.handle_arr_length(
            [x['status'] for x in self.switches if x['machine'] == machine.machine_name]
        )
        machine.set_status(status=status)

    def fit(self, machine: Machine.LEDMachine):
        self.set_automation(machine)
        self.set_status(machine)


store = Collector('s1')
led = Machine.LEDMachine()
LedCollector(store.automations, store.switches).fit(led)
pprint(vars(led))
