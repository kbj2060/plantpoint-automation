import constants
import requests
import json

from interfaces.Section import MachineSection, EnvironmentSection


class HttpHandler:
    def __init__(self):
        self.access_header = ''
        self.generate_token()

    def generate_token(self):
        data = json.dumps({"username": constants.USERNAME, "password": constants.PASSWORD})
        header = {"Content-Type": "application/json"}
        token = requests.post(f'{constants.SIGNIN_URL}', data=data, headers=header)
        self.access_header = {"Authorization": f"Bearer {token.json()['access_token']}"}

    def get_automations(self, ms: MachineSection):
        return requests.get(
            f'{constants.AUTOMATION_READ_URL}/{ms.section}',
            headers=self.access_header
        ).json()['lastAutomations']

    def get_environments(self, es: EnvironmentSection):

        environment = requests.get(
            f'{constants.ENVIRONMENT_READ_URL}/{es.section}',
            headers=self.access_header
        ).json()
        environment['section'] = es.section
        return environment

    def get_switches(self, ms: MachineSection):
        return requests.get(
            f'{constants.SWITCH_READ_URL}/{ms.section}',
            headers=self.access_header
        ).json()
