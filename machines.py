from interfaces.Machine import TimeRangeMachine, TemperatureRangeMachine, CycleMachine


class LedMachine(TimeRangeMachine):
    def __init__(self):
        super().__init__()
        self.name = 'led'


class HeaterMachine(TemperatureRangeMachine):
    def __init__(self):
        super().__init__()
        self.name = 'heater'

    def check_temperature(self, temperature):
        if temperature > self.end[0]:
            return False
        elif temperature < self.start[0]:
            return True
        else:
            return None


class CoolerMachine(TemperatureRangeMachine):
    def __init__(self):
        super().__init__()
        self.name = 'cooler'

    def check_temperature(self, temperature):
        if temperature < self.start[0]:
            return False
        elif temperature > self.end[0]:
            return True
        else:
            return None


class FanMachine(CycleMachine):
    def __init__(self):
        super().__init__()
        self.name = 'fan'


class RoofFanMachine(CycleMachine):
    def __init__(self):
        super().__init__()
        self.name = 'roofFan'


class WaterPumpMachine(CycleMachine):
    def __init__(self):
        super().__init__()
        self.name = 'waterpump'
