from constants import SEND_SWITCH_TO_SERVER, SOCKET_ENDPOINT, WS_LOGGER_MSG
import socketio

from decorator.logger_decorator import BasicLogger
from logger.custom_logger import custom_logger


class WebSocketHandler:
    def __init__(self):
        self.sio = socketio.Client()
        self.sio.connect(SOCKET_ENDPOINT)

    def __del__(self):
        self.disconnect()

    def disconnect(self):
        self.sio.disconnect()
        custom_logger.success('Websocket Disconnected')

    @BasicLogger(WS_LOGGER_MSG('Websockets'))
    def emit_switch(self, machine_section: str, machine: str, status: bool):
        self.sio.emit(SEND_SWITCH_TO_SERVER, data={
            "machineSection": machine_section,
            "machine": machine,
            "status": status,
        })

