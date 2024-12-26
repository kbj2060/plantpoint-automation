from controller.machine_controller import BaseCycleMachineController, TemperatureRangeMachineController, \
    TimeRangeMachineController
from reference.envrionments import *
from reference.machines import *
from interfaces.Machine import BaseMachine


def get_machine(machine: BaseMachine):
    name = machine.name
    if name == 'led':
        return LedMachine
    elif name == 'airconditioner':
        return AirConditionerMachine
    elif name == 'waterpump':
        return WatersprayMachine
    elif name == 'fan':
        return FanMachine
    elif name == 'ph':
        return PhMachine
    elif name == 'ec':
        return EcMachine
    elif name == 'humidity':
        return HumidityMachine
    elif name == 'co2':
        return Co2Machine
    elif name == 'water_temperature':
        return WaterTemperatureMachine
    else:
        raise ValueError()

# def get_sensor(name: str) -> BaseSensor:
#     if name == 'ph':
#         return PhSensor
#     elif name == 'ec':
#         return EcSensor
#     elif name == 'temperature':
#         return TemperatureSensor
#     elif name == 'humidity':
#         return HumiditySensor
#     elif name == 'co2':
#         return Co2Sensor
#     elif name == 'water_temperature':
#         return WaterTemperatureSensor
#     else:
#         raise ValueError()


def get_environment(name):
    if name == 'temperature':
        return Temperature
    elif name == 'co2':
        return Co2
    elif name == 'humidity':
        return Humidity
    else:
        raise ValueError()


def get_automation_manager(automation):
    _type = automation['automations_category']
    if _type == 'interval':
        return IntervalManager
    elif _type == 'target':
        return TargetManager
    elif _type == 'range':
        return RangeManager
    else:
        raise ValueError()


def get_controller(_type):
    if _type == 'CycleMachine':
        return BaseCycleMachineController
    elif _type == 'TemperatureRangeMachine':
        return TemperatureRangeMachineController
    elif _type == 'TimeRangeMachine':
        return TimeRangeMachineController
    else:
        raise ValueError()
