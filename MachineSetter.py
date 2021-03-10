from abc import abstractmethod
from interfaces.Machine import BaseMachine


def handle_arr_length(arr):
    if len(arr) != 1:
        raise ValueError()
    else:
        return arr[0]


class BaseMachineSetter:
    def __init__(self, automations, switches):
        self.switches = switches
        self.automations = automations

    @staticmethod
    def set_mqtt(machine: BaseMachine):
        machine.set_mqtt(topic=f"switch/{machine.section}/{machine.name}")

    @abstractmethod
    def set_automation(self, machine: BaseMachine):
        raise NotImplementedError()

    def set_status(self, machine: BaseMachine):
        status = handle_arr_length(
            [x['status'] for x in self.switches if x['machine'] == machine.name]
        )
        machine.set_status(status=status)

    def fit(self, machine: BaseMachine):
        self.set_automation(machine)
        self.set_mqtt(machine)
        self.set_status(machine)


class RangeSetter(BaseMachineSetter):
    def __init__(self, automations, switches):
        super().__init__(automations=automations, switches=switches)

    def set_automation(self, machine: BaseMachine):
        automation = handle_arr_length(
            [x for x in self.automations if x['machine'] == machine.name]
        )

        machine.set_automation(
            _type=automation['automationType'],
            enable=automation['enable'],
            start=automation['start'],
            end=automation['end'],
        )


class CycleSetter(BaseMachineSetter):
    def __init__(self, automations, switches):
        super().__init__(automations=automations, switches=switches)

    def set_automation(self, machine: BaseMachine):
        automation = handle_arr_length(
            [x for x in self.automations if x['machine'] == machine.name]
        )

        machine.set_automation(
            _type=automation['automationType'],
            enable=automation['enable'],
            start=automation['start'],
            end=automation['end'],
            term=automation['term'],
        )
