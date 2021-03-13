from typing import List

from interfaces.Section import MachineSection, EnvironmentSection, Section
from logger.custom_logger import custom_logger
from resources import db
from utils import grouping


class SectionCollector:
    def __init__(self):
        self.grouped_sections = grouping(db.get_sections())
        self.section_holder: List[Section] = list()

    def collect_sections(self) -> List[Section]:
        for ms in self.grouped_sections.keys():
            m_section = MachineSection(ms)
            e_sections = [EnvironmentSection(es) for es in self.grouped_sections[ms]]
            self.section_holder.append(Section(m_section, e_sections))
        custom_logger.success("Collecting The Sections Information Completed!")
        return self.section_holder
