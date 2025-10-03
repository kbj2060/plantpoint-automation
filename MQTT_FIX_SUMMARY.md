# MQTT Connection Fix Summary

Date: 2025-10-02

## Problem

MQTT connection was failing with error:
```
[Errno 11001] getaddrinfo failed
```

This error occurred because the application was trying to connect to hostname `mqtt` which only exists inside Docker network.

## Root Cause

1. **Wrong websocket package**: `websocket` 0.2.1 was installed instead of `websocket-client`
2. **Configuration priority**: `.env` file (Docker config) was being used instead of `.env.development` (local dev config)
3. **MQTT host resolution**: hostname `mqtt` cannot be resolved outside Docker network

## Solution

### 1. Fixed WebSocket Import Issue

**Problem**: Wrong `websocket` package installed
```bash
# Wrong package
pip list | grep websocket
websocket  0.2.1
```

**Fix**: Install correct package
```bash
pip uninstall -y websocket
pip install websocket-client==1.8.0
```

**Result**: WebSocket imports now work correctly
```python
from websocket import WebSocketApp, WebSocketConnectionClosedException  # ✓ Works!
```

### 2. Improved Environment Configuration

**Files Modified**:
- `.env.development` - Updated with complete local development config
- `config.py` - Updated to try `.env.development` first, then `.env`
- `.env` → `.env.docker` - Renamed to avoid conflicts

**Key Changes in `.env.development`**:
```bash
# MQTT Configuration (for local development)
MQTT_HOST=127.0.0.1   # Changed from 'mqtt'
MQTT_PORT=1883

# Redis Configuration
REDIS_HOST=127.0.0.1  # Changed from 'redis'
REDIS_PORT=6379

# API Configuration
SIGNIN_URL=http://127.0.0.1:9000/authentication/signin
# ... other API endpoints

# GPIO Configuration
USE_REAL_GPIO=false   # Use fake GPIO for local testing
```

### 3. Enhanced MQTT Client

**File**: [resources/mqtt.py](plantpoint-automation/resources/mqtt.py)

**Improvements**:
- Added comprehensive type hints
- Better error messages with troubleshooting steps
- Connection state tracking
- Improved logging with host/port information
- Added MQTT return code descriptions

**Before**:
```python
class MQTTClient:
    def __init__(self):
        self.client = mqtt.Client()
        self.client.connect(MQTT_HOST, int(MQTT_PORT))
```

**After**:
```python
class MQTTClient:
    def __init__(
        self,
        host: str = MQTT_HOST,
        port: int = None,
        client_id: Optional[str] = None
    ) -> None:
        # ... comprehensive error handling with helpful messages
        try:
            self.client.connect(self.host, self.port, keepalive=60)
        except OSError as e:
            error_msg = (
                f"MQTT 브로커 연결 실패: {self.host}:{self.port}\n"
                f"해결 방법:\n"
                f"1. MQTT 브로커가 실행 중인지 확인\n"
                f"2. .env 파일에서 MQTT_HOST 확인\n"
                f"3. 로컬 개발: MQTT_HOST=127.0.0.1\n"
                f"4. Docker 내부: MQTT_HOST=mqtt"
            )
            raise ConnectionError(error_msg) from e
```

### 4. Enhanced WebSocket Client

**File**: [resources/websocket.py](plantpoint-automation/resources/websocket.py)

**Improvements**:
- Added complete type hints
- Better error handling and logging
- Return bool from `send_message()` for status checking
- More descriptive error messages
- Proper exception handling

## Testing

### Before Fix:
```bash
$ python -c "from resources.mqtt import MQTTClient"
# Error: [Errno 11001] getaddrinfo failed
```

### After Fix:
```bash
$ python -c "from resources.mqtt import MQTTClient; import time; m = MQTTClient(); time.sleep(2)"
# Output:
# 2025-10-02 01-37-41 | [INFO] | MQTT 브로커 연결 시도: 127.0.0.1:1883
# 2025-10-02 01-37-41 | [INFO] | MQTT 클라이언트 초기화 완료
# 2025-10-02 01-37-41 | [INFO] | MQTT 브로커 연결 성공: 127.0.0.1:1883
```

## Configuration Files

### For Local Development

Use `.env` (copied from `.env.development`):
```bash
MQTT_HOST=127.0.0.1
REDIS_HOST=127.0.0.1
DB_HOST=127.0.0.1
USE_REAL_GPIO=false
```

### For Docker Deployment

Use `.env.docker`:
```bash
MQTT_HOST=mqtt
REDIS_HOST=redis
DB_HOST=postgres
USE_REAL_GPIO=true
```

## How to Run

### Local Development (Outside Docker)

1. Ensure services are running in Docker:
```bash
docker ps | grep -E "mqtt|redis|postgres"
```

2. Use local environment:
```bash
cp .env.development .env  # or ensure .env has localhost configs
python main.py
```

### Inside Docker Container

1. Use Docker environment:
```bash
cp .env.docker .env  # or ensure .env has Docker hostnames
docker-compose up automation
```

## Files Modified

### Created/Updated:
- `.env.development` - Complete local development configuration
- `.env.docker` - Docker deployment configuration (renamed from .env)
- `config.py` - Multi-environment support
- `resources/mqtt.py` - Enhanced with type hints and error handling
- `resources/websocket.py` - Enhanced with type hints and error handling
- `MQTT_FIX_SUMMARY.md` - This file

### Key Improvements:
- ✓ Fixed websocket package conflict
- ✓ Improved MQTT error messages
- ✓ Added comprehensive type hints
- ✓ Better configuration management
- ✓ Environment-aware setup

## Troubleshooting

### MQTT Still Failing?

1. **Check MQTT broker is running**:
```bash
docker ps | grep mqtt
# Should show: mqtt container running with 0.0.0.0:1883->1883/tcp
```

2. **Check connectivity**:
```bash
telnet 127.0.0.1 1883
# Should connect successfully
```

3. **Check configuration**:
```bash
python -c "from config import settings; print(f'MQTT: {settings.mqtt_host}:{settings.mqtt_port}')"
# Should show: MQTT: 127.0.0.1:1883
```

4. **Check logs**:
```bash
docker logs mqtt
# Check for any MQTT broker errors
```

### WebSocket Import Error?

```bash
# Verify correct package is installed
pip show websocket-client
# Should show: websocket-client 1.8.0

# If wrong package installed:
pip uninstall -y websocket
pip install websocket-client==1.8.0
```

## Summary

The MQTT connection issue was resolved by:

1. ✅ Installing correct `websocket-client` package
2. ✅ Fixing environment configuration priority
3. ✅ Using localhost (127.0.0.1) for local development
4. ✅ Adding better error messages and logging
5. ✅ Improving code with type hints and documentation

MQTT connection now works successfully for local development! 🎉
