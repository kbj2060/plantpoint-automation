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

try:
    from drivers.AtlasI2C import AtlasI2C
    ATLAS_AVAILABLE = True
except ImportError:
    custom_logger.warning("AtlasI2C module not available. Sensor readings will be simulated.")
    ATLAS_AVAILABLE = False


class NutrientManager:
    """
    Nutrient management system for monitoring pH, EC, and water temperature.
    """

    SENSOR_NAME_MAPPING = {
        "RTD": "water_temperature",
        "PH": "ph",
        "EC": "ec"
    }

    # Safety limits
    PH_MIN = 5.5
    PH_MAX = 7.5
    EC_MIN = 0.5
    EC_MAX = 3.0
    TEMP_MIN = 15.0
    TEMP_MAX = 35.0

    def __init__(self, store, thread_manager: ThreadManager) -> None:
        self.store = store
        self.thread_manager = thread_manager
        self.nutrient_thread: Optional[object] = None
        self.atlas_devices: List = []
        self.last_readings: Dict[str, float] = {}
        custom_logger.info("NutrientManager initialized")

    def initialize(self) -> bool:
        """
        Initialize nutrient manager and discover Atlas I2C sensors.

        Returns:
            bool: True if initialization successful, False otherwise.
        """
        if not ATLAS_AVAILABLE:
            custom_logger.warning("Atlas I2C not available. Running in simulation mode.")
            return False

        try:
            self._discover_atlas_devices()
            if self.atlas_devices:
                custom_logger.info(f"Found {len(self.atlas_devices)} Atlas sensor(s)")
                self._start_nutrient_threads()
                return True
            else:
                custom_logger.warning("No Atlas sensors found")
                return False
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
        if not self.atlas_devices:
            custom_logger.warning("No Atlas devices available. Cannot start nutrient threads.")
            return

        nutrient_thread = self.thread_manager.create_nutrient_thread(self)
        self.thread_manager.nutrient_threads.append(nutrient_thread)
        nutrient_thread.start()
        custom_logger.info("Nutrient monitoring thread started")

    def read_sensors(self) -> Dict[str, float]:
        """
        Read all Atlas sensors and return sensor values.

        Returns:
            Dict[str, float]: Dictionary of sensor name to value.
        """
        if not ATLAS_AVAILABLE or not self.atlas_devices:
            return {}

        results = {}

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

            self.last_readings = results
            return results

        except Exception as e:
            custom_logger.error(f"Error reading sensors: {e}")
            return {}

    def _get_sensor_name(self, moduletype: str) -> str:
        """Map module type to sensor name."""
        return self.SENSOR_NAME_MAPPING.get(moduletype.upper(), moduletype.lower())

    def adjust_nutrients(self) -> None:
        """
        Main loop for nutrient adjustment.
        Reads sensors and checks safety limits.
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
            custom_logger.error(f"Error in adjust_nutrients: {e}")

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
            }
        }

        table_data = []
        for sensor_name, value in readings.items():
            if sensor_name in sensor_info:
                info = sensor_info[sensor_name]
                display_name = info["name"]
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
            "water_temperature": "environment/water_temperature"
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

    def adjust_ph(self) -> None:
        """Adjust pH level (placeholder for future implementation)."""
        custom_logger.warning("pH adjustment not yet implemented")

    def adjust_ec(self) -> None:
        """Adjust EC level (placeholder for future implementation)."""
        custom_logger.warning("EC adjustment not yet implemented")

    def adjust_temp(self) -> None:
        """Adjust temperature (placeholder for future implementation)."""
        custom_logger.warning("Temperature adjustment not yet implemented")

    def run(self) -> None:
        """Main loop execution."""
        custom_logger.info("NutrientManager running")
        self.adjust_nutrients()

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
