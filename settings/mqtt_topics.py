"""
MQTT 토픽 패턴 정의
"""


class MQTTTopics:
    """MQTT 토픽 패턴 상수"""

    # 기본 토픽 패턴
    SWITCH = "switch/{name}"
    AUTOMATION = "automation/{name}"
    ENVIRONMENT = "environment/{name}"

    # 구독 패턴 (와일드카드)
    SUBSCRIBED = ["environment/#", "automation/#", "switch/#"]

    @staticmethod
    def switch(name: str) -> str:
        """스위치 제어 토픽 생성

        Args:
            name: 디바이스 이름

        Returns:
            str: switch/{name} 형식의 토픽
        """
        return f"switch/{name}"

    @staticmethod
    def automation(name: str) -> str:
        """자동화 설정 토픽 생성

        Args:
            name: 디바이스 이름

        Returns:
            str: automation/{name} 형식의 토픽
        """
        return f"automation/{name}"

    @staticmethod
    def environment(name: str) -> str:
        """환경 센서 값 토픽 생성

        Args:
            name: 센서 이름

        Returns:
            str: environment/{name} 형식의 토픽
        """
        return f"environment/{name}"
