AUTOMATION_READ_URL = 'http://localhost:9000/automations/read'
SIGNIN_URL = 'http://localhost:9000/authentication/signin'
ENVIRONMENT_READ_URL = 'http://localhost:9000/environments/read/last'
SWITCH_READ_URL = 'http://localhost:9000/switches/read/last'
SWITCH_CREATE_URL = 'http://localhost:9000/switches/create'

ON = 1
OFF = 0

NAME = "Auto"
USERNAME = "auto"
PASSWORD = "dnjfem2006"

SOCKET_ENDPOINT = 'http://localhost:4000'
SEND_SWITCH_TO_SERVER = 'sendSwitchToServer',
SEND_SWITCH_TO_CLIENT = 'sendSwitchToClient'

DB_HOST = 'localhost'
DB_USER = 'root'
DB_PASSWORD = '01055646565'

GET_SECTION_SQL = 'SELECT section, environmentSection FROM iot.environment_section;'
GET_MACHINE_SQL = 'SELECT ms.machineSection, m.machine from iot.machine m ' \
                  'INNER JOIN iot.machine_section ms ON m.machineSectionId = ms.id'
GET_AUTO_SWITCH_SQL = lambda x: f"SELECT  s.created FROM iot.switch s INNER JOIN iot.user u ON s.controlledById = u.id WHERE u.username = \"auto\" AND s.machine = \"{x}\" ORDER BY s.id DESC LIMIT 1;"

AUTOMATION_DISABLED_REPORT = " : Disabled"
AUTOMATION_STAY_REPORT = " : Stay"
AUTOMATION_ON_REPORT = " : On"
AUTOMATION_OFF_REPORT = " : OFF"
