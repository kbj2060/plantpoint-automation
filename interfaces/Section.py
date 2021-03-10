from typing import List


class EnvironmentSection:
    def __init__(self, e_section: str):
        super().__init__()
        self.e_section = e_section


class MachineSection:
    def __init__(self, m_section: str):
        super().__init__()
        self.m_section = m_section


class Section:
    def __init__(self,
                 m_section: MachineSection,
                 e_sections: List[EnvironmentSection]):
        self.m_section = m_section
        self.e_sections = e_sections
