from logger.custom_logger import custom_logger
from models.sensors import PhSensor, EcSensor, TemperatureSensor
from models.actuators import MagneticFan, DosingPump
from managers.thread_manager import ThreadManager
import threading
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
        self.temp_sensor = TemperatureSensor(self._get_sensor_pin('water_temperature'))
        self.ph_sensor = PhSensor(self._get_sensor_pin('ph'))
        self.ec_sensor = EcSensor(self._get_sensor_pin('ec'))
        self.ph_mixer = MagneticFan(self._get_machine_pin('ph_mixer'))
        self.ec_mixer = MagneticFan(self._get_machine_pin('ec_mixer'))
        self.ph_pump = DosingPump(self._get_machine_pin('ph'))
        self.ec_pump = DosingPump(self._get_machine_pin('ec'))

        # 목표 pH, EC, 온도 설정
        self.target_ph = self._get_automation_setting('ph', 7.0)  # 기본값 7.0
        self.target_ec = self._get_automation_setting('ec', 1.5)
        self.target_temp = self._get_automation_setting('temperature', 25.0)

    def _get_machine_pin(self, name):
        machine = next((m for m in self.store.machines if m.name == name), None)
        return machine.pin if machine else None

    def _get_sensor_pin(self, name):
        sensor = next((s for s in self.store.sensors if s['name'] == name), None)
        return sensor['pin'] if sensor else None

    def _get_automation_setting(self, key, default):
        automation = next((a for a in self.store.automations if key in a['settings']), None)
        return automation['settings'][key] if automation else default

    def initialize(self) -> bool:
        """영양소 매니저 초기화"""
        try:
            custom_logger.info("\n=== 영양소 매니저 초기화 중 ===")
            self._start_monitoring()
            return True
        except Exception as e:
            custom_logger.error(f"영양소 매니저 초기화 실패: {str(e)}")
            return False

    def _start_monitoring(self):
        """영양소 조절 스레드 시작"""
        try:
            self.nutrient_thread = threading.Thread(
                target=self._monitor_nutrients,
                name="NutrientControl",
                daemon=True
            )
            self.nutrient_thread.start()
            self.thread_manager.current_threads['nutrient'] = self.nutrient_thread
            custom_logger.info("영양소 조절 스레드 시작")
        except Exception as e:
            custom_logger.error(f"영양소 조절 스레드 시작 실패: {str(e)}")
            raise

    def _monitor_nutrients(self):
        """영양소 상태 모니터링"""
        try:
            while not self.thread_manager.stop_event.is_set():
                self.adjust_nutrients()
                self.thread_manager.stop_event.wait(60)  # 1분마다 조절
        except Exception as e:
            custom_logger.error(f"영양소 모니터링 중 오류 발생: {str(e)}")

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
            self.ph_pump.add_ph_up()
            custom_logger.info("pH 상승을 위해 용액 추가")
        elif ph > self.target_ph:
            self.ph_pump.add_ph_down()
            custom_logger.info("pH 하강을 위해 용액 추가")

        # EC 조절
        if ec < self.target_ec:
            self.ec_pump.add_nutrient_solution()
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
