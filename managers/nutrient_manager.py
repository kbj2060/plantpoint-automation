"""
Nutrient Manager Implementation

This module manages nutrient-related sensors including pH, EC, and water temperature.
It uses Atlas Scientific I2C sensors for monitoring water quality parameters.
"""

import time
from typing import Optional, Dict, List
from logger.custom_logger import custom_logger
from managers.thread_manager import ThreadManager

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
                    custom_logger.debug(f"Read {sensor_name}: {value}")
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

    def check_safety_limits(self, readings: Dict[str, float]) -> bool:
        """
        Check if sensor readings are within safe limits.

        Args:
            readings: Dictionary of sensor readings

        Returns:
            bool: True if all readings are safe, False otherwise
        """
        warnings = []

        ph = readings.get("ph")
        if ph is not None:
            if ph < self.PH_MIN or ph > self.PH_MAX:
                warnings.append(f"pH out of range: {ph} (safe range: {self.PH_MIN}-{self.PH_MAX})")

        ec = readings.get("ec")
        if ec is not None:
            if ec < self.EC_MIN or ec > self.EC_MAX:
                warnings.append(f"EC out of range: {ec} (safe range: {self.EC_MIN}-{self.EC_MAX})")

        temp = readings.get("water_temperature")
        if temp is not None:
            if temp < self.TEMP_MIN or temp > self.TEMP_MAX:
                warnings.append(f"Temperature out of range: {temp} (safe range: {self.TEMP_MIN}-{self.TEMP_MAX})")

        if warnings:
            for warning in warnings:
                custom_logger.warning(warning)
            return False

        return True

    def adjust_nutrients(self) -> None:
        """
        Main loop for nutrient adjustment.
        Reads sensors and checks safety limits.
        """
        try:
            readings = self.read_sensors()

            if readings:
                # Log current readings
                custom_logger.info(f"Sensor readings: {readings}")

                # Check safety limits
                if not self.check_safety_limits(readings):
                    custom_logger.warning("Sensor readings outside safe limits")

                # Store readings in store if needed
                if self.store:
                    for sensor_name, value in readings.items():
                        self.store.set(f"sensor:{sensor_name}", value)

        except Exception as e:
            custom_logger.error(f"Error in adjust_nutrients: {e}")

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
