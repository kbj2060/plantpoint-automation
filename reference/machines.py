class LedMachine:
    def __init__(self):
        super().__init__()
        self.name = 'led'

    def __str__(self):
        return 'RangeMachine'

class FanMachine:
    def __init__(self):
        super().__init__()
        self.name = 'fan'

    def __str__(self):
        return 'IntervalMachine'

class WatersprayMachine:
    def __init__(self):
        super().__init__()
        self.name = 'waterspray'

    def __str__(self):
        return 'IntervalMachine'

class AirConditionerMachine:
    def __init__(self):
        super().__init__()
        self.name = 'airconditioner'

    def __str__(self):
        return 'TargetMachine'

class PhMachine:
    def __init__(self):
        super().__init__()
        self.name = 'ph'

    def __str__(self):
        return 'TargetMachine'

class EcMachine:
    def __init__(self):
        super().__init__()
        self.name = 'ec'

    def __str__(self):
        return 'TargetMachine'

class HumidityMachine:
    def __init__(self):
        super().__init__()
        self.name = 'humidity'

    def __str__(self):
        return 'TargetMachine'

class Co2Machine:
    def __init__(self):
        super().__init__()
        self.name = 'co2'

    def __str__(self):
        return 'TargetMachine'

class WaterTemperatureMachine:
    def __init__(self):
        super().__init__()
        self.name = 'water_temperature'

    def __str__(self):
        return 'TargetMachine'



# class HeaterMachine(TemperatureRangeMachine):
#     def __init__(self):
#         super().__init__()
#         self.name = 'heater'

#     def __str__(self):
#         return 'TemperatureRangeMachine'

#     def check_temperature(self, temperature):
#         if temperature > self.end[0]:
#             return False
#         elif temperature < self.start[0]:
#             return True
#         else:
#             return None


# class CoolerMachine(TemperatureRangeMachine):
#     def __init__(self):
#         super().__init__()
#         self.name = 'cooler'

#     def __str__(self):
#         return 'TemperatureRangeMachine'

#     def check_temperature(self, temperature):
#         if temperature > self.end[0]:
#             return True
#         elif temperature < self.start[0]:
#             return False
#         else:
#             return None