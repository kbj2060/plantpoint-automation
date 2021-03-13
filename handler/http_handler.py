import requests
import json
from constants import \
    NAME, SIGNIN_URL, AUTOMATION_READ_URL, ENVIRONMENT_READ_URL, SWITCH_READ_URL,\
    SWITCH_CREATE_URL, HTTP_LOGGER_GET_MSG, HTTP_LOGGER_POST_MSG
from decorator.logger_decorator import BasicLogger
from handler.secret import USERNAME, PASSWORD
from interfaces.Section import MachineSection, EnvironmentSection
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
        self.access_header = {"Authorization": f"Bearer {token.json()['access_token']}"}

    @BasicLogger(HTTP_LOGGER_GET_MSG('Automations'))
    def get_automations(self, ms: MachineSection):
        automation = requests.get(
            f'{AUTOMATION_READ_URL}/{ms.section}',
            headers=self.access_header
        ).json()['lastAutomations']

        if None in automation:
            custom_logger.error(f"Section : {ms.section:3} | No Automations")
            return []

        return automation

    @BasicLogger(HTTP_LOGGER_GET_MSG('Environments'))
    def get_environments(self, es: EnvironmentSection):
        environment = requests.get(
            f'{ENVIRONMENT_READ_URL}/{es.section}',
            headers=self.access_header
        ).json()
        environment['section'] = es.section

        if None in environment:
            custom_logger.error(f"Section : {es.section:3} | No Environments")
            return []

        return environment

    @BasicLogger(HTTP_LOGGER_GET_MSG('Switches'))
    def get_switches(self, ms: MachineSection):
        switches = requests.get(
            f'{SWITCH_READ_URL}/{ms.section}',
            headers=self.access_header
        ).json()

        if None in switches:
            custom_logger.error(f"Section : {ms.section:3} | No Switches")
            return []

        return switches

    @BasicLogger(HTTP_LOGGER_POST_MSG('Switch'))
    def post_switch(self, section: str, name: str, status: int):
        data = {
            "machineSection": section,
            "machine": name,
            "status": status,
            "controlledBy": NAME
        }
        requests.post(
            f'{SWITCH_CREATE_URL}', json=data, headers=self.access_header
        )
