# PlantPoint Automation System

Smart farm automation system for controlling devices based on environmental conditions and schedules.

## Features

- **Multiple Automation Strategies**
  - Range-based: Control devices based on sensor value ranges
  - Interval-based: Control devices on time intervals
  - Target-based: Control devices to reach target sensor values

- **Real-time Monitoring**
  - Current monitoring for device safety
  - Environment sensor data collection
  - MQTT-based device communication

- **Flexible Configuration**
  - Pydantic-based settings with validation
  - Environment variable support
  - Type-safe configuration management

## Architecture

```
plantpoint-automation/
├── config.py              # Pydantic settings (USE THIS)
├── constants.py           # Deprecated compatibility layer
├── main.py                # Application entry point
├── store.py               # Data store for caching API responses
├── managers/              # Business logic managers
│   ├── automation_manager.py    # Automation orchestration
│   ├── current_manager.py       # Current monitoring
│   ├── nutrient_manager.py      # Placeholder for nutrient control
│   ├── resource_manager.py      # External resource management
│   └── thread_manager.py        # Thread lifecycle management
├── models/                # Data models
│   ├── automation/        # Automation strategy implementations
│   │   ├── base.py        # Base automation class
│   │   ├── factory.py     # Automation factory
│   │   ├── interval.py    # Interval automation
│   │   ├── range.py       # Range automation
│   │   ├── target.py      # Target automation
│   │   └── models.py      # Data models
│   ├── Current.py         # Current monitoring thread
│   ├── Machine.py         # Machine/device models
│   ├── Message.py         # MQTT message types
│   └── Response.py        # API response models (dataclasses)
├── resources/             # External resource clients
│   ├── http.py            # HTTP API client
│   ├── mqtt.py            # MQTT client
│   ├── redis.py           # Redis client
│   └── websocket.py       # WebSocket client
├── logger/                # Logging infrastructure
│   └── custom_logger.py   # Thread-aware logger
└── tests/                 # Test files
    ├── gpio.py            # GPIO test script
    └── gpio1.py           # GPIO test script

```

## Installation

### 1. Install Dependencies

```bash
pip3 install -r requirements.txt
```

### 2. Configure Environment

Create a `.env` file in the project root:

```bash
# GPIO Configuration
USE_REAL_GPIO=true

# Authentication
USERNAME=your_username
PASSWORD=your_password

# API Configuration
API_BASE_URL=http://localhost:3000
SIGNIN_URL=http://localhost:3000/api/auth/signin
AUTOMATION_READ_URL=http://localhost:3000/api/automation/read
INTERVAL_DEVICE_STATES_READ_URL=http://localhost:3000/api/automation/interval/device/each/latest
ENVIRONMENT_EACH_LATEST_READ_URL=http://localhost:3000/api/environment/each/latest
ENVIRONMENT_TYPE_READ_URL=http://localhost:3000/api/environment/type/read
SWITCH_EACH_LATEST_READ_URL=http://localhost:3000/api/switch/each/latest
MACHINE_READ_URL=http://localhost:3000/api/machine/device/read
SENSOR_READ_URL=http://localhost:3000/api/machine/sensor/read
CURRENT_READ_URL=http://localhost:3000/api/machine/current/read

# Database Configuration
DB_HOST=localhost
DB_PORT=5432
DB_NAME=plantpoint
DB_USER=postgres
DB_PASSWORD=postgres

# MQTT Configuration
MQTT_HOST=localhost
MQTT_PORT=1883

# Redis Configuration
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0

# WebSocket Configuration
WS_HOST=localhost
WS_PORT=3000

# Logging Configuration
LOG_DIR=.logs
LOG_MAX_BYTES=10485760
LOG_BACKUP_COUNT=5

# Thread Configuration
THREAD_CHECK_INTERVAL=60

# Automation Configuration
CURRENT_BUFFER_SIZE=5
TARGET_REQUIRED_COUNT=3
```

### 3. Run the Application

```bash
python3 main.py
```

## Automation Types

### Range Automation

Controls devices based on sensor value ranges with time constraints.

**Example**: Turn on fan when temperature is between 25-30°C during 09:00-18:00.

