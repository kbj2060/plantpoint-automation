import requests
import json
from constants import \
    MACHINE_READ_URL, SENSOR_READ_URL, ENVIRONMENT_EACH_LATEST_READ_URL, ENVIRONMENT_TYPE_READ_URL, NAME, PASSWORD, SIGNIN_URL, AUTOMATION_READ_URL, SWITCH_EACH_LATEST_READ_URL, SWITCH_CREATE_URL,\
    HTTP_LOGGER_GET_MSG, HTTP_LOGGER_POST_MSG, USERNAME
from decorator.logger_decorator import BasicLogger
# from reference.secret import USERNAME, PASSWORD
from logger.custom_logger import custom_logger


class HttpHandler:
    def __init__(self):
        self.access_header = {}
        self.generate_token()

    @BasicLogger(HTTP_LOGGER_GET_MSG('Authentication Token'))
    def generate_token(self):
        data = json.dumps({"username": USERNAME, "password": PASSWORD})
        header = {"Content-Type": "application/json"}
        token = requests.post(f'{SIGNIN_URL}', data=data, headers=header)
        self.access_header = {"Authorization": f"Bearer {token.json()['accessToken']}"}

    @BasicLogger(HTTP_LOGGER_GET_MSG('Machine'))
    def get_machine(self):
        machine = requests.get(
            f'{MACHINE_READ_URL}',
            headers=self.access_header
        ).json()

        if None in machine:
            custom_logger.error(f"No Machines")
            return []

        return machine
    
    @BasicLogger(HTTP_LOGGER_GET_MSG('Sensor'))
    def get_sensor(self):
        sensor = requests.get(
            f'{SENSOR_READ_URL}',
            headers=self.access_header
        ).json()

        if None in sensor:
            custom_logger.error(f"No Sensors")
            return []

        return sensor

    @BasicLogger(HTTP_LOGGER_GET_MSG('Automations'))
    def get_automations(self):
        automation = requests.get(
            f'{AUTOMATION_READ_URL}',
            headers=self.access_header
        ).json()

        if None in automation:
            custom_logger.error(f"No Automations")
            return []

        return automation

    @BasicLogger(HTTP_LOGGER_GET_MSG('Environments Types'))
    def get_environment_types(self):
        environment = requests.get(
            f'{ENVIRONMENT_TYPE_READ_URL}',
            headers=self.access_header
        ).json()

        if None in environment:
            custom_logger.error(f"Section : No Environments Types")
            return []

        return environment
    
    @BasicLogger(HTTP_LOGGER_GET_MSG('Environments'))
    def get_environments(self):
        environment = requests.get(
            f'{ENVIRONMENT_EACH_LATEST_READ_URL}',headers=self.access_header
        ).json()

        if None in environment:
            custom_logger.error(f"No Environments")
            return []

        return environment

    @BasicLogger(HTTP_LOGGER_GET_MSG('Switches'))
    def get_switches(self):
        switches = requests.get(
            f'{SWITCH_EACH_LATEST_READ_URL}', headers=self.access_header
        ).json()

        if None in switches:
            custom_logger.error(f"No Switches")
            return []

        return switches

    @BasicLogger(HTTP_LOGGER_POST_MSG('Switch'))
    def post_switch(self, deviceId: int, status: int):
        data = {
            "deviceId": deviceId,
            "status": status,
            "controlledBy": NAME
        }
        requests.post(
            f'{SWITCH_CREATE_URL}', json=data, headers=self.access_header
        )
