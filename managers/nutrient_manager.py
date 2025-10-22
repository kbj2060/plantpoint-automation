"""
Nutrient Manager Implementation

This module manages nutrient-related sensors including pH, EC, and water temperature.
It uses Atlas Scientific I2C sensors for monitoring water quality parameters.
"""

import time
from typing import Optional, Dict, List
from logger.custom_logger import custom_logger
from managers.thread_manager import ThreadManager
from resources import mqtt
from tabulate import tabulate
from datetime import datetime
from config import settings

try:
    from drivers.AtlasI2C import AtlasI2C
    ATLAS_AVAILABLE = True
except ImportError:
    custom_logger.warning("AtlasI2C module not available. Sensor readings will be simulated.")
    ATLAS_AVAILABLE = False

try:
    import Adafruit_DHT
    DHT_AVAILABLE = True
except ImportError:
    custom_logger.warning("Adafruit_DHT module not available. DHT22 readings will be simulated.")
    DHT_AVAILABLE = False

try:
    import mh_z19
    CO2_AVAILABLE = True
except ImportError:
    custom_logger.warning("mh_z19 module not available. CO2 readings will be simulated.")
    CO2_AVAILABLE = False


class NutrientManager:
    """
    Nutrient management system for monitoring pH, EC, and water temperature.
    """

    SENSOR_NAME_MAPPING = {
        "RTD": "water_temperature",
        "PH": "ph",
        "EC": "ec",
        "co2": "co2",
        "temperature": "temperature"
    }

    # DHT22 센서 설정
    DHT_SENSOR = Adafruit_DHT.DHT22
    DHT_PIN = 26  # GPIO 핀 번호 (필요에 따라 변경)
    
    # MH-Z19E CO2 센서 설정
    # i3 Interlink 쉴드 사용 시 UART 포트 확인 필요
    CO2_SENSOR_PORT = None  # 자동 감지 시도
    # i3 Interlink 쉴드 사용 시 다음 중 하나로 설정:
    # CO2_SENSOR_PORT = '/dev/ttyAMA0'  # 기본 UART
    # CO2_SENSOR_PORT = '/dev/ttyAMA1'  # 추가 UART (쉴드에 따라 다름)
    # CO2_SENSOR_PORT = '/dev/serial0'  # 심볼릭 링크

    # Safety limits (loaded from environment variables)
    PH_MIN = settings.ph_min
    PH_MAX = settings.ph_max
    EC_MIN = settings.ec_min
    EC_MAX = settings.ec_max
    TEMP_MIN = settings.temp_min
    TEMP_MAX = settings.temp_max
    CO2_MIN = settings.co2_min
    CO2_MAX = settings.co2_max
    WATER_LEVEL_LOW = 1  # 아래 수위
    WATER_LEVEL_HIGH = 0  # 위 수위

    def __init__(self, store, thread_manager: ThreadManager) -> None:
        self.store = store
        self.thread_manager = thread_manager
        self.nutrient_thread: Optional[object] = None
        self.atlas_devices: List = []
        self.last_readings: Dict[str, float] = {}
        custom_logger.info("NutrientManager initialized")

    def initialize(self) -> bool:
        """
        Initialize nutrient manager and discover available sensors.

        Returns:
            bool: True if initialization successful, False otherwise.
        """
        try:
            # Atlas I2C 센서 검색 시도 (선택사항)
            if ATLAS_AVAILABLE:
                self._discover_atlas_devices()
                if self.atlas_devices:
                    custom_logger.info(f"Found {len(self.atlas_devices)} Atlas sensor(s)")
                else:
                    custom_logger.info("No Atlas sensors found")
            else:
                custom_logger.info("Atlas I2C not available - skipping Atlas sensor detection")

            # DHT22 센서 확인
            if DHT_AVAILABLE:
                custom_logger.info("DHT22 sensor available for temperature/humidity monitoring")
            else:
                custom_logger.info("DHT22 sensor not available - will use simulated values")

            # CO2 센서 확인
            if CO2_AVAILABLE:
                custom_logger.info("CO2 sensor available")
            else:
                custom_logger.info("CO2 sensor not available - will use simulated values")

            custom_logger.info("Sensor monitoring initialized successfully")
            return True

        except Exception as e:
            custom_logger.error(f"Failed to initialize NutrientManager: {e}")
            return False

    def _discover_atlas_devices(self) -> None:
        """Discover and initialize all Atlas I2C devices."""
        if not ATLAS_AVAILABLE:
            return

        device = AtlasI2C()
        device_address_list = device.list_i2c_devices()

        for address in device_address_list:
            device.set_i2c_address(address)
            response = device.query("I")
            try:
                moduletype = response.split(",")[1]
                name = device.query("name,?").split(",")[1]
                atlas_device = AtlasI2C(address=address, moduletype=moduletype, name=name)
                self.atlas_devices.append(atlas_device)
                custom_logger.info(f"Discovered Atlas sensor: {moduletype} at address {address}")
            except IndexError:
                continue

    def _start_nutrient_threads(self) -> None:
        """Start nutrient monitoring threads."""
        nutrient_thread = self.thread_manager.create_nutrient_thread(self)
        self.thread_manager.nutrient_threads.append(nutrient_thread)
        nutrient_thread.start()
        custom_logger.info("Nutrient monitoring thread started")

    def read_sensors(self) -> Dict[str, float]:
        """
        Read all Atlas sensors and water level sensor, return sensor values.

        Returns:
            Dict[str, float]: Dictionary of sensor name to value.
        """
        results = {}

        # Read Atlas I2C sensors (pH, EC, water_temperature)
        if ATLAS_AVAILABLE and self.atlas_devices:
            try:
                # Send read command to all devices
                for dev in self.atlas_devices:
                    dev.write("R")

                # Wait for sensors to respond
                time.sleep(AtlasI2C.LONG_TIMEOUT)

                # Read responses
                for dev in self.atlas_devices:
                    response_str = dev.read()

                    try:
                        # Parse response (format: "Success <device_info>: <value>")
                        value_str = response_str.split(':')[-1].strip().split('\x00')[0]
                        value = float(value_str)
                        sensor_name = self._get_sensor_name(dev.moduletype)
                        results[sensor_name] = value
                    except (ValueError, IndexError) as err:
                        custom_logger.error(f"Error reading {dev.moduletype}: {err}")

            except Exception as e:
                custom_logger.error(f"Error reading Atlas sensors: {e}")

        # Read water level sensor
        try:
            water_level_sensor = self._get_sensor_by_name("waterlevel")
            if water_level_sensor:
                water_level = self._read_sensor_value(water_level_sensor)
                if water_level is not None:
                    results["waterlevel"] = water_level
        except Exception as e:
            custom_logger.error(f"Error reading water level sensor: {e}")

        # Read DHT22 sensor (temperature and humidity)
        try:
            dht_results = self._read_dht22_sensor()
            results.update(dht_results)
        except Exception as e:
            custom_logger.error(f"Error reading DHT22 sensor: {e}")

        # Read MH-Z19E CO2 sensor
        try:
            co2_result = self._read_co2_sensor()
            results.update(co2_result)
        except Exception as e:
            custom_logger.error(f"Error reading CO2 sensor: {e}")

        self.last_readings = results
        return results

    def _get_sensor_name(self, moduletype: str) -> str:
        """Map module type to sensor name."""
        return self.SENSOR_NAME_MAPPING.get(moduletype.upper(), moduletype.lower())

    def _read_dht22_sensor(self) -> Dict[str, float]:
        """
        DHT22 센서에서 온도와 습도 읽기
        
        Returns:
            Dict[str, float]: {'temperature': 온도값, 'humidity': 습도값}
        """
        results = {}
        
        if not DHT_AVAILABLE:
            # 시뮬레이션 모드
            import random
            results["temperature"] = round(random.uniform(20.0, 30.0), 1)
            results["humidity"] = round(random.uniform(40.0, 80.0), 1)
            custom_logger.debug("DHT22 simulation mode - using random values")
            return results
        
        try:
            # DHT22 센서 읽기 (최대 3번 시도)
            for attempt in range(3):
                humidity, temperature = Adafruit_DHT.read_retry(
                    self.DHT_SENSOR, 
                    self.DHT_PIN
                )
                
                if humidity is not None and temperature is not None:
                    results["temperature"] = round(temperature, 1)
                    results["humidity"] = round(humidity, 1)
                    custom_logger.debug(f"DHT22 읽기 성공: 온도={temperature:.1f}°C, 습도={humidity:.1f}%")
                    break
                else:
                    custom_logger.warning(f"DHT22 읽기 실패 (시도 {attempt + 1}/3)")
                    time.sleep(2)  # 2초 대기 후 재시도
            else:
                custom_logger.error("DHT22 센서 읽기 실패 - 모든 시도 실패")
                # 실패 시 기본값 반환
                results["temperature"] = 25.0
                results["humidity"] = 50.0
                
        except Exception as e:
            custom_logger.error(f"DHT22 센서 읽기 중 오류: {e}")
            # 오류 시 기본값 반환
            results["temperature"] = 25.0
            results["humidity"] = 50.0
            
        return results

    def _read_co2_sensor(self) -> Dict[str, float]:
        """
        MH-Z19E CO2 센서에서 CO2 농도 읽기

        Returns:
            Dict[str, float]: {'co2': CO2값}
        """
        results = {}

        if not CO2_AVAILABLE:
            # 시뮬레이션 모드
            import random
            results["co2"] = round(random.uniform(400.0, 1000.0), 1)
            custom_logger.debug("CO2 simulation mode - using random values")
            return results

        try:
            # MH-Z19E 센서 읽기 - mh_z19.read_all()는 dict를 반환함
            # read_all()은 {'co2': value, 'temperature': value, ...} 형태를 반환
            if self.CO2_SENSOR_PORT:
                co2_data = mh_z19.read_all(serial_dev=self.CO2_SENSOR_PORT)
            else:
                # 포트가 None이면 라이브러리가 자동으로 적절한 UART 포트를 감지
                co2_data = mh_z19.read_all()

            # mh_z19.read_all()는 {'co2': value, 'temperature': value, ...} 형태의 dict를 반환
            if co2_data and isinstance(co2_data, dict) and 'co2' in co2_data:
                co2_value = co2_data['co2']

                # 유효한 범위 확인 (0-10000 ppm)
                if co2_value is not None and 0 <= co2_value <= 10000:
                    results["co2"] = round(float(co2_value), 1)
                    custom_logger.debug(f"CO2 읽기 성공: {co2_value:.1f} ppm")
                else:
                    custom_logger.warning(f"CO2 값이 유효하지 않은 범위: {co2_value}")
                    results["co2"] = 0.0
            else:
                custom_logger.warning(f"CO2 센서 읽기 실패 또는 잘못된 응답 형식: {co2_data}")
                results["co2"] = 0.0

        except Exception as e:
            custom_logger.error(f"CO2 센서 읽기 중 오류: {e}")
            # 오류 시 기본값 반환
            results["co2"] = 0.0

        return results

    def monitor_sensors(self) -> None:
        """
        센서 모니터링 루프 - 센서 값을 읽고 출력/전송
        """
        try:
            readings = self.read_sensors()

            if readings:
                # 센서값을 표 형식으로 출력
                self._print_sensor_table(readings)

                # 센서값들을 MQTT로 전송
                self._publish_sensor_data(readings)

                # Store readings in store if needed
                if self.store:
                    pass

        except Exception as e:
            custom_logger.error(f"Error in monitor_sensors: {e}")

    def _print_sensor_table(self, readings: Dict[str, float]) -> None:
        """
        센서 데이터를 표 형식으로 출력

        Args:
            readings: 센서 데이터 딕셔너리
        """
        current_time = datetime.now().strftime("%H:%M:%S")

        # 센서 데이터 테이블 준비
        sensor_info = {
            "ph": {
                "name": "pH",
                "min": self.PH_MIN,
                "max": self.PH_MAX
            },
            "ec": {
                "name": "EC (mS/cm)",
                "min": self.EC_MIN,
                "max": self.EC_MAX
            },
            "water_temperature": {
                "name": "Water Temp (°C)",
                "min": self.TEMP_MIN,
                "max": self.TEMP_MAX
            },
            "temperature": {
                "name": "Air Temp (°C)",
                "min": 15.0,
                "max": 35.0
            },
            "humidity": {
                "name": "Humidity (%)",
                "min": 30.0,
                "max": 90.0
            },
            "co2": {
                "name": "CO2 (ppm)",
                "min": self.CO2_MIN,
                "max": self.CO2_MAX
            },
            "waterlevel": {
                "name": "Water Level",
                "min": self.WATER_LEVEL_HIGH,
                "max": self.WATER_LEVEL_LOW
            }
        }

        table_data = []
        for sensor_name, value in readings.items():
            if sensor_name in sensor_info:
                info = sensor_info[sensor_name]
                display_name = info["name"]

                # Water level은 디지털 센서이므로 다르게 표시
                if sensor_name == "waterlevel":
                    value_str = "HIGH" if value == 0 else "LOW"
                    range_str = "0=HIGH / 1=LOW"
                    status = self._get_sensor_status(sensor_name, value)
                    table_data.append([display_name, value_str, range_str, status])
                else:
                    range_str = f"{info['min']:.1f} ~ {info['max']:.1f}"
                    status = self._get_sensor_status(sensor_name, value)
                    table_data.append([display_name, f"{value:.2f}", range_str, status])

        print(f"\n╔{'═' * 58}╗")
        print(f"║  영양소 센서 상태 - {current_time}                             ║")
        print(f"╚{'═' * 58}╝\n")
        print(tabulate(
            table_data,
            headers=["Sensor", "Value", "Range", "Status"],
            tablefmt="grid"
        ))
        print()

    def _get_sensor_status(self, sensor_name: str, value: float) -> str:
        """
        센서값의 상태를 반환 (정상/경고)

        Args:
            sensor_name: 센서 이름
            value: 센서값

        Returns:
            상태 문자열
        """
        if sensor_name == "ph":
            if self.PH_MIN <= value <= self.PH_MAX:
                return "✓ 정상"
            else:
                return "⚠ 경고"
        elif sensor_name == "ec":
            if self.EC_MIN <= value <= self.EC_MAX:
                return "✓ 정상"
            else:
                return "⚠ 경고"
        elif sensor_name == "water_temperature":
            if self.TEMP_MIN <= value <= self.TEMP_MAX:
                return "✓ 정상"
            else:
                return "⚠ 경고"
        elif sensor_name == "temperature":
            if 15.0 <= value <= 35.0:
                return "✓ 정상"
            else:
                return "⚠ 경고"
        elif sensor_name == "humidity":
            if 30.0 <= value <= 90.0:
                return "✓ 정상"
            else:
                return "⚠ 경고"
        elif sensor_name == "co2":
            if self.CO2_MIN <= value <= self.CO2_MAX:
                return "✓ 정상"
            else:
                return "⚠ 경고"
        elif sensor_name == "water_level":
            if value == self.WATER_LEVEL_HIGH:
                return "✓ HIGH (Full)"
            elif value == self.WATER_LEVEL_LOW:
                return "⚠ LOW"
            else:
                return "⚠ Invalid"
        return "-"

    def _publish_sensor_data(self, readings: Dict[str, float]) -> None:
        """
        센서 데이터를 MQTT로 전송 (범용)

        Args:
            readings: 센서 데이터 딕셔너리 (예: {'ph': 7.0, 'ec': 1.5, 'water_temperature': 25.0})
        """
        # 센서 이름과 MQTT 토픽 매핑
        sensor_topic_mapping = {
            "ph": "environment/ph",
            "ec": "environment/ec",
            "water_temperature": "environment/water_temperature",
            "temperature": "environment/temperature",
            "humidity": "environment/humidity",
            "co2": "environment/co2"
        }

        timestamp = time.time()

        for sensor_name, value in readings.items():
            try:
                # 매핑된 토픽이 있는 경우에만 전송
                if sensor_name in sensor_topic_mapping:
                    topic = sensor_topic_mapping[sensor_name]
                    payload = {
                        "pattern": topic,
                        "data": {
                            "name": sensor_name.lower(),
                            "value": value
                        }
                    }

                    mqtt.publish_message(topic, payload)
                    # custom_logger.debug(f"{sensor_name} 데이터 전송 완료: {value} -> {topic}")

            except Exception as e:
                custom_logger.error(f"{sensor_name} 데이터 전송 실패: {e}")

    def adjust_water_tank(
        self,
        nutrient_a_amount: float,
        nutrient_b_amount: float,
        mixing_duration: float = 60.0
    ) -> bool:
        """
        순환식 양액 교체 프로세스 - water_level이 1(LOW)로 바뀌었을 때 시작

        시작 조건: water_level 센서가 1 (아래 수위, LOW)

        프로세스:
        1. 탱크 아래 밸브를 켜서 물 비우기 수위까지 배수
        2. 급수 밸브를 열어 물 채우기 수위까지 물 주입
        3. A양액 주입 (워터펌프 + 유량센서로 제어)
        4. 교반기로 양액 혼합
        5. B양액 주입 (워터펌프 + 유량센서로 제어)
        6. 교반기로 양액 혼합

        Args:
            nutrient_a_amount: A양액 주입량 (mL)
            nutrient_b_amount: B양액 주입량 (mL)
            mixing_duration: 교반 시간 (초, 기본값: 60초)

        Returns:
            bool: 프로세스 성공 여부

        필요한 디바이스/센서:
            drain_valve: 배수 밸브
            fill_valve: 급수 밸브
            water_level: 수위 센서 (1개, 디지털)
            nutrient_a_pump: A양액 펌프
            nutrient_b_pump: B양액 펌프
            nutrient_a_flow: A양액 유량센서
            nutrient_b_flow: B양액 유량센서
            mixer: 교반기
        """
        try:
            # 시작 조건 체크: water_level이 1(LOW)인지 확인
            water_level_sensor = self._get_sensor_by_name("waterlevel")
            if not water_level_sensor:
                custom_logger.error("수위 센서를 찾을 수 없습니다")
                return False

            current_level = self._read_sensor_value(water_level_sensor)
            if current_level != self.WATER_LEVEL_LOW:
                custom_logger.warning(f"수위가 아직 LOW 상태가 아닙니다 (현재: {current_level})")
                return False

            custom_logger.info("=== 양액 교체 프로세스 시작 (waterlevel: LOW) ===")

            # 1. 물 비우기
            if not self._drain_water():
                custom_logger.error("물 비우기 실패")
                return False

            # 2. 물 채우기 대기
            if not self._wait_for_water_fill():
                custom_logger.error("물 채우기 대기 실패")
                return False

            # 3. A양액 주입
            if not self._inject_nutrient('A', nutrient_a_amount):
                custom_logger.error("A양액 주입 실패")
                return False

            # 4. A양액 혼합
            if not self._mix_nutrients(mixing_duration):
                custom_logger.error("A양액 혼합 실패")
                return False

            # 5. B양액 주입
            if not self._inject_nutrient('B', nutrient_b_amount):
                custom_logger.error("B양액 주입 실패")
                return False

            # 6. B양액 혼합
            if not self._mix_nutrients(mixing_duration):
                custom_logger.error("B양액 혼합 실패")
                return False

            custom_logger.info("=== 양액 교체 프로세스 완료 ===")
            return True

        except Exception as e:
            custom_logger.error(f"양액 교체 프로세스 중 오류 발생: {e}")
            return False

    def _drain_water(self) -> bool:
        """
        물 비우기 - 탱크 아래 밸브를 켜서 물 배수

        수위 센서 동작:
        - 아래 수위 (물 적음): 1
        - 위 수위 (물 많음): 0

        Returns:
            bool: 성공 여부
        """
        try:
            custom_logger.info("1단계: 물 비우기 시작")

            # 배수 밸브 디바이스 찾기
            drain_valve = self._get_machine_by_name("drain_valve")
            if not drain_valve:
                custom_logger.error("배수 밸브를 찾을 수 없습니다")
                return False

            # 물 수위 센서 찾기 (1=아래 수위, 0=위 수위)
            water_level_sensor = self._get_sensor_by_name("waterlevel")

            # 배수 밸브 열기
            self._control_machine(drain_valve, 1)
            custom_logger.info("배수 밸브 열림")

            # 물 비우기 수위까지 대기 (센서값 1이 될 때까지 = 아래 수위)
            start_time = time.time()
            timeout = 300  # 5분 타임아웃

            while time.time() - start_time < timeout:
                if water_level_sensor:
                    water_level = self._read_sensor_value(water_level_sensor)
                    if water_level == 1:  # 아래 수위 도달 (물 비워짐)
                        custom_logger.info("비우기 수위 도달 (센서: 아래 수위)")
                        break
                time.sleep(1)
            else:
                custom_logger.warning("물 비우기 타임아웃 - 센서 확인 필요")

            # 배수 밸브 닫기
            self._control_machine(drain_valve, 0)
            custom_logger.info("배수 밸브 닫힘 - 물 비우기 완료")

            return True

        except Exception as e:
            custom_logger.error(f"물 비우기 중 오류: {e}")
            return False

    def _wait_for_water_fill(self) -> bool:
        """
        물 채우기 - 급수 밸브를 열어 물탱크에 물 주입

        수위 센서 동작:
        - 아래 수위 (물 적음): 1
        - 위 수위 (물 많음): 0

        Returns:
            bool: 성공 여부
        """
        try:
            custom_logger.info("2단계: 물 채우기 시작")

            # 급수 밸브 디바이스 찾기
            fill_valve = self._get_machine_by_name("fill_valve")
            if not fill_valve:
                custom_logger.error("급수 밸브를 찾을 수 없습니다")
                return False

            # 물 수위 센서 찾기 (1=아래 수위, 0=위 수위)
            water_level_sensor = self._get_sensor_by_name("waterlevel")

            # 급수 밸브 열기
            self._control_machine(fill_valve, 1)
            custom_logger.info("급수 밸브 열림")

            # 채우기 수위까지 대기 (센서값 0이 될 때까지 = 위 수위)
            start_time = time.time()
            timeout = 600  # 10분 타임아웃

            while time.time() - start_time < timeout:
                if water_level_sensor:
                    water_level = self._read_sensor_value(water_level_sensor)
                    if water_level == 0:  # 위 수위 도달 (물 채워짐)
                        custom_logger.info("채우기 수위 도달 (센서: 위 수위)")
                        break
                time.sleep(2)
            else:
                custom_logger.error("물 채우기 타임아웃")
                # 타임아웃 시에도 밸브는 닫아야 함
                self._control_machine(fill_valve, 0)
                return False

            # 급수 밸브 닫기
            self._control_machine(fill_valve, 0)
            custom_logger.info("급수 밸브 닫힘 - 물 채우기 완료")

            return True

        except Exception as e:
            custom_logger.error(f"물 채우기 중 오류: {e}")
            # 예외 발생 시에도 밸브 닫기 시도
            try:
                fill_valve = self._get_machine_by_name("fill_valve")
                if fill_valve:
                    self._control_machine(fill_valve, 0)
            except:
                pass
            return False

    def _inject_nutrient(self, nutrient_type: str, amount: float) -> bool:
        """
        양액 주입 - 워터펌프와 유량센서로 양액 주입

        Args:
            nutrient_type: 양액 종류 ('A' 또는 'B')
            amount: 주입량 (mL)

        Returns:
            bool: 성공 여부
        """
        try:
            custom_logger.info(f"{nutrient_type}양액 주입 시작 (목표: {amount}mL)")

            # 워터펌프와 유량센서 찾기
            pump_name = f"nutrient_{nutrient_type.lower()}_pump"
            flow_sensor_name = f"nutrient_{nutrient_type.lower()}_flow"

            pump = self._get_machine_by_name(pump_name)
            if not pump:
                custom_logger.error(f"{pump_name}을 찾을 수 없습니다")
                return False

            flow_sensor = self._get_sensor_by_name(flow_sensor_name)

            # 워터펌프 켜기
            self._control_machine(pump, 1)
            custom_logger.info(f"{pump_name} 가동 시작")

            # 유량 체크
            total_flow = 0.0  # mL
            start_time = time.time()
            timeout = 300  # 5분 타임아웃
            last_check_time = start_time

            while time.time() - start_time < timeout:
                current_time = time.time()

                if flow_sensor:
                    flow_rate = self._read_sensor_value(flow_sensor)  # mL/min
                    if flow_rate is not None:
                        # 경과 시간 동안 주입된 양 계산
                        time_delta = current_time - last_check_time
                        total_flow += (flow_rate / 60.0) * time_delta  # mL

                        custom_logger.debug(f"{nutrient_type}양액 주입량: {total_flow:.1f}mL / {amount}mL")

                        if total_flow >= amount:
                            break

                last_check_time = current_time
                time.sleep(0.5)

            # 워터펌프 끄기
            self._control_machine(pump, 0)
            custom_logger.info(f"{pump_name} 정지 - {nutrient_type}양액 주입 완료 ({total_flow:.1f}mL)")

            return total_flow >= amount * 0.95  # 95% 이상 주입되면 성공

        except Exception as e:
            custom_logger.error(f"{nutrient_type}양액 주입 중 오류: {e}")
            return False

    def _mix_nutrients(self, duration: float) -> bool:
        """
        양액 혼합 - 교반기를 가동하여 양액 혼합

        Args:
            duration: 교반 시간 (초)

        Returns:
            bool: 성공 여부
        """
        try:
            custom_logger.info(f"양액 혼합 시작 ({duration}초)")

            # 교반기 찾기
            mixer = self._get_machine_by_name("mixer")
            if not mixer:
                custom_logger.error("교반기를 찾을 수 없습니다")
                return False

            # 교반기 켜기
            self._control_machine(mixer, 1)
            custom_logger.info("교반기 가동")

            # 지정된 시간 동안 대기
            time.sleep(duration)

            # 교반기 끄기
            self._control_machine(mixer, 0)
            custom_logger.info("교반기 정지 - 혼합 완료")

            return True

        except Exception as e:
            custom_logger.error(f"양액 혼합 중 오류: {e}")
            return False

    def _get_machine_by_name(self, name: str):
        """
        이름으로 machine 찾기

        Args:
            name: machine 이름

        Returns:
            Machine object or None
        """
        if not self.store or not self.store.machines:
            return None

        for machine in self.store.machines:
            if machine.name.lower() == name.lower():
                return machine

        return None

    def _get_sensor_by_name(self, name: str):
        """
        이름으로 sensor 찾기 (placeholder)

        Args:
            name: sensor 이름

        Returns:
            Sensor object or None
        """
        # TODO: store에 sensors 리스트가 있다면 구현
        custom_logger.warning(f"Sensor lookup not implemented: {name}")
        return None

    def _control_machine(self, machine, status: int) -> None:
        """
        Machine 제어 - MQTT로 제어 명령 전송

        Args:
            machine: Machine 객체
            status: 0 (OFF) 또는 1 (ON)
        """
        try:
            topic = machine.mqtt_topic
            payload = {
                "pattern": topic,
                "data": {
                    "name": machine.name,
                    "status": status
                }
            }

            mqtt.publish_message(topic, payload)
            machine.set_status(status)

            action = "ON" if status == 1 else "OFF"
            custom_logger.info(f"{machine.name} {action}")

        except Exception as e:
            custom_logger.error(f"Machine 제어 중 오류: {e}")

    def _read_sensor_value(self, sensor) -> Optional[float]:
        """
        센서 값 읽기 (placeholder)

        Args:
            sensor: Sensor 객체

        Returns:
            float or None
        """
        # TODO: 실제 센서 읽기 구현
        custom_logger.warning("Sensor read not implemented")
        return None

    def adjust_ph(self) -> None:
        """Adjust pH level (placeholder for future implementation)."""
        custom_logger.warning("pH adjustment not yet implemented")

    def adjust_ec(self) -> None:
        """Adjust EC level (placeholder for future implementation)."""
        custom_logger.warning("EC adjustment not yet implemented")

    def adjust_temp(self) -> None:
        """Adjust temperature (placeholder for future implementation)."""
        custom_logger.warning("Temperature adjustment not yet implemented")

    def start(self) -> None:
        """센서 모니터링 스레드 시작"""
        try:
            self._start_nutrient_threads()
            custom_logger.info("센서 모니터링 시작됨")
        except Exception as e:
            custom_logger.error(f"센서 모니터링 시작 실패: {e}")

    def run(self) -> None:
        """Main loop execution - 스레드에서 호출되는 메서드"""
        custom_logger.info("NutrientManager running")
        self.monitor_sensors()

        #self.adjust_water_tank(100, 100)

        custom_logger.info("센서 모니터링 완료")

    def stop(self) -> None:
        """Stop nutrient manager."""
        custom_logger.info("NutrientManager stop requested")
        self.thread_manager.stop_nutrient_threads()

    def cleanup(self) -> None:
        """Clean up resources."""
        try:
            # Close Atlas I2C devices
            for device in self.atlas_devices:
                try:
                    device.close()
                except Exception as e:
                    custom_logger.error(f"Error closing device: {e}")

            self.atlas_devices.clear()
            custom_logger.info("NutrientManager cleanup completed")
        except Exception as e:
            custom_logger.error(f"Error during cleanup: {e}")
