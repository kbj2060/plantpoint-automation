"""Configuration management using Pydantic Settings."""

from typing import Optional
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings with validation."""

    # GPIO Configuration
    use_real_gpio: bool = Field(default=True, description="Use real GPIO hardware")

    # Authentication
    api_username: str = Field(..., description="API username")
    api_password: str = Field(..., description="API password")

    # API URLs
    api_base_url: str = Field(default="http://localhost:3000", description="Base API URL")
    signin_url: str = Field(default="http://localhost:3000/api/auth/signin", description="Sign in endpoint")
    automation_read_url: str = Field(
        default="http://localhost:3000/api/automation/read",
        description="Automation read endpoint"
    )
    interval_device_states_read_url: str = Field(
        default="http://localhost:3000/api/automation/interval/device/each/latest",
        description="Interval device states endpoint"
    )
    environment_each_latest_read_url: str = Field(
        default="http://localhost:3000/api/environment/each/latest",
        description="Environment latest readings endpoint"
    )
    environment_type_read_url: str = Field(
        default="http://localhost:3000/api/environment/type/read",
        description="Environment type endpoint"
    )
    switch_each_latest_read_url: str = Field(
        default="http://localhost:3000/api/switch/each/latest",
        description="Switch latest states endpoint"
    )
    machine_read_url: str = Field(
        default="http://localhost:3000/api/machine/device/read",
        description="Machine read endpoint"
    )
    sensor_read_url: str = Field(
        default="http://localhost:3000/api/machine/sensor/read",
        description="Sensor read endpoint"
    )
    current_read_url: str = Field(
        default="http://localhost:3000/api/machine/current/read",
        description="Current read endpoint"
    )

    # Database Configuration
    db_host: str = Field(default="localhost", description="Database host")
    db_port: int = Field(default=5432, description="Database port")
    db_name: str = Field(default="plantpoint", description="Database name")
    db_user: str = Field(default="plantpoint", description="Database user")
    db_password: str = Field(default="plantpoint123", description="Database password")

    # MQTT Configuration
    mqtt_host: str = Field(default="localhost", description="MQTT broker host")
    mqtt_port: int = Field(default=1883, description="MQTT broker port")
    mqtt_client_id: Optional[str] = Field(default=None, description="MQTT client ID (auto-generated if None)")
    mqtt_keepalive: int = Field(default=60, description="MQTT keepalive interval in seconds")

    # Redis Configuration
    redis_host: str = Field(default="localhost", description="Redis host")
    redis_port: int = Field(default=6379, description="Redis port")
    redis_db: int = Field(default=0, description="Redis database number")

    # WebSocket Configuration
    ws_host: str = Field(default="localhost", description="WebSocket host")
    ws_port: int = Field(default=3000, description="WebSocket port")

    # Logging Configuration
    log_dir: str = Field(default=".logs", description="Log directory path")
    log_max_bytes: int = Field(default=10 * 1024 * 1024, description="Maximum log file size in bytes")
    log_backup_count: int = Field(default=5, description="Number of backup log files to keep")

    # Thread Configuration
    thread_check_interval: int = Field(
        default=60,
        description="Interval in seconds to check thread health"
    )

    # Automation Configuration
    current_buffer_size: int = Field(default=5, description="Buffer size for current monitoring")
    target_required_count: int = Field(
        default=3,
        description="Required count for target automation to trigger"
    )

    model_config = SettingsConfigDict(
        # Try .env.development first (for local dev), fallback to .env (for production/docker)
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )

    @field_validator("db_port", "mqtt_port", "redis_port", "ws_port")
    @classmethod
    def validate_port(cls, v: int) -> int:
        """Validate port numbers are in valid range."""
        if not 1 <= v <= 65535:
            raise ValueError(f"Port must be between 1 and 65535, got {v}")
        return v

    @field_validator("thread_check_interval", "mqtt_keepalive")
    @classmethod
    def validate_positive(cls, v: int) -> int:
        """Validate values are positive."""
        if v <= 0:
            raise ValueError(f"Value must be positive, got {v}")
        return v


# Global settings instance
settings = Settings()
