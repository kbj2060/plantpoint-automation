from logger.custom_logger import custom_logger
from resources import redis, mqtt

class ResourceManager:
    @staticmethod
    def initialize():
        """MQTT 및 Redis 초기화"""
        try:
            custom_logger.info("리소스 초기화 중...")
            mqtt.client.loop_start()
            custom_logger.info("MQTT 브로커 연결 완료")
            custom_logger.info("Redis 연결 완료")
            return True
        except Exception as e:
            custom_logger.error(f"리소스 초기화 실패: {str(e)}")
            return False

    @staticmethod
    def cleanup():
        """리소스 정리"""
        redis.disconnect()
        mqtt.disconnect() 