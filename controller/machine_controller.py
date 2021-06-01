import time
from datetime import datetime
from statistics import mean
from constants import ON, OFF
from logger.custom_logger import custom_logger
from resources import ws, http, db


class BaseController:
    def __init__(self, machine, environments):
        self.machine = machine
        self.environments = environments

    def check_machine_on(self) -> bool:
        return self.machine.status == 1

    def check_on_condition(self, *kwargs):
        pass

    def check_off_condition(self, *kwargs):
        pass

    def control(self, condition):
        if not self.machine.enable:
            return
        elif self.check_on_condition(condition):
            self.machine.status = ON
            http.post_switch(self.machine.section, self.machine.name, ON)
            ws.emit_switch(self.machine.section, self.machine.name, True)
        elif self.check_off_condition(condition):
            self.machine.status = OFF
            http.post_switch(self.machine.section, self.machine.name, OFF)
            ws.emit_switch(self.machine.section, self.machine.name, False)
        else:
            return


class TemperatureRangeMachineController(BaseController):
    def __init__(self, machine, environments):
        super(TemperatureRangeMachineController, self).__init__(machine=machine, environments=environments)

    @staticmethod
    def get_avg_temp(environments):
        temps = [env['temperature'] for env in environments if env['temperature'] != 0]
        if len(temps) == 0:
            return 0
        else:
            return mean(temps)

    def check_on_condition(self, temperature):
        if self.machine.check_temperature(temperature) is None:
            return False
        return not self.check_machine_on() and self.machine.check_temperature(temperature)

    def check_off_condition(self, temperature):
        if self.machine.check_temperature(temperature) is None:
            return False
        return self.check_machine_on() and not self.machine.check_temperature(temperature)

    def control(self, condition=None):
        temperature = self.get_avg_temp(self.environments)
        super().control(temperature)


class TimeRangeMachineController(BaseController):
    def __init__(self, machine, environments):
        super(TimeRangeMachineController, self).__init__(machine=machine, environments=environments)

    def check_hour(self, current_hour):
        return self.machine.start[0] <= current_hour < self.machine.end[0]

    def check_on_condition(self, current_hour):
        return self.check_hour(current_hour) and not self.check_machine_on()

    def check_off_condition(self, current_hour):
        return not self.check_hour(current_hour) and self.check_machine_on()

    def control(self, condition=None):
        current_hour = int(time.strftime('%H', time.localtime(time.time())))
        super().control(current_hour)


class BaseCycleMachineController(BaseController):
    def __init__(self, machine, environments):
        super(BaseCycleMachineController, self).__init__(machine=machine, environments=environments)

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
        switch_created = db.get_auto_created(self.machine.name)
        super().control(switch_created)
