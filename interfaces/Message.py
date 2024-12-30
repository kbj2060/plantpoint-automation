from typing import TypedDict, Literal
from dataclasses import dataclass

class SwitchData(TypedDict):
    name: str
    value: Literal[0, 1]

class MQTTPayload(TypedDict):
    pattern: str
    data: SwitchData

class WSPayload(TypedDict):
    event: Literal['sendSwitchToServer']
    data: dict[str, bool | str]