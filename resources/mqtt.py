"""MQTT client for PlantPoint automation system."""

import json
import uuid
from typing import Optional, Dict, Any
import paho.mqtt.client as mqtt
from logger.custom_logger import custom_logger
from constants import MQTT_HOST, MQTT_PORT, MQTT_ID

# MQTT Connection return codes
MQTT_RC_CODES = {
    0: "Connection successful",
    1: "Connection refused - incorrect protocol version",
    2: "Connection refused - invalid client identifier",
    3: "Connection refused - server unavailable",
    4: "Connection refused - bad username or password",
    5: "Connection refused - not authorized"
}


class MQTTClient:
    """
    MQTT client for device communication and automation control.

    Handles connection, reconnection, topic subscription, and message publishing.
    """

    def __init__(
        self,
        host: str = MQTT_HOST,
        port: int = None,
        client_id: Optional[str] = None
    ) -> None:
        """
        Initialize MQTT client.

        Args:
            host: MQTT broker hostname or IP
            port: MQTT broker port
            client_id: Unique client identifier (auto-generated if None)

        Raises:
            ConnectionError: If initial connection fails
        """
        self.host = host
        self.port = int(port or MQTT_PORT)
        self.client_id = client_id or MQTT_ID or f"automation_{uuid.uuid4().hex[:8]}"
        self.connected = False

        # Create MQTT client
        try:
            self.client = mqtt.Client(client_id=self.client_id)
        except Exception as e:
            custom_logger.error(f"MQTT 클라이언트 생성 실패: {e}")
            raise

        # Set callbacks
        self.client.on_connect = self._on_connect
        self.client.on_disconnect = self._on_disconnect

        # Connect to broker
        try:
            custom_logger.info(
                f"MQTT 브로커 연결 시도: {self.host}:{self.port} "
                f"(client_id: {self.client_id})"
            )
            self.client.connect(self.host, self.port, keepalive=60)
            custom_logger.info("MQTT 클라이언트 초기화 완료 (연결 대기 중...)")
        except OSError as e:
            error_msg = (
                f"MQTT 브로커 연결 실패: {self.host}:{self.port}\n"
                f"에러: {e}\n"
                f"해결 방법:\n"
                f"1. MQTT 브로커가 실행 중인지 확인: docker ps | grep mqtt\n"
                f"2. .env.development 파일에서 MQTT_HOST가 올바른지 확인\n"
                f"3. 로컬 개발: MQTT_HOST=127.0.0.1 또는 localhost\n"
                f"4. Docker 내부: MQTT_HOST=mqtt"
            )
            custom_logger.error(error_msg)
            raise ConnectionError(error_msg) from e
        except Exception as e:
            custom_logger.error(f"MQTT 연결 중 예상치 못한 오류: {e}", exc_info=True)
            raise

    def _on_connect(
        self,
        client: mqtt.Client,
        userdata: Any,
        flags: Dict[str, Any],
        rc: int
    ) -> None:
        """
        MQTT connection callback.

        Args:
            client: MQTT client instance
            userdata: User data
            flags: Connection flags
            rc: Connection result code
        """
        if rc == 0:
            self.connected = True
            custom_logger.info(
                f"MQTT 브로커 연결 성공: {self.host}:{self.port} "
                f"(client_id: {self.client_id})"
            )

            # Subscribe to topics
            topics = [
                ("environment/#", 0),
                ("automation/#", 0),
                ("switch/#", 0),
            ]
            self.client.subscribe(topics)
            custom_logger.info(
                f"MQTT 토픽 구독: {', '.join([t[0] for t in topics])}"
            )
        else:
            self.connected = False
            error_msg = MQTT_RC_CODES.get(rc, f"Unknown error code: {rc}")
            custom_logger.error(f"MQTT 브로커 연결 실패 (code: {rc}): {error_msg}")

    def _on_disconnect(
        self,
        client: mqtt.Client,
        userdata: Any,
        rc: int
    ) -> None:
        """
        MQTT disconnection callback.

        Args:
            client: MQTT client instance
            userdata: User data
            rc: Disconnection result code
        """
        self.connected = False
        if rc != 0:
            custom_logger.warning(
                f"MQTT 브로커 연결이 예기치 않게 종료됨 (code: {rc}). "
                f"자동 재연결 시도 중..."
            )
        else:
            custom_logger.info("MQTT 브로커 연결 정상 종료")

    def publish_message(
        self,
        topic: str,
        payload: Dict[str, Any],
        qos: int = 0,
        retain: bool = False
    ) -> bool:
        """
        MQTT 메시지 발행

        Args:
            topic: MQTT 토픽
            payload: 전송할 데이터
            qos: Quality of Service level (0, 1, or 2)
            retain: Whether to retain message

        Returns:
            bool: 발행 성공 여부
        """
        if not self.connected:
            custom_logger.error("MQTT 브로커에 연결되지 않았습니다. 메시지 발행 실패.")
            return False

        try:
            message = json.dumps(payload)
            info = self.client.publish(topic, message, qos=qos, retain=retain)

            if info.rc == mqtt.MQTT_ERR_SUCCESS:
                custom_logger.debug(f"MQTT 메시지 발행 성공: {topic}")
                return True
            else:
                error_msg = mqtt.error_string(info.rc)
                custom_logger.error(f"MQTT 메시지 발행 실패: {error_msg}")
                return False
        except Exception as e:
            custom_logger.error(f"MQTT 메시지 발행 중 오류: {e}", exc_info=True)
            return False

    def disconnect(self) -> None:
        """MQTT 브로커 연결 종료"""
        try:
            self.client.loop_stop()
            self.client.disconnect()
            self.connected = False
            custom_logger.info("MQTT 클라이언트 종료 완료")
        except Exception as e:
            custom_logger.error(f"MQTT 연결 종료 중 오류: {e}", exc_info=True)
