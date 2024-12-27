from typing import List, Dict
from tabulate import tabulate
from constants import ON
from interfaces.Machine import BaseMachine
from logger.custom_logger import custom_logger


class AutomationLogger:
    def __init__(self, automated_machines: List[BaseMachine], prev_machines: List[Dict]):
        """
        Args:
            automated_machines: 자동화가 실행된 장치들
            prev_machines: 자동화 실행 전 장치들의 상태
        """
        self.automated_machines = automated_machines or []
        self.prev_machines = prev_machines
        self.header = ['machine_id', 'name', 'mqtt_topic', 'status', 'switch_created_at', 'remarks']
        self.table: list = []

    def get_status_text(self, status: bool) -> str:
        """상태를 ON/OFF 텍스트로 변환"""
        return "ON" if status else "OFF"

    def format_status_change(self, current_status: bool, prev_status: bool) -> str:
        """상태 변경 내용을 포맷팅"""
        return f"{self.get_status_text(prev_status)} -> {self.get_status_text(current_status)}"

    def get_machine_status(self, machine: BaseMachine, prev_status: bool) -> List[str]:
        """장치의 상태 변경 여부에 따른 remarks 반환"""
        if machine.status == prev_status:
            return ["STAY"]
        return [self.format_status_change(machine.status, prev_status)]

    def create_machine_from_switch(self, switch: Dict) -> BaseMachine:
        """딕셔너리로부터 BaseMachine 객체 생성"""
        return BaseMachine(
            machine_id=switch['device_id'],
            name=switch['name'],
            status=switch['status'],
            switch_created_at=switch['created_at']
        )

    def get_machine_values(self, machine: BaseMachine) -> list:
        """BaseMachine 객체의 값들을 리스트로 반환 (pin 제외)"""
        return [
            machine.machine_id,
            machine.name,
            machine.mqtt_topic,
            machine.status,
            machine.switch_created_at
        ]

    def build_table(self) -> None:
        """테이블 데이터 생성"""
        for prev_m in self.prev_machines:
            # 자동화가 실행된 장치에서 찾기
            machine = next(
                (m for m in self.automated_machines if m.name == prev_m['name']), 
                None
            )
            
            if not machine:
                # 자동화가 실행되지 않은 장치는 이전 상태 표시
                machine = self.create_machine_from_switch(prev_m)
                self.table.append(self.get_machine_values(machine) + ["STAY"])
            else:
                # 자동화가 실행된 장치는 상태 변경 여부 확인
                self.table.append(
                    self.get_machine_values(machine) + 
                    self.get_machine_status(machine, prev_m['status'])
                )

    def result(self) -> None:
        """자동화 실행 결과를 테이블로 출력"""
        self.build_table()
        
        custom_logger.info(
            "\n------------------Automation Status Information------------------\n"
            + tabulate(self.table, self.header, tablefmt="fancy_grid")
        )