**Settings**:
```json
{
  "sensor": "temperature",
  "min_value": 25.0,
  "max_value": 30.0,
  "start_time": "09:00:00",
  "end_time": "18:00:00"
}
```

### Interval Automation

Controls devices on fixed time intervals.

**Example**: Turn on irrigation pump for 5 minutes every 2 hours.

**Settings**:
```json
{
  "duration": 300,
  "interval": 7200
}
```

### Target Automation

Controls devices to reach a target sensor value with hysteresis.

**Example**: Turn on heater when temperature drops below 20°C (with 3-reading buffer).

**Settings**:
```json
{
  "sensor": "temperature",
  "target_value": 20.0,
  "comparison": "less_than",
  "action": "on"
}
```

## Configuration Management

### New Way (Recommended)

```python
from config import settings

# Access configuration
print(settings.mqtt_host)
print(settings.db_port)
```

### Old Way (Deprecated)

```python
from constants import MQTT_HOST, DB_PORT  # Shows deprecation warning
```

## Development

### Code Quality

- **Type hints**: All functions/methods should have type hints
- **Docstrings**: Use Google-style docstrings
- **Error handling**: Use proper exception handling with logging
- **Testing**: Add tests for new functionality (TODO)

### Running Tests

```bash
# Test GPIO functionality (requires hardware or fake_rpi)
python tests/gpio.py
```

### Logging

Logs are written to `.logs/` directory with automatic rotation:
- `automation.log`: Automation manager logs
- `current.log`: Current monitoring logs
- `nutrient.log`: Nutrient manager logs (placeholder)
- `resource.log`: Resource manager logs

## Known Issues & TODOs

### High Priority

1. **Testing**: No test suite exists yet
   - Add pytest configuration
   - Create unit tests for automation strategies
   - Add integration tests for managers

2. **Nutrient Manager**: Currently a placeholder
   - Implement pH sensor integration
   - Implement EC sensor integration
   - Add pump and fan control

3. **Error Recovery**: Limited retry logic
   - Add exponential backoff for HTTP requests
   - Implement MQTT reconnection logic
   - Add circuit breaker pattern

### Medium Priority

1. **Token Refresh**: HTTP client doesn't refresh expired tokens
2. **Thread Health Monitoring**: Basic monitoring, needs improvement
3. **Metrics**: No metrics collection for monitoring

### Low Priority

1. **Async I/O**: Consider async/await for network operations
2. **GPIO Interrupts**: Use interrupts instead of polling for current monitoring
3. **Configuration Hot-reload**: Support reloading config without restart

## Contributing

1. Add type hints to all new code
2. Write docstrings for public functions/classes
3. Add appropriate logging
4. Update this README if adding new features

## License

See [LICENSE](LICENSE) file for details.

## System Flow

### 1. Initialization
- ResourceManager connects to MQTT, Redis
- Store loads data from HTTP API and caches in Redis
- Managers initialize their respective threads

### 2. Automation Execution
- AutomationManager creates automation threads based on category
- Each automation subscribes to relevant MQTT topics
- Automations control devices based on their strategy

### 3. Monitoring
- CurrentManager monitors device current consumption
- Automations send device state changes via MQTT
- All state changes are logged

### 4. Shutdown
- Graceful shutdown on SIGINT
- All threads are stopped
- Resources are cleaned up
- GPIO pins are released

## Troubleshooting

### MQTT Connection Fails
- Check MQTT broker is running: `mosquitto -v`
- Verify MQTT_HOST and MQTT_PORT in .env
- Check firewall settings

### Redis Connection Fails
- Check Redis is running: `redis-cli ping`
- Verify REDIS_HOST and REDIS_PORT in .env

### HTTP Authentication Fails
- Verify USERNAME and PASSWORD in .env
- Check API server is running
- Verify SIGNIN_URL is correct

### GPIO Errors
- Set `USE_REAL_GPIO=false` for testing without hardware
- Install fake_rpi: `pip install fake_rpi`
- Check GPIO permissions on Raspberry Pi

## Hardware Requirements

- Raspberry Pi (any model with GPIO)
- GPIO-connected devices (relays, sensors, etc.)
- Network connectivity for MQTT, HTTP, Redis

## Software Requirements

- Python 3.8+
- MQTT Broker (Mosquitto recommended)
- Redis Server
- Backend API Server
