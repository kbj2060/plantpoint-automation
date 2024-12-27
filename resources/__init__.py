from resources.mqtt import MQTTClient
from resources.websocket import WebSocket
from resources.http import HTTP
from constants import SWITCH_SOCKET_ADDRESS, CURRENT_SOCKET_ADDRESS


# 리소스 인스턴스 생성
mqtt = MQTTClient()
ws = WebSocket
http = HTTP()

# 모듈 레벨에서 사용할 수 있도록 내보내기
__all__ = ['mqtt', 'ws', 'http'] 