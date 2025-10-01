"""Resource manager for external connections (MQTT, Redis)."""

import time
from typing import Optional
from logger.custom_logger import custom_logger
from resources import redis, mqtt


class ResourceManager:
    """Manages external resource connections."""

    def __init__(self) -> None:
        self.mqtt_connected = False
        self.redis_connected = False

    def initialize(self, timeout: int = 10) -> bool:
        """
        MQTT 및 Redis 초기화

        Args:
            timeout: Connection timeout in seconds

        Returns:
            bool: True if all resources initialized successfully
        """
        try:
            custom_logger.info("리소스 초기화 중...")

            # Start MQTT loop
            mqtt.client.loop_start()

            # Wait for MQTT connection
            if self._wait_for_mqtt_connection(timeout):
                self.mqtt_connected = True
                custom_logger.info("MQTT 브로커 연결 완료")
            else:
                custom_logger.error(f"MQTT 연결 타임아웃 ({timeout}초)")
                return False

            # Verify Redis connection
            if self._verify_redis_connection():
                self.redis_connected = True
                custom_logger.info("Redis 연결 완료")
            else:
                custom_logger.error("Redis 연결 실패")
                return False

            return True
        except Exception as e:
            custom_logger.error(f"리소스 초기화 실패: {str(e)}", exc_info=True)
            return False

    def _wait_for_mqtt_connection(self, timeout: int) -> bool:
        """
        Wait for MQTT connection to establish.

        Args:
            timeout: Maximum wait time in seconds

        Returns:
            bool: True if connected within timeout
        """
        start_time = time.time()
        while time.time() - start_time < timeout:
            if mqtt.client.is_connected():
                return True
            time.sleep(0.1)
        return False

    def _verify_redis_connection(self) -> bool:
        """
        Verify Redis connection is working.

        Returns:
            bool: True if Redis is accessible
        """
        try:
            redis.redis_client.ping()
            return True
        except Exception as e:
            custom_logger.error(f"Redis ping 실패: {str(e)}")
            return False

    def cleanup(self) -> None:
        """리소스 정리"""
        try:
            if self.redis_connected:
                redis.disconnect()
                custom_logger.info("Redis 연결 해제 완료")
            if self.mqtt_connected:
                mqtt.disconnect()
                custom_logger.info("MQTT 연결 해제 완료")
        except Exception as e:
            custom_logger.error(f"리소스 정리 중 오류: {str(e)}", exc_info=True) 