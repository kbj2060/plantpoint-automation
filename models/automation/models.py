from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Tuple, Dict, Any, Union, Callable
from enum import Enum
import re

@dataclass
class TimeConfig:
    """시간 설정을 관리하는 클래스 (문자열 '1m', '30s' 등도 지원)"""
    value: int = field(default=0)
    unit: str = field(default='s')

    def __init__(self, value):
        if isinstance(value, str):
            # 문자열 파싱: 예) '1m', '30s', '2h'
            match = re.match(r"^(\d+)([smhd])$", value.strip())
            if match:
                self.value = int(match.group(1))
                self.unit = match.group(2)
            else:
                # 파싱 실패시 기본값
                self.value = 0
                self.unit = 's'
        else:
            self.value = value if value is not None else 0
            self.unit = 's'

    def to_seconds(self) -> int:
        """시간 단위를 초 단위로 변환"""
        units = {
            's': 1,           # 초
            'm': 60,          # 분
            'h': 3600,        # 시간
            'd': 86400        # 일
        }
        return self.value * units.get(self.unit, 1)

@dataclass
class IntervalState:
    """인터벌 자동화의 상태를 관리하는 클래스"""
    last_start_time: Optional[datetime] = None
    last_toggle_time: Optional[datetime] = None

    def start_new_cycle(self, now: datetime) -> None:
        """새로운 주기 시작"""
        self.last_start_time = now
        self.last_toggle_time = now

    def update_toggle_time(self, now: datetime) -> None:
        """토글 시간 업데이트"""
        self.last_toggle_time = now

    def get_elapsed_times(self, now: datetime) -> Tuple[float, float]:
        """경과 시간 계산"""
        if not self.last_start_time or not self.last_toggle_time:
            return 0.0, 0.0
        return (
            (now - self.last_start_time).total_seconds(),
            (now - self.last_toggle_time).total_seconds()
        ) 

class TopicType(Enum):
    """MQTT 토픽 타입"""
    AUTOMATION = "automation"
    CURRENT = "current"
    SWITCH = "switch"
    ENVIRONMENT = "environment"
    
    @classmethod
    def from_topic(cls, topic: str) -> Optional['TopicType']:
        """토픽 문자열에서 TopicType 생성"""
        topic_type = topic.split('/')[0]
        try:
            return cls(topic_type)
        except ValueError:
            return None

@dataclass
class SensorData:
    """센서 데이터 관리"""
    name: str
    value: float
    timestamp: datetime = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()
    
    @property
    def redis_key(self) -> str:
        """Redis 키 생성"""
        return f"{self.topic_type.value}/{self.name}"
    
    def to_dict(self) -> Dict[str, Any]:
        """딕셔너리 변환"""
        return {
            "name": self.name,
            "value": self.value,
            "timestamp": self.timestamp.isoformat()
        }

@dataclass
class EnvironmentData(SensorData):
    """환경 센서 데이터"""
    topic_type: TopicType = TopicType.ENVIRONMENT

@dataclass
class CurrentData(SensorData):
    """전류 센서 데이터"""
    topic_type: TopicType = TopicType.CURRENT

@dataclass
class MQTTMessage:
    """MQTT 메시지 관리"""
    topic: str
    payload: Dict[str, Any]
    
    @classmethod
    def from_message(cls, message) -> 'MQTTMessage':
        """MQTT 메시지 객체로 변환"""
        import json
        return cls(
            topic=message.topic,
            payload=json.loads(message.payload.decode())
        )
    
    @property
    def topic_parts(self) -> Tuple[str, str]:
        """토픽 분리 (타입, 이름)"""
        return tuple(self.topic.split('/'))
    
    def to_sensor_data(self) -> Optional[SensorData]:
        """센서 데이터 객체로 변환"""
        topic_type, name = self.topic_parts
        value = self.payload.get('value')
        
        if value is None:
            return None
            
        sensor_types = {
            TopicType.ENVIRONMENT.value: EnvironmentData,
            TopicType.CURRENT.value: CurrentData
        }
        
        data_class = sensor_types.get(topic_type)
        if data_class:
            return data_class(name=name, value=float(value))
        return None

@dataclass
class RedisData:
    """Redis 데이터 관리"""
    key: str
    value: Union[str, float, int]
    
    @classmethod
    def from_sensor_data(cls, data: SensorData) -> 'RedisData':
        """센서 데이터로부터 Redis 데이터 생성"""
        return cls(
            key=data.redis_key,
            value=str(data.value)
        )
    
    def save(self) -> bool:
        """Redis에 데이터 저장"""
        from resources import redis
        try:
            redis.set(self.key, str(self.value))
            return True
        except Exception:
            return False
    
    @classmethod
    def get(cls, key: str) -> Optional['RedisData']:
        """Redis에서 데이터 조회"""
        from resources import redis
        try:
            value = redis.get(key)
            if value is not None:
                return cls(key=key, value=value)
            return None
        except Exception:
            return None 

@dataclass
class SwitchMessage:
    """스위치 메시지 데이터"""
    name: str
    value: bool

    def to_dict(self) -> Dict[str, Any]:
        """딕셔너리 변환"""
        return {
            'name': self.name,
            'value': self.value
        }

@dataclass
class MQTTPayloadData:
    """MQTT 페이로드 데이터"""
    pattern: str
    data: SwitchMessage

    def to_dict(self) -> Dict[str, Any]:
        """딕셔너리 변환"""
        return {
            'pattern': self.pattern,
            'data': self.data.to_dict()
        }

@dataclass
class WebSocketMessage:
    """WebSocket 메시지 데이터"""
    event: str
    data: Dict[str, bool]

    @classmethod
    def from_switch(cls, name: str, value: bool, event: str) -> 'WebSocketMessage':
        """스위치 데이터로부터 WebSocket 메시지 생성"""
        return cls(
            event=event,
            data={ name: value }
        )

    def to_dict(self) -> Dict[str, Any]:
        """딕셔너리 변환"""
        return {
            'event': self.event,
            'data': self.data
        } 

@dataclass
class MessageHandler:
    """메시지 핸들러 설정"""
    topic_type: TopicType
    handler: Callable
    description: str 