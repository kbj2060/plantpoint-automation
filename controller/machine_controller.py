import time
from datetime import datetime
from statistics import mean
from constants import AUTOMATION_DISABLED_REPORT, AUTOMATION_STAY_REPORT, AUTOMATION_ON_REPORT, AUTOMATION_OFF_REPORT, ON, OFF
from handler.db_handler import DBHandler
from handler.http_handler import HttpHandler


def print_disabled(machine_name):
    print(f"{machine_name} {AUTOMATION_DISABLED_REPORT}")


def print_stay(machine_name):
    print(f"{machine_name} {AUTOMATION_STAY_REPORT}")


def print_on(machine_name):
    print(f"{machine_name} {AUTOMATION_ON_REPORT}")


def print_off(machine_name):
    print(f"{machine_name} {AUTOMATION_OFF_REPORT}")


class BaseController:
    def __init__(self, machine, environments, ws):
        self.machine = machine
        self.environments = environments
        self.ws = ws

    def check_machine_on(self) -> bool:
        return self.machine.status == 1

    def check_on_condition(self, *kwargs):
        pass

    def check_off_condition(self, *kwargs):
        pass

    def control(self, condition):
        if not self.machine.enable:
            print_disabled(self.machine.name)
        elif self.check_on_condition(condition):
            print_on(self.machine.name)
            HttpHandler().post_switch(self.machine.section, self.machine.name, ON)
            self.ws.emit_switch(self.machine.section, self.machine.name, True)
        elif self.check_off_condition(condition):
            print_off(self.machine.name)
            HttpHandler().post_switch(self.machine.section, self.machine.name, OFF)
            self.ws.emit_switch(self.machine.section, self.machine.name, False)
        else:
            print_stay(self.machine.name)


class TemperatureRangeMachineController(BaseController):
    def __init__(self, machine, environments, ws):
        super(TemperatureRangeMachineController, self).__init__(machine=machine, environments=environments, ws=ws)

    @staticmethod
    def get_avg_temp(environments):
        return mean([env['temperature'] for env in environments if env['temperature'] != 0])

    def check_on_condition(self, temperature):
        return not self.check_machine_on() and self.machine.check_temperature(temperature)

    def check_off_condition(self, temperature):
        return self.check_machine_on() and not self.machine.check_temperature(temperature)

    def control(self, condition=None):
        condition = self.get_avg_temp(self.environments)
        super().control(condition)


class TimeRangeMachineController(BaseController):
    def __init__(self, machine, environments, ws):
        super(TimeRangeMachineController, self).__init__(machine=machine, environments=environments, ws=ws)

    def check_hour(self, current_hour):
        return self.machine.start[0] <= current_hour < self.machine.end[0]

    def check_on_condition(self, current_hour):
        return self.check_hour(current_hour) and not self.check_machine_on()

    def check_off_condition(self, current_hour):
        return not self.check_hour(current_hour) and self.check_machine_on()

    def control(self, condition=None):
        condition = int(time.strftime('%H', time.localtime(time.time())))
        super().control(condition)


class BaseCycleMachineController(BaseController):
    def __init__(self, machine, environments, ws):
        super(BaseCycleMachineController, self).__init__(machine=machine, environments=environments, ws=ws)

    @staticmethod
    def get_hour(date):
        return int(date.split(':')[0]) if int(date.split(':')[0]) != 24 else 0

    def check_term(self, switch_created):
        diff = (datetime.now() - switch_created).days
        if diff >= self.machine.term or diff == 0:
            return True
        else:
            return False

    def check_hour(self):
        hour = int(time.strftime('%H', time.localtime(time.time())))
        for start, end in zip(self.machine.start, self.machine.end):
            if self.get_hour(start) <= hour < self.get_hour(end):
                return True
        return False

    def check_on_condition(self, switch_created):
        return not self.check_machine_on() and (self.check_term(switch_created) and self.check_hour())

    def check_off_condition(self, switch_created):
        return self.check_machine_on() and not (self.check_term(switch_created) and self.check_hour())

    def control(self, condition=None):
        condition = DBHandler().get_auto_created(self.machine.name)
        super().control(condition)
