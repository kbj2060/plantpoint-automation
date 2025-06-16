from logger.custom_logger import custom_logger
from models.sensors import PhSensor, EcSensor, TemperatureSensor
from models.actuators import MagneticFan, DosingPump
from managers.thread_manager import ThreadManager
import threading
from constants import USE_REAL_GPIO

if not USE_REAL_GPIO:
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
            self._start_nutrient_threads()
            return True
        except Exception as e:
            custom_logger.error(f"영양소 매니저 초기화 실패: {str(e)}")
            return False

    def _start_nutrient_threads(self):
        """pH, EC, 온도 각각에 대해 스레드 생성 및 시작"""
        try:
            ph_thread = threading.Thread(target=self._ph_control_loop, name="Nutrient-pH", daemon=True)
            ec_thread = threading.Thread(target=self._ec_control_loop, name="Nutrient-EC", daemon=True)
            temp_thread = threading.Thread(target=self._temp_control_loop, name="Nutrient-Temp", daemon=True)
            ph_thread.start()
            ec_thread.start()
            temp_thread.start()
            self.thread_manager.nutrient_threads.extend([ph_thread, ec_thread, temp_thread])
            custom_logger.info("pH, EC, 온도 조절 스레드 시작")
        except Exception as e:
            custom_logger.error(f"영양소 조절 스레드 시작 실패: {str(e)}")
            raise

    def _ph_control_loop(self):
        while not self.thread_manager.stop_event.is_set():
            self.adjust_ph()
            self.thread_manager.stop_event.wait(60)

    def _ec_control_loop(self):
        while not self.thread_manager.stop_event.is_set():
            self.adjust_ec()
            self.thread_manager.stop_event.wait(60)

    def _temp_control_loop(self):
        while not self.thread_manager.stop_event.is_set():
            self.adjust_temp()
            self.thread_manager.stop_event.wait(60)

    def adjust_ph(self):
        # ph = self.ph_sensor.read()
        # custom_logger.info(f"[pH] 센서 데이터: pH={ph}, 목표={self.target_ph}")
        # if ph < self.target_ph:
        #     self.ph_pump.add_ph_up()
        #     custom_logger.info("[pH] pH 상승을 위해 용액 추가")
        # elif ph > self.target_ph:
        #     self.ph_pump.add_ph_down()
        #     custom_logger.info("[pH] pH 하강을 위해 용액 추가")
        pass

    def adjust_ec(self):
        # ec = self.ec_sensor.read()
        # custom_logger.info(f"[EC] 센서 데이터: EC={ec}, 목표={self.target_ec}")
        # if ec < self.target_ec:
        #     self.ec_pump.add_nutrient_solution()
        #     custom_logger.info("[EC] EC 상승을 위해 영양소 추가")
        pass

    def adjust_temp(self):
        # temp = self.temp_sensor.read()
        # custom_logger.info(f"[Temp] 센서 데이터: Temp={temp}, 목표={self.target_temp}")
        # if temp > self.target_temp:
        #     self.fan.start()
        #     custom_logger.info("[Temp] 온도 조절을 위해 팬 작동")
        # else:
        #     self.fan.stop()
        pass

    def run(self):
        """메인 루프 실행"""
        if not self.thread_manager.nutrient_threads:
            custom_logger.warning("실행 중인 영양소 스레드가 없습니다.")
            return
        custom_logger.info(f"영양소 스레드 {len(self.thread_manager.nutrient_threads)}개 시작 완료")
        try:
            while not self.thread_manager.stop_event.is_set():
                # 필요시 nutrient thread 상태 모니터링 추가 가능
                self.thread_manager.stop_event.wait(60)
        except KeyboardInterrupt:
            self.stop()

    def stop(self):
        """영양소 매니저 종료"""
        custom_logger.info("\n영양소 매니저 종료 요청")
        self.thread_manager.stop_nutrient_threads()
        self.cleanup()

    def cleanup(self):
        """리소스 정리"""
        self.fan.stop()
        self.pump.stop_all()
        GPIO.cleanup()
        custom_logger.info("Nutrient Manager 종료 및 리소스 정리 완료")

    def _start_monitoring(self):
        pass  # 더 이상 사용하지 않음

    def _monitor_nutrients(self):
        pass  # 더 이상 사용하지 않음

    def read_sensors(self):
        """센서 데이터 읽기"""
        ph = self.ph_sensor.read()
        ec = self.ec_sensor.read()
        temp = self.temp_sensor.read()
        custom_logger.info(f"센서 데이터: pH={ph}, EC={ec}, Temp={temp}")
        return ph, ec, temp
    def adjust_nutrients(self):
        pass  # 더 이상 사용하지 않음

