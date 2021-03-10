from abc import ABCMeta


class Environment(metaclass=ABCMeta):
    def __init__(self):
        self.value = 0


class Co2(Environment):
    def __init__(self):
        super().__init__()


class Temperature(Environment):
    def __init__(self):
        super().__init__()


class Humidity(Environment):
    def __init__(self):
        super().__init__()