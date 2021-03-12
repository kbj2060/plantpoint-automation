import requests
import json
from constants import \
    NAME, USERNAME, PASSWORD, SIGNIN_URL, AUTOMATION_READ_URL, ENVIRONMENT_READ_URL, SWITCH_READ_URL, SWITCH_CREATE_URL, \
    HTTP_LOGGER_GET_MSG, HTTP_LOGGER_POST_MSG
from decorator.logger_decorator import BasicLogger
from interfaces.Section import MachineSection, EnvironmentSection


class HttpHandler:
    def __init__(self):
        self.access_header = {}
        self.generate_token()

    @BasicLogger(HTTP_LOGGER_POST_MSG('Authentication'))
    def generate_token(self):
        data = json.dumps({"username": USERNAME, "password": PASSWORD})
        header = {"Content-Type": "application/json"}
        token = requests.post(f'{SIGNIN_URL}', data=data, headers=header)
        self.access_header = {"Authorization": f"Bearer {token.json()['access_token']}"}

    @BasicLogger(HTTP_LOGGER_GET_MSG('Automations'))
    def get_automations(self, ms: MachineSection):
        return requests.get(
            f'{AUTOMATION_READ_URL}/{ms.section}',
            headers=self.access_header
        ).json()['lastAutomations']

    @BasicLogger(HTTP_LOGGER_GET_MSG('Environments'))
    def get_environments(self, es: EnvironmentSection):
        environment = requests.get(
            f'{ENVIRONMENT_READ_URL}/{es.section}',
            headers=self.access_header
        ).json()
        environment['section'] = es.section
        return environment

    @BasicLogger(HTTP_LOGGER_GET_MSG('Switches'))
    def get_switches(self, ms: MachineSection):
        return requests.get(
            f'{SWITCH_READ_URL}/{ms.section}',
            headers=self.access_header
        ).json()

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
