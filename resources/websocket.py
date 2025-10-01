"""WebSocket client for PlantPoint automation system."""

from typing import Optional, Dict, Any
import threading
import json
import time

from websocket import WebSocketApp, WebSocketConnectionClosedException
from logger.custom_logger import custom_logger
from constants import SOCKET_ADDRESS


class WebSocket:
    """
    WebSocket client for real-time communication.

    Note: This class starts connection in __init__ which makes it hard to test.
    Consider using lazy connection initialization in future refactoring.
    """

    def __init__(
        self,
        url: str = SOCKET_ADDRESS,
        headers: Optional[Dict[str, str]] = None
    ) -> None:
        """
        Initialize WebSocket connection.

        Args:
            url: WebSocket server URL
            headers: Optional HTTP headers for connection

        Raises:
            ConnectionError: If connection fails within timeout
        """
        self.url = url
        self.headers = headers or {
            "Content-Type": "application/json",
            "Client-Type": "automation"
        }
        self.ws: Optional[WebSocketApp] = None
        self.connected = False
        self.thread: Optional[threading.Thread] = None

        # Start connection in background thread
        self.thread = threading.Thread(target=self._connect, daemon=True)
        self.thread.start()

        # Wait for connection (max 5 seconds)
        self._wait_for_connection()

    def _connect(self) -> None:
        """
        웹소켓 연결 및 이벤트 처리 설정

        This method runs in a separate thread.
        """
        try:
            self.ws = WebSocketApp(
                self.url,
                header=self.headers,
                on_open=self._on_open,
                on_error=self._on_error,
                on_close=self._on_close,
            )
            self.ws.run_forever()
        except Exception as e:
            custom_logger.error(f"WebSocket 연결 스레드 오류: {e}", exc_info=True)

    def _on_open(self, ws: WebSocketApp) -> None:
        """WebSocket connection opened callback."""
        self.connected = True
        custom_logger.info(f"WebSocket 연결 성공: {self.url}")

    def _on_error(self, ws: WebSocketApp, error: Exception) -> None:
        """WebSocket error callback."""
        custom_logger.error(f"WebSocket 오류: {error}", exc_info=True)

    def _on_close(
        self,
        ws: WebSocketApp,
        close_status_code: Optional[int],
        close_msg: Optional[str]
    ) -> None:
        """WebSocket connection closed callback."""
        self.connected = False
        custom_logger.info(
            f"WebSocket 연결 종료 (code: {close_status_code}, msg: {close_msg})"
        )

    def _wait_for_connection(self, timeout: int = 5) -> None:
        """
        연결 상태를 확인하며 대기

        Args:
            timeout: Maximum wait time in seconds

        Raises:
            ConnectionError: If connection not established within timeout
        """
        start_time = time.time()
        while not self.connected and time.time() - start_time < timeout:
            time.sleep(0.1)

        if not self.connected:
            error_msg = f"WebSocket 연결 타임아웃 ({timeout}초): {self.url}"
            custom_logger.error(error_msg)
            raise ConnectionError(error_msg)

    def send_message(self, event: str, data: Dict[str, Any]) -> bool:
        """
        WebSocket을 통해 메시지 전송

        Args:
            event: Event name
            data: Event data

        Returns:
            bool: True if message sent successfully, False otherwise
        """
        if not self.connected:
            custom_logger.error("WebSocket이 연결되지 않았습니다. 메시지 전송 실패.")
            return False

        if not self.ws:
            custom_logger.error("WebSocket 객체가 초기화되지 않았습니다.")
            return False

        message = json.dumps({'event': event, 'data': data})
        try:
            self.ws.send(message)
            custom_logger.debug(f"메시지 전송 성공: event={event}")
            return True
        except WebSocketConnectionClosedException:
            self.connected = False
            custom_logger.error("WebSocket 연결이 닫혔습니다. 메시지 전송 실패.")
            return False
        except Exception as e:
            custom_logger.error(f"메시지 전송 중 오류: {e}", exc_info=True)
            return False

    def disconnect(self) -> None:
        """WebSocket 연결 해제"""
        if self.ws:
            try:
                self.ws.close()
                self.connected = False
                custom_logger.info("WebSocket 연결 해제 완료")
            except Exception as e:
                custom_logger.error(f"WebSocket 연결 해제 중 오류: {e}", exc_info=True)
        else:
            custom_logger.warning("WebSocket이 초기화되지 않았습니다.") 