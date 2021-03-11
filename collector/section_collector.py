from typing import List

from collector.utils import grouping
from handler.db_handler import DBHandler
from interfaces.Section import MachineSection, EnvironmentSection, Section


class SectionCollector:
    def __init__(self):
        self.db = DBHandler()
        self.grouped_sections = grouping(self.db.get_sections())
        self.section_holder = list()

    def collect_sections(self) -> List[Section]:
        for ms in self.grouped_sections.keys():
            m_section = MachineSection(ms)
            e_sections = [EnvironmentSection(es) for es in self.grouped_sections[ms]]
            self.section_holder.append(Section(m_section, e_sections))
        return self.section_holder
