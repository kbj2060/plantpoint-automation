from abc import ABCMeta


class Section(metaclass=ABCMeta):
    def __init__(self):
        pass


class EnvironmentSection(Section):
    def __init__(self, e_section):
        super().__init__()
        self.e_section = e_section


class MachineSection(Section):
    def __init__(self, m_section: str, e_sections: list):
        super().__init__()
        self.m_section = m_section
        self.e_sections = e_sections
