from abc import ABCMeta


class Environment(metaclass=ABCMeta):
    def __init__(self):
        self.value = 0

    def set_value(self, value):
        self.value = value


class Environments:
    def __init__(self, section: str, environments: list):
        self.environments = environments
        self.section = section
