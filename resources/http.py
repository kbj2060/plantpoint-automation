"""HTTP client for PlantPoint API."""

from typing import List, Dict, Any
from datetime import datetime
import requests
from logger.custom_logger import custom_logger
from models.Response import (
    AutomationResponse,
    AutomationSwitchResponse,
    CurrentResponse,
    EnvironmentResponse,
    EnvironmentTypeResponse,
    MachineResponse,
    SensorResponse,
    SwitchResponse
)
from constants import (
    CURRENT_READ_URL,
    INTERVAL_DEVICE_STATES_READ_URL,
    SIGNIN_URL,
    AUTOMATION_READ_URL,
    ENVIRONMENT_EACH_LATEST_READ_URL,
    ENVIRONMENT_TYPE_READ_URL,
    SWITCH_EACH_LATEST_READ_URL,
    MACHINE_READ_URL,
    SENSOR_READ_URL,
    USERNAME,
    PASSWORD
)


class HTTP:
    """HTTP client for API communication."""

    def __init__(self) -> None:
        self.token = self._get_token()
        self.headers = {'Authorization': f'Bearer {self.token}'}

    def _get_token(self) -> str:
        """
        인증 토큰 획득

        Returns:
            str: JWT access token

        Raises:
            Exception: If authentication fails
        """
        try:
            response = requests.post(
                SIGNIN_URL,
                json={'username': USERNAME, 'password': PASSWORD},
                timeout=10
            )
            response.raise_for_status()
            return response.json()['accessToken']
        except Exception as e:
            custom_logger.error(f"토큰 획득 실패: {str(e)}")
            raise

    def _get_request(self, url: str) -> List[Dict[str, Any]]:
        """
        GET 요청 처리

        Args:
            url: Request URL

        Returns:
            Response JSON data

        Raises:
            Exception: If request fails
        """
        try:
            response = requests.get(url, headers=self.headers, timeout=10)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            custom_logger.error(f"GET 요청 실패 ({url}): {str(e)}")
            raise

    def get_automations(self) -> List[Dict[str, Any]]:
        """Get automation configurations."""
        return self._get_request(AUTOMATION_READ_URL)

    def get_interval_device_states(self) -> List[Dict[str, Any]]:
        """Get interval-based device states."""
        return self._get_request(INTERVAL_DEVICE_STATES_READ_URL)

    def get_environments(self) -> List[Dict[str, Any]]:
        """Get latest environment readings."""
        return self._get_request(ENVIRONMENT_EACH_LATEST_READ_URL)

    def get_environment_type(self) -> List[Dict[str, Any]]:
        """Get environment type configurations."""
        return self._get_request(ENVIRONMENT_TYPE_READ_URL)

    def get_switches(self) -> List[Dict[str, Any]]:
        """Get latest switch states."""
        return self._get_request(SWITCH_EACH_LATEST_READ_URL)

    def get_machines(self) -> List[Dict[str, Any]]:
        """Get machine configurations."""
        return self._get_request(MACHINE_READ_URL)

    def get_sensors(self) -> List[Dict[str, Any]]:
        """Get sensor configurations."""
        return self._get_request(SENSOR_READ_URL)

    def get_currents(self) -> List[Dict[str, Any]]:
        """Get current monitoring data."""
        return self._get_request(CURRENT_READ_URL)