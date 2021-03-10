import time
from datetime import datetime
from abc import *
from interfaces.Section import MachineSection


class BaseMachine:
    def __init__(self, section: MachineSection):
        self.section = section.section
        self.name = ''
        self.automation_type = ''
        self.enable = None
        self.status = None
        self.mqtt_topic = ''
        self.start = []
        self.end = []

    def set_status(self, status):
        self.status = status

    def set_mqtt(self, topic):
        self.mqtt_topic = topic

    @abstractmethod
    def set_automation(self, **kw):
        raise NotImplementedError()

    def check_machine_on(self):
        return self.status == 1


class RangeMachine(BaseMachine):
    def __init__(self, section):
        super().__init__(section=section)

    def set_automation(self, _type, enable, start, end):
        self.automation_type = _type
        self.enable = enable
        self.start = start
        self.end = end


class TemperatureRangeMachine(RangeMachine):
    def __init__(self, section):
        super().__init__(section=section)

    def check_temperature(self, temperature):
        raise NotImplementedError()

    def check_on_condition(self, temperature):
        return not self.check_machine_on() and self.check_temperature(temperature)

    def check_off_condition(self, temperature):
        return self.check_machine_on() and not self.check_temperature(temperature)


class TimeRangeMachine(RangeMachine):
    def __init__(self, section):
        super().__init__(section=section)

    def check_hour(self, current_hour):
        return self.start[0] <= current_hour < self.end[0]

    def check_on_condition(self, current_hour):
        return self.check_hour(current_hour) and not self.check_machine_on()

    def check_off_condition(self, current_hour):
        return not self.check_hour(current_hour) and self.check_machine_on()


class CycleMachine(BaseMachine):
    def __init__(self, section):
        super().__init__(section=section)
        self.term = 0

    def set_automation(self, _type, enable, start, end, term):
        self.automation_type = _type
        self.enable = enable
        self.start = start
        self.end = end
        self.term = term

    @staticmethod
    def get_hour(date):
        return int(date.split(':')[0]) if int(date.split(':')[0]) != 24 else 0

    # switch_created : db 에서 auto가 자동으로 작동한 마지막 시간
    def check_term(self, switch_created: str):
        diff = (datetime.now() - datetime.strptime(switch_created, format='YYYY-MM-DD')).days
        if diff >= self.term or diff == 0:
            return True
        else:
            return False

    def check_hour(self):
        hour = int(time.strftime('%H', time.localtime(time.time())))
        for start, end in zip(self.start, self.end):
            if self.get_hour(start) <= hour < self.get_hour(end):
                return True
        return False

    def check_on_condition(self, switch_created):
        return not self.check_machine_on() and (self.check_term(switch_created) and self.check_hour())

    def check_off_condition(self, switch_created):
        return self.check_machine_on() and not (self.check_term(switch_created) and self.check_hour())


class Machines:
    def __init__(self, section: str, machines: list):
        self.machines = machines
        self.section = section
