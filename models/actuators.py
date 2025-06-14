import time

class MagneticFan:
    def __init__(self, pin):
        self.pin = pin

    def start(self):
        # 팬을 시작하는 로직을 구현해야 합니다.
        print(f"Magnetic Fan on pin {self.pin} started.")

    def stop(self):
        # 팬을 멈추는 로직을 구현해야 합니다.
        print(f"Magnetic Fan on pin {self.pin} stopped.")


class DosingPump:
    def __init__(self, pin):
        self.pin = pin

    def add_ph_up(self):
        # pH 상승 용액을 추가하는 로직을 구현해야 합니다.
        print(f"Dosing Pump on pin {self.pin} adding pH up solution.")
        time.sleep(1)  # 실제 동작 시간

    def add_ph_down(self):
        # pH 하강 용액을 추가하는 로직을 구현해야 합니다.
        print(f"Dosing Pump on pin {self.pin} adding pH down solution.")
        time.sleep(1)  # 실제 동작 시간

    def add_nutrient_solution(self):
        # 영양소 용액을 추가하는 로직을 구현해야 합니다.
        print(f"Dosing Pump on pin {self.pin} adding nutrient solution.")
        time.sleep(1)  # 실제 동작 시간

    def stop_all(self):
        # 모든 펌프를 멈추는 로직을 구현해야 합니다.
        print(f"Dosing Pump on pin {self.pin} stopped.") 