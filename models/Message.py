from typing import TypedDict, Literal
from dataclasses import dataclass

class SwitchData(TypedDict):
    name: str
    value: float

class MQTTPayload(TypedDict):
    pattern: str
    data: SwitchData

class WSPayload(TypedDict):
    event: Literal['sendSwitchToServer', 'sendCurrentToServer']
    data: dict[str, bool | str]