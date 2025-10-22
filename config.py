"""Configuration management using environment variables and .env files."""

import os
from typing import Optional
from dotenv import load_dotenv


class Settings:
    """Application settings loaded from environment variables."""

    def __init__(self):
        # Load .env files in order of priority
        load_dotenv(".env", override=True)
        load_dotenv(".env.development", override=False)

        # GPIO Configuration
        self.use_real_gpio: bool = self._get_bool("USE_REAL_GPIO", True)

        # Authentication
        self.api_username: str = self._get_required("API_USERNAME")
        self.api_password: str = self._get_required("API_PASSWORD")

        # API URLs
        self.api_base_url: str = os.getenv("API_BASE_URL", "http://localhost:3000")
        self.signin_url: str = os.getenv("SIGNIN_URL", "http://localhost:3000/api/auth/signin")
        self.automation_read_url: str = os.getenv("AUTOMATION_READ_URL", "http://localhost:3000/api/automation/read")
        self.interval_device_states_read_url: str = os.getenv(
            "INTERVAL_DEVICE_STATES_READ_URL",
            "http://localhost:3000/api/automation/interval/device/each/latest"
        )
        self.environment_each_latest_read_url: str = os.getenv(
            "ENVIRONMENT_EACH_LATEST_READ_URL",
            "http://localhost:3000/api/environment/each/latest"
        )
        self.environment_type_read_url: str = os.getenv(
            "ENVIRONMENT_TYPE_READ_URL",
            "http://localhost:3000/api/environment/type/read"
        )
        self.switch_each_latest_read_url: str = os.getenv(
            "SWITCH_EACH_LATEST_READ_URL",
            "http://localhost:3000/api/switch/each/latest"
        )
        self.machine_read_url: str = os.getenv(
            "MACHINE_READ_URL",
            "http://localhost:3000/api/machine/device/read"
        )
        self.sensor_read_url: str = os.getenv(
            "SENSOR_READ_URL",
            "http://localhost:3000/api/machine/sensor/read"
        )
        self.current_read_url: str = os.getenv(
            "CURRENT_READ_URL",
            "http://localhost:3000/api/machine/current/read"
        )

        # Database Configuration
        self.db_host: str = os.getenv("DB_HOST", "localhost")
        self.db_port: int = self._get_port("DB_PORT", 5432)
        self.db_name: str = os.getenv("DB_NAME", "plantpoint")
        self.db_user: str = os.getenv("DB_USER", "plantpoint")
        self.db_password: str = os.getenv("DB_PASSWORD", "plantpoint123")

        # MQTT Configuration
        self.mqtt_host: str = os.getenv("MQTT_HOST", "localhost")
        self.mqtt_port: int = self._get_port("MQTT_PORT", 1883)
        self.mqtt_client_id: Optional[str] = os.getenv("MQTT_CLIENT_ID")
        self.mqtt_keepalive: int = self._get_positive_int("MQTT_KEEPALIVE", 60)

        # Redis Configuration
        self.redis_host: str = os.getenv("REDIS_HOST", "localhost")
        self.redis_port: int = self._get_port("REDIS_PORT", 6379)
        self.redis_db: int = self._get_int("REDIS_DB", 0)

        # Logging Configuration
        self.log_dir: str = os.getenv("LOG_DIR", ".logs")
        self.log_max_bytes: int = self._get_int("LOG_MAX_BYTES", 10 * 1024 * 1024)
        self.log_backup_count: int = self._get_int("LOG_BACKUP_COUNT", 5)

        # Thread Configuration
        self.thread_check_interval: int = self._get_positive_int("THREAD_CHECK_INTERVAL", 60)

        # Automation Configuration
        self.current_buffer_size: int = self._get_int("CURRENT_BUFFER_SIZE", 5)
        self.target_required_count: int = self._get_int("TARGET_REQUIRED_COUNT", 3)

        # Thread Interval Configuration
        self.automation_interval: int = self._get_positive_int("AUTOMATION_INTERVAL", 60)  # 자동화 실행 주기 (초)
        self.sensor_read_interval: int = self._get_positive_int("SENSOR_READ_INTERVAL", 300)  # 센서값 읽기 주기 (초)
        self.current_monitor_interval: int = self._get_positive_int("CURRENT_MONITOR_INTERVAL", 10)  # 전류 모니터 주기 (초)

    def _get_required(self, key: str) -> str:
        """Get required environment variable."""
        value = os.getenv(key)
        if value is None:
            raise ValueError(f"Required environment variable {key} is not set")
        return value

    def _get_bool(self, key: str, default: bool) -> bool:
        """Get boolean environment variable."""
        value = os.getenv(key)
        if value is None:
            return default
        return value.lower() in ("true", "1", "yes", "on")

    def _get_int(self, key: str, default: int) -> int:
        """Get integer environment variable."""
        value = os.getenv(key)
        if value is None:
            return default
        try:
            return int(value)
        except ValueError:
            raise ValueError(f"Environment variable {key} must be an integer, got {value}")

    def _get_port(self, key: str, default: int) -> int:
        """Get port number environment variable with validation."""
        port = self._get_int(key, default)
        if not 1 <= port <= 65535:
            raise ValueError(f"Port {key} must be between 1 and 65535, got {port}")
        return port

    def _get_positive_int(self, key: str, default: int) -> int:
        """Get positive integer environment variable."""
        value = self._get_int(key, default)
        if value <= 0:
            raise ValueError(f"Environment variable {key} must be positive, got {value}")
        return value


# Global settings instance
settings = Settings()
