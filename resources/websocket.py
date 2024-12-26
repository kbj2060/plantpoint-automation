from websocket import WebSocketApp, WebSocketConnectionClosedException
from logger.custom_logger import custom_logger
from constants import SOCKET_ADDRESS
import threading
import json
import time

class WebSocket:
    def __init__(self, url=SOCKET_ADDRESS, headers={"Content-Type": "application/json", "Client-Type": "automation"}):
        self.url = url
        self.headers = headers or {}
        self.ws = None
        self.connected = False

        # 스레드로 WebSocket 연결 실행
        self.thread = threading.Thread(target=self._connect, daemon=True)
        self.thread.start()
        # 연결 대기 (최대 5초)
        self._wait_for_connection()

    def _connect(self):
        """웹소켓 연결 및 이벤트 처리 설정"""
        self.ws = WebSocketApp(
            self.url,
            self.headers,
            on_open=self._on_open,
            on_error=self._on_error,
            on_close=self._on_close,
        )
        self.ws.run_forever()

    def _on_open(self, ws):
        self.connected = True
        custom_logger.success("WebSocket 연결 성공!")

    def _on_error(self, ws, error):
        custom_logger.error(f"WebSocket 오류: {error}")

    def _on_close(self, ws, close_status_code, close_msg):
        self.connected = False
        custom_logger.success("WebSocket 연결 종료!")

    def _wait_for_connection(self, timeout=5):
        """연결 상태를 확인하며 대기"""
        start_time = time.time()
        while not self.connected and time.time() - start_time < timeout:
            time.sleep(0.1)
        if not self.connected:
            raise ConnectionError("WebSocket 연결에 실패했습니다.")

    def send_message(self, event: str, data: dict):
        """WebSocket을 통해 메시지 전송"""
        if self.connected:
            message = json.dumps({'event': event, 'data': data})
            try:
                self.ws.send(message)
            except WebSocketConnectionClosedException:
                custom_logger.error("WebSocket 연결이 닫혔습니다. 메시지 전송 실패.")
        else:
            custom_logger.error("WebSocket이 연결되지 않았습니다. 메시지 전송 실패.")

    def disconnect(self):
        """WebSocket 연결 해제"""
        if self.ws:
            self.ws.close()
            self.connected = False 