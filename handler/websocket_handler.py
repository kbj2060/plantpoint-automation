from constants import SEND_SWITCH_TO_SERVER, SOCKET_ENDPOINT
import socketio


class WebSocketHandler:
    def __init__(self):
        self.sio = socketio.Client()
        self.sio.connect(SOCKET_ENDPOINT,
                         socketio_path='/ws',
                         namespaces='/switch')

    def __del__(self):
        self.disconnect()

    def disconnect(self):
        self.sio.disconnect()

    def emit_switch(self, machine_section: str, machine: str, status: bool):
        self.sio.emit(SEND_SWITCH_TO_SERVER, data={
            "machineSection": machine_section,
            "machine": machine,
            "status": status,
        }, namespace='/switch')
