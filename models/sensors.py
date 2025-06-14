import random

class PhSensor:
    def __init__(self, pin):
        self.pin = pin

    def read(self):
        # 실제 센서에서 데이터를 읽어오는 로직을 구현해야 합니다.
        # 여기서는 임의의 값을 반환합니다.
        return round(random.uniform(5.5, 7.5), 2)


class EcSensor:
    def __init__(self, pin):
        self.pin = pin

    def read(self):
        # 실제 센서에서 데이터를 읽어오는 로직을 구현해야 합니다.
        # 여기서는 임의의 값을 반환합니다.
        return round(random.uniform(1.0, 2.0), 2)


class TemperatureSensor:
    def __init__(self, pin):
        self.pin = pin

    def read(self):
        # 실제 센서에서 데이터를 읽어오는 로직을 구현해야 합니다.
        # 여기서는 임의의 값을 반환합니다.
        return round(random.uniform(20.0, 30.0), 2) 