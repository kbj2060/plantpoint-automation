import time
import threading
from logger.custom_logger import custom_logger
from sensors import PhSensor, EcSensor, TemperatureSensor
from actuators import MagneticFan, DosingPump
from managers.thread_manager import ThreadManager
import sys

if sys.platform != "linux":
    from fake_rpi.RPi import GPIO
else:
    import RPi.GPIO as GPIO

class NutrientManager:
    def __init__(self, store, thread_manager: ThreadManager):
        self.store = store
        self.thread_manager = thread_manager
        self.nutrient_thread = None

        # 센서 및 액추에이터 초기화
        self.temp_sensor = TemperatureSensor(self._get_from_sensors('water_temperature'))
        self.ph_sensor = PhSensor(self._get_from_sensors('ph'))
        self.ec_sensor = EcSensor(self._get_from_sensors('ec'))
        self.ph_mixer = MagneticFan(self._get_from_machines('ph_mixer'))
        self.ec_mixer = MagneticFan(self._get_from_machines('ph_mixer'))
        self.ec_mixer = DosingPump(self._get_from_machines('ph'))
        self.ec_mixer = DosingPump(self._get_from_machines('ec'))

        # 목표 pH, EC, 온도 설정
        self.target_ph = 6.5
        self.target_ec = 1.5
        self.target_temp = 25.0
    
    def _get_from_machines(self, name):
        return next((m for m in self.store.machines if m.name == name), None)

    def _get_from_sensors(self, name):
        return next((m for m in self.store.sensors if m['name'] == name), None)
    
    def initialize(self) -> bool:
        """영양소 매니저 초기화"""
        try:
            custom_logger.info("\n=== 영양소 매니저 초기화 중 ===")
            self._start_nutrient_thread()
            return True
        except Exception as e:
            custom_logger.error(f"영양소 매니저 초기화 실패: {str(e)}")
            return False

    def _start_nutrient_thread(self):
        """영양소 조절 스레드 시작"""
        def run_nutrient_control():
            try:
                while not self.thread_manager.stop_event.is_set():
                    self.adjust_nutrients()
                    self.thread_manager.stop_event.wait(60)  # 1분마다 조절
            except Exception as e:
                custom_logger.error(f"영양소 조절 스레드 오류 발생: {str(e)}")

        self.nutrient_thread = threading.Thread(
            target=run_nutrient_control,
            name="NutrientControl",
            daemon=True
        )
        self.nutrient_thread.start()
        self.thread_manager.automation_threads.append(self.nutrient_thread)
        custom_logger.info("영양소 조절 스레드 시작")

    def read_sensors(self):
        """센서 데이터 읽기"""
        ph = self.ph_sensor.read()
        ec = self.ec_sensor.read()
        temp = self.temp_sensor.read()
        custom_logger.info(f"센서 데이터: pH={ph}, EC={ec}, Temp={temp}")
        return ph, ec, temp

    def adjust_nutrients(self):
        """영양소 조절 알고리즘"""
        ph, ec, temp = self.read_sensors()

        # pH 조절
        if ph < self.target_ph:
            self.pump.add_ph_up()
            custom_logger.info("pH 상승을 위해 용액 추가")
        elif ph > self.target_ph:
            self.pump.add_ph_down()
            custom_logger.info("pH 하강을 위해 용액 추가")

        # EC 조절
        if ec < self.target_ec:
            self.pump.add_nutrient_solution()
            custom_logger.info("EC 상승을 위해 영양소 추가")

        # 온도 조절 (팬 작동)
        if temp > self.target_temp:
            self.fan.start()
            custom_logger.info("온도 조절을 위해 팬 작동")
        else:
            self.fan.stop()

    def stop(self):
        """영양소 매니저 종료"""
        custom_logger.info("\n영양소 매니저 종료 요청")
        if self.nutrient_thread and self.nutrient_thread.is_alive():
            self.thread_manager.stop_event.set()
            self.nutrient_thread.join()
        self.cleanup()

    def cleanup(self):
        """리소스 정리"""
        self.fan.stop()
        self.pump.stop_all()
        GPIO.cleanup()
        custom_logger.info("Nutrient Manager 종료 및 리소스 정리 완료")

if __name__ == "__main__":
    manager = NutrientManager(ph_pin=17, ec_pin=27, temp_pin=22, fan_pin=5, pump_pin=6)
    manager.run() 