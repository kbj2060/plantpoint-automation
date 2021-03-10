from typing import List


class EnvironmentSection:
    def __init__(self, section: str):
        super().__init__()
        self.section = section


class MachineSection:
    def __init__(self, section: str):
        super().__init__()
        self.section = section


class Section:
    def __init__(self,
                 m_section: MachineSection,
                 e_sections: List[EnvironmentSection]):
        self.m_section = m_section
        self.e_sections = e_sections
