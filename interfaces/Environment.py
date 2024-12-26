from abc import ABCMeta


class Environment(metaclass=ABCMeta):
    def __init__(self):
        self.value = 0

    def set_value(self, value):
        self.value = value

class Co2(Environment):
    def __init__(self):
        super().__init__()


class Temperature(Environment):
    def __init__(self):
        super().__init__()


class Humidity(Environment):
    def __init__(self):
        super().__init__()


class Ph(Environment):
    def __init__(self):
        super().__init__()

class EC(Environment):
    def __init__(self):
        super().__init__()

class WaterTemperature(Environment):
    def __init__(self):
        super().__init__()
        
class Environments:
    def __init__(self, environments: list):
        self.environments = environments
