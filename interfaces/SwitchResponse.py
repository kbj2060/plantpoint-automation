class SwitchResponse:
    def __init__(self, machine_section: str, machine: str, status: int):
        self.section = machine_section
        self.name = machine
        self.status = status
