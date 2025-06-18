import requests
from logger.custom_logger import custom_logger
from constants import (
    CURRENT_READ_URL, INTERVAL_DEVICE_STATES_READ_URL, SIGNIN_URL, AUTOMATION_READ_URL, ENVIRONMENT_EACH_LATEST_READ_URL,
    ENVIRONMENT_TYPE_READ_URL, SWITCH_EACH_LATEST_READ_URL, MACHINE_READ_URL,
    SENSOR_READ_URL, USERNAME, PASSWORD
)

class HTTP:
    def __init__(self):
        self.token = self._get_token()
        self.headers = {'Authorization': f'Bearer {self.token}'}

    def _get_token(self) -> str:
        """인증 토큰 획득"""
        try:
            response = requests.post(SIGNIN_URL, json={'username': USERNAME, 'password': PASSWORD})
            response.raise_for_status()
            return response.json()['accessToken']
        except Exception as e:
            custom_logger.error(f"토큰 획득 실패: {str(e)}")
            raise

    def _get_request(self, url: str) -> dict:
        """GET 요청 처리"""
        try:
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            custom_logger.error(f"GET 요청 실패 ({url}): {str(e)}")
            raise

    def get_automations(self) -> list:
        return self._get_request(AUTOMATION_READ_URL)
    
    def get_interval_device_states(self) -> list:
        return self._get_request(INTERVAL_DEVICE_STATES_READ_URL)

    def get_environments(self) -> list:
        return self._get_request(ENVIRONMENT_EACH_LATEST_READ_URL)

    def get_environment_type(self) -> list:
        return self._get_request(ENVIRONMENT_TYPE_READ_URL)

    def get_switches(self) -> list:
        return self._get_request(SWITCH_EACH_LATEST_READ_URL)

    def get_machines(self) -> list:
        return self._get_request(MACHINE_READ_URL)

    def get_sensors(self) -> list:
        return self._get_request(SENSOR_READ_URL) 
    
    def get_currents(self) -> list:
        return self._get_request(CURRENT_READ_URL)