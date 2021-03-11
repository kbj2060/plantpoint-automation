from controller.machine_controller import BaseCycleMachineController, TemperatureRangeMachineController, \
    TimeRangeMachineController
from reference.envrionments import *
from manger.machine_manager import *
from reference.machines import *


def get_machine(name):
    if name == 'led':
        return LedMachine
    elif name == 'cooler':
        return CoolerMachine
    elif name == 'heater':
        return HeaterMachine
    elif name == 'waterpump':
        return WaterPumpMachine
    elif name == 'fan':
        return FanMachine
    elif name == 'roofFan':
        return RoofFanMachine
    else:
        raise ValueError()


def get_environment(name):
    if name == 'temperature':
        return Temperature
    elif name == 'co2':
        return Co2
    elif name == 'humidity':
        return Humidity
    else:
        raise ValueError()


def get_manager(_type):
    if _type == 'cycle':
        return CycleManager
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
