class BaseMachine:
    def __init__(self, machine_id, pin, name, status=None, switch_created_at=None):
        self.machine_id = machine_id
        self.name = name
        self.mqtt_topic = f'switch/{name}'
        self.pin = pin
        self.status = status
        self.switch_created_at = switch_created_at

    def __str__(self) -> str:
        """객체를 문자열로 표현할 때 사용"""
        return f"BaseMachine({', '.join(f'{k}={v}' for k, v in self.__dict__.items())})"
    
    def __repr__(self) -> str:
        """디버깅/개발용 출력"""
        return self.__str__()
    
    def get_properties(self) -> dict:
        """객체의 모든 프로퍼티를 딕셔너리로 반환"""
        return self.__dict__
    
    def print_properties(self):
        """객체의 모든 프로퍼티를 보기 좋게 출력"""
        for key, value in self.__dict__.items():
            print(f"{key}: {value}")

    def set_status(self, status):
        self.status = status

    def check_machine_on(self):
        return self.status == 1

    @staticmethod
    def merge_device_data(switch_data: list, device_data: list) -> list:
        """
        스위치 데이터의 status와 created_at을 device_data에 추가
        """
        # 스위치 데이터를 device_id를 키로 하는 딕셔너리로 변환
        switch_dict = {
            switch['device_id']: {
                'status': switch['status'],
                'created_at': switch['created_at']
            } for switch in switch_data
        }
        
        # 디바이스 데이터에 status와 switch_created_at 추가
        for device in device_data:
            device_switch = switch_dict.get(device['id'], {'status': 0, 'created_at': None})
            device['status'] = device_switch['status']
            device['switch_created_at'] = device_switch['created_at']
        
        return device_data

class Machines:
    def __init__(self, machines: list):
        self.machines = machines
