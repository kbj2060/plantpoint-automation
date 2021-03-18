from interfaces.Machine import TimeRangeMachine, TemperatureRangeMachine, CycleMachine


class LedMachine(TimeRangeMachine):
    def __init__(self, section):
        super().__init__(section=section)
        self.name = 'led'

    def __str__(self):
        return 'TimeRangeMachine'


class HeaterMachine(TemperatureRangeMachine):
    def __init__(self, section):
        super().__init__(section=section)
        self.name = 'heater'

    def __str__(self):
        return 'TemperatureRangeMachine'

    def check_temperature(self, temperature):
        if temperature >= self.end[0]:
            return False
        elif temperature <= self.start[0]:
            return True
        else:
            return None


class CoolerMachine(TemperatureRangeMachine):
    def __init__(self, section):
        super().__init__(section=section)
        self.name = 'cooler'

    def __str__(self):
        return 'TemperatureRangeMachine'

    def check_temperature(self, temperature):
        if temperature <= self.start[0]:
            return False
        elif temperature >= self.end[0]:
            return True
        else:
            return None


class FanMachine(CycleMachine):
    def __init__(self, section):
        super().__init__(section=section)
        self.name = 'fan'

    def __str__(self):
        return 'CycleMachine'


class RoofFanMachine(CycleMachine):
    def __init__(self, section):
        super().__init__(section=section)
        self.name = 'roofFan'

    def __str__(self):
        return 'CycleMachine'


class WaterPumpMachine(CycleMachine):
    def __init__(self, section):
        super().__init__(section=section)
        self.name = 'waterpump'

    def __str__(self):
        return 'CycleMachine'