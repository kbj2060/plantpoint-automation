from dotenv import load_dotenv
import os

# .env 파일 로드
load_dotenv('.env.development')

# 환경 변수 사용
USERNAME = os.getenv('USERNAME')
PASSWORD = os.getenv('PASSWORD')

DB_HOST = os.getenv('DB_HOST', 'localhost')
DB_PORT = os.getenv('DB_PORT', 5432)
DB_NAME = os.getenv('DB_NAME', 'plantpoint')
DB_USER = os.getenv('DB_USER', 'postgres')
DB_PASSWORD = os.getenv('DB_PASSWORD', 'postgres')

BACKEND_ADDRESS = os.getenv('BACKEND_ADDRESS')

SWITCH_SOCKET_ADDRESS = os.getenv('SWITCH_SOCKET_ADDRESS')
CURRENT_SOCKET_ADDRESS = os.getenv('CURRENT_SOCKET_ADDRESS')
SOCKET_ADDRESS = os.getenv('SOCKET_ADDRESS')
WS_SWITCH_EVENT = os.getenv('WS_SWITCH_EVENT')
WS_CURRENT_EVENT = os.getenv('WS_SWITCH_EVENT')

MQTT_HOST = os.getenv('MQTT_HOST')
MQTT_PORT = os.getenv('MQTT_PORT')
MQTT_ID = os.getenv('MQTT_ID')

# Redis 설정
REDIS_HOST = os.getenv('REDIS_HOST', '127.0.0.1')
REDIS_PORT = os.getenv('REDIS_PORT', 6379)


AUTOMATION_READ_URL = f'{BACKEND_ADDRESS}/automations'

SIGNIN_URL = f'{BACKEND_ADDRESS}/authentication/signin'

ENVIRONMENT_EACH_LATEST_READ_URL = f'{BACKEND_ADDRESS}/environment/each-latest'
ENVIRONMENT_TYPE_READ_URL = f'{BACKEND_ADDRESS}/environment/types'

INTERVAL_DEVICE_STATES_READ_URL = f'{BACKEND_ADDRESS}/switches/interval-states'
SWITCH_EACH_LATEST_READ_URL = f'{BACKEND_ADDRESS}/switches/each-latest'
SWITCH_CREATE_URL = f'{BACKEND_ADDRESS}/switches/create'

CURRENT_READ_URL = f'{BACKEND_ADDRESS}/current/read-all'

MACHINE_READ_URL = f'{BACKEND_ADDRESS}/device?type=machine'
SENSOR_READ_URL = f'{BACKEND_ADDRESS}/device?type=sensor'


ON = 1
OFF = 0

NAME = "Auto"
TREAD_DURATION_LIMIT=60

SEND_SWITCH_TO_SERVER = 'sendSwitchToServer'
SEND_CURRENT_TO_SERVER = 'sendCurrentToServer'

DB_LOGGER_MSG = lambda x: {"success_msg": f"Getting {x} From DB is Completed!",
                                "error_msg": f"Cannot Get {x} From DB"}
HTTP_LOGGER_GET_MSG = lambda x: {"success_msg": f"Getting {x} From HTTP is Completed!",
                                "error_msg": f"Cannot Get {x} From HTTP"}
HTTP_LOGGER_POST_MSG = lambda x: {"success_msg": f"Posting {x} To HTTP is Completed!",
                                "error_msg": f"Cannot Post {x} To HTTP"}
WS_LOGGER_MSG = lambda x: {"success_msg": f"Emitting {x} To Clients is Completed!",
                        "error_msg": f"Cannot Emit {x} To Clients"}
BOUNDARY_ERROR_MSG = "Out of Conditions Error. Please, Check Your Conditions."


