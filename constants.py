"""
Constants for PlantPoint Automation System.

This module provides backward compatibility for the old constants interface.
New code should import from config.py instead.

DEPRECATED: This module will be removed in a future version.
Please use: from config import settings
"""

import warnings
from config import settings

# Show deprecation warning
warnings.warn(
    "Importing from constants.py is deprecated. Use 'from config import settings' instead.",
    DeprecationWarning,
    stacklevel=2
)

# GPIO Configuration
USE_REAL_GPIO = settings.use_real_gpio

# Authentication
USERNAME = settings.api_username
PASSWORD = settings.api_password

# Database Configuration
DB_HOST = settings.db_host
DB_PORT = settings.db_port
DB_NAME = settings.db_name
DB_USER = settings.db_user
DB_PASSWORD = settings.db_password

# MQTT Configuration
MQTT_HOST = settings.mqtt_host
MQTT_PORT = settings.mqtt_port
MQTT_ID = settings.mqtt_client_id

# Redis Configuration
REDIS_HOST = settings.redis_host
REDIS_PORT = settings.redis_port

# API URLs
SIGNIN_URL = settings.signin_url
AUTOMATION_READ_URL = settings.automation_read_url
INTERVAL_DEVICE_STATES_READ_URL = settings.interval_device_states_read_url
ENVIRONMENT_EACH_LATEST_READ_URL = settings.environment_each_latest_read_url
ENVIRONMENT_TYPE_READ_URL = settings.environment_type_read_url
SWITCH_EACH_LATEST_READ_URL = settings.switch_each_latest_read_url
MACHINE_READ_URL = settings.machine_read_url
SENSOR_READ_URL = settings.sensor_read_url
CURRENT_READ_URL = settings.current_read_url

# Status Constants
ON = 1
OFF = 0

# Thread Configuration
TREAD_DURATION_LIMIT = settings.thread_check_interval

# Deprecated: These lambda functions are no longer used
# Kept for backward compatibility only
DB_LOGGER_MSG = lambda x: {
    "success_msg": f"Getting {x} From DB is Completed!",
    "error_msg": f"Cannot Get {x} From DB"
}
HTTP_LOGGER_GET_MSG = lambda x: {
    "success_msg": f"Getting {x} From HTTP is Completed!",
    "error_msg": f"Cannot Get {x} From HTTP"
}
HTTP_LOGGER_POST_MSG = lambda x: {
    "success_msg": f"Posting {x} To HTTP is Completed!",
    "error_msg": f"Cannot Post {x} To HTTP"
}
WS_LOGGER_MSG = lambda x: {
    "success_msg": f"Emitting {x} To Clients is Completed!",
    "error_msg": f"Cannot Emit {x} To Clients"
}
BOUNDARY_ERROR_MSG = "Out of Conditions Error. Please, Check Your Conditions."
