from envrionments import *
from machine_manager import *
from machines import *


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


def get_environment(name):
    if name == 'temperature':
        return Temperature
    elif name == 'co2':
        return Co2
    elif name == 'humidity':
        return Humidity


def get_manager(_type):
    if _type == 'cycle':
        return CycleManager
    elif _type == 'range':
        return RangeManager
