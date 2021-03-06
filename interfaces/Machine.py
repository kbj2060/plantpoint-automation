class BaseMachine:
    def __init__(self, section: str):
        self.section = section
        self.name = ''
        self.automation_type = ''
        self.enable = None
        self.status = None
        self.mqtt_topic = ''
        self.start = []
        self.end = []
        self.term = 0

    @classmethod
    def get_properties(cls):
        return list(vars(cls('')).keys())

    def set_status(self, status):
        self.status = status

    def set_mqtt(self, topic):
        self.mqtt_topic = topic

    def set_automation(self, **kw):
        raise NotImplementedError()

    def check_machine_on(self):
        return self.status == 1


class RangeMachine(BaseMachine):
    def __init__(self, section: str):
        super().__init__(section=section)

    def set_automation(self, _type: str, enable: bool, start: list, end: list):
        self.automation_type = _type
        self.enable = enable
        self.start = start
        self.end = end


class TemperatureRangeMachine(RangeMachine):
    def __init__(self, section: str):
        super().__init__(section=section)


class TimeRangeMachine(RangeMachine):
    def __init__(self, section: str):
        super().__init__(section=section)


class CycleMachine(BaseMachine):
    def __init__(self, section: str):
        super().__init__(section=section)
        # self.term = 0

    def set_automation(self, _type: str, enable: bool, start: list, end: list, term: int):
        self.automation_type = _type
        self.enable = enable
        self.start = start
        self.end = end
        self.term = term


class Machines:
    def __init__(self, m_section: str, machines: list):
        self.machines = machines
        self.section = m_section
