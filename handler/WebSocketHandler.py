import socketio
from constants import SOCKET_ENDPOINT, SEND_SWITCH_TO_SERVER, SEND_SWITCH_TO_CLIENT


# interface ControlSwitchEvent {
#   machineSection: string;
#   machine: string;
#   status: number | boolean;
# }

class WebSocketHandler:
    def __init__(self):
        self.sio = socketio.Client()
        self.sio.connect(f"http://{SOCKET_ENDPOINT}")

    def emit_switch(self, machine_section: str, machine: str, status: bool):
        self.sio.emit(SEND_SWITCH_TO_SERVER, {
            "machineSection": machine_section,
            "machine": machine,
            "status": status,
        })

