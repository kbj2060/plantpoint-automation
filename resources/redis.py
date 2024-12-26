import redis
from logger.custom_logger import custom_logger
from constants import REDIS_HOST, REDIS_PORT

class RedisClient:
    def __init__(self):
        try:
            self.client = redis.Redis(
                host=REDIS_HOST,
                port=int(REDIS_PORT),
                decode_responses=True  # 문자열 자동 디코딩
            )
            # 연결 테스트
            self.client.ping()
            custom_logger.success("Redis 연결 성공")
        except redis.ConnectionError as e:
            custom_logger.error(f"Redis 연결 실패: {str(e)}")
            raise
        except Exception as e:
            custom_logger.error(f"Redis 초기화 중 오류 발생: {str(e)}")
            raise

    def get(self, key: str) -> str:
        """Redis에서 값 조회"""
        try:
            value = self.client.get(key)
            if value is None:
                custom_logger.warning(f"Redis key not found: {key}")
            return value
        except Exception as e:
            custom_logger.error(f"Redis get 실패: {str(e)}")
            return None

    def set(self, key: str, value: str, expire: int = None) -> bool:
        """Redis에 값 저장"""
        try:
            self.client.set(key, value)
            if expire:
                self.client.expire(key, expire)
            custom_logger.info(f"Redis set 성공: {key}={value}")
            return True
        except Exception as e:
            custom_logger.error(f"Redis set 실패: {str(e)}")
            return False

    def delete(self, key: str) -> bool:
        """Redis에서 키 삭제"""
        try:
            return bool(self.client.delete(key))
        except Exception as e:
            custom_logger.error(f"Redis delete 실패: {str(e)}")
            return False

    def disconnect(self):
        """Redis 연결 종료"""
        try:
            self.client.close()
            custom_logger.success("Redis 연결 종료")
        except Exception as e:
            custom_logger.error(f"Redis 연결 종료 실패: {str(e)}")


# 싱글톤 인스턴스 생성
redis_client = RedisClient()

# 편의를 위한 함수들
def get(key: str) -> str:
    return redis_client.get(key)

def set(key: str, value: str, expire: int = None) -> bool:
    return redis_client.set(key, value, expire)

def delete(key: str) -> bool:
    return redis_client.delete(key)

def disconnect():
    redis_client.disconnect() 