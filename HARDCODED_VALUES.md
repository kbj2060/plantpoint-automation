# Automation 하드코딩 분석 문서

> **프로젝트:** plantpoint-automation (Python)
> **작성일:** 2025-10-22
> **목적:** 새로운 센서/기계 추가 시 수정이 필요한 하드코딩 위치 정리

---

## 📋 목차
1. [MQTT 토픽](#1-mqtt-토픽)
2. [GPIO 핀](#2-gpio-핀)
3. [센서 측정 범위](#3-센서-측정-범위-안전-임계값)
4. [타임아웃 값](#4-타임아웃-값)
5. [폴링/슬립 간격](#5-폴링슬립-간격)
6. [센서 타입 매핑](#6-센서-타입-매핑)
7. [자동화 타입](#7-자동화-타입)
8. [Redis 키](#8-redis-키)
9. [디바이스 이름](#9-디바이스-이름-데이터베이스-기반)
10. [이미 잘 정리된 상수들](#10-이미-잘-정리된-상수들-)
11. [새 디바이스 추가 체크리스트](#11-새-디바이스-추가-체크리스트)

---

## 1. MQTT 토픽

### 위치 및 하드코딩된 값

#### Machine.py
- [models/Machine.py](models/Machine.py#L18)
```python
topic = f'switch/{name}'
```

#### mqtt.py
- [resources/mqtt.py](resources/mqtt.py#L109-L113)
```python
mqtt_client.subscribe("environment/#")
mqtt_client.subscribe("automation/#")
mqtt_client.subscribe("switch/#")
```

#### base.py (자동화 베이스 클래스)
- [models/automation/base.py](models/automation/base.py)
```python
# Line 51
f"switch/{self.name}"

# Line 69
f"automation/{self.name}"

# Line 73
f"environment/{self.name}"

# Line 77
f"switch/{self.name}"
```

#### nutrient_manager.py
- [managers/nutrient_manager.py](managers/nutrient_manager.py#L461-L468)
```python
# 여러 MQTT 토픽
"environment/ph"
"environment/ec"
"environment/water_temperature"
# 등등
```

### MQTT 토픽 구조 정리

| 토픽 패턴 | 방향 | 용도 | 예시 |
|----------|------|------|------|
| `switch/{name}` | 구독 & 발행 | 스위치 제어 명령 및 상태 | `switch/led` |
| `automation/{name}` | 구독 | 자동화 설정 업데이트 | `automation/temperature` |
| `environment/{name}` | 구독 & 발행 | 환경 센서 값 | `environment/humidity` |
| `environment/#` | 구독 | 모든 환경 센서 값 | - |
| `automation/#` | 구독 | 모든 자동화 설정 | - |
| `switch/#` | 구독 | 모든 스위치 명령 | - |

### 개선 방안
```python
# config.py에 추가
class MQTTTopics:
    """MQTT 토픽 패턴 정의"""
    SWITCH = "switch/{name}"
    AUTOMATION = "automation/{name}"
    ENVIRONMENT = "environment/{name}"

    # 구독 패턴
    SUBSCRIBED = ["environment/#", "automation/#", "switch/#"]

    @staticmethod
    def switch(name: str) -> str:
        return f"switch/{name}"

    @staticmethod
    def automation(name: str) -> str:
        return f"automation/{name}"

    @staticmethod
    def environment(name: str) -> str:
        return f"environment/{name}"

# 사용 예시
mqtt_client.publish(MQTTTopics.environment("temperature"), value)
```

---

## 2. GPIO 핀

### 위치 및 하드코딩된 값

#### nutrient_manager.py
- [managers/nutrient_manager.py](managers/nutrient_manager.py#L53)
```python
DHT_PIN = 26  # DHT22 센서 GPIO 핀
```

#### AtlasI2C.py
- [drivers/AtlasI2C.py](drivers/AtlasI2C.py#L18)
```python
DEFAULT_BUS = 1  # I2C 버스 번호 (Raspberry Pi)
```

- [drivers/AtlasI2C.py](drivers/AtlasI2C.py#L20)
```python
DEFAULT_ADDRESS = 98  # 기본 I2C 센서 주소
```

- [drivers/AtlasI2C.py](drivers/AtlasI2C.py#L73)
```python
I2C_SLAVE = 0x703  # I2C ioctl 명령 상수
```

### GPIO/I2C 핀 정리

| 상수 | 값 | 용도 | 비고 |
|------|---|------|------|
| `DHT_PIN` | 26 | DHT22 온습도 센서 GPIO | GPIO 0-27 사용 가능 |
| `DEFAULT_BUS` | 1 | I2C 버스 번호 | Raspberry Pi 기본값 |
| `DEFAULT_ADDRESS` | 98 (0x62) | Atlas 센서 기본 I2C 주소 | pH, EC, RTD 센서 |
| `I2C_SLAVE` | 0x703 | I2C ioctl 명령 | 하드웨어 상수 |

### 개선 방안
```python
# config.py에 추가
DHT22_GPIO_PIN = int(os.getenv("DHT22_GPIO_PIN", 26))
I2C_BUS = int(os.getenv("I2C_BUS", 1))
I2C_DEFAULT_ADDRESS = int(os.getenv("I2C_DEFAULT_ADDRESS", 98))

# constants.py에 추가 (하드웨어 상수)
I2C_SLAVE = 0x703  # ioctl 명령, 변경 불필요
```

### 새 센서 추가 시 GPIO 핀 할당
1. DHT 계열: GPIO 핀 사용
2. I2C 센서: I2C 주소 확인 (기본 0x62, 변경 가능)
3. SPI 센서: SPI 핀 사용 (CE0, CE1)
4. 릴레이: GPIO 핀 사용 (데이터베이스에서 관리)

---

## 3. 센서 측정 범위 (안전 임계값)

### 위치
- [managers/nutrient_manager.py](managers/nutrient_manager.py#L64-L71)

### 하드코딩된 값
```python
# 센서 안전 범위
PH_MIN = 5.5
PH_MAX = 7.5
EC_MIN = 0.5
EC_MAX = 3.0
TEMP_MIN = 15.0
TEMP_MAX = 35.0
CO2_MIN = 300.0
CO2_MAX = 2000.0
```

### 추가 검증 범위
- [managers/nutrient_manager.py](managers/nutrient_manager.py#L290)
```python
0 <= co2_value <= 10000  # CO2 유효 범위
```

### 센서별 안전 범위 정리

| 센서 | 최소값 | 최대값 | 단위 | 용도 |
|------|-------|-------|------|------|
| pH | 5.5 | 7.5 | pH | 양액 pH 안전 범위 |
| EC | 0.5 | 3.0 | mS/cm | 양액 전기전도도 안전 범위 |
| 온도 | 15.0 | 35.0 | °C | 환경 온도 안전 범위 |
| CO2 | 300.0 | 2000.0 | ppm | CO2 농도 안전 범위 |
| CO2 유효 | 0 | 10000 | ppm | 센서 측정 유효 범위 |

### 용도
- 센서 값이 범위를 벗어나면 경고 로그 출력
- 비정상 값 필터링
- 안전 제어

### 개선 방안
```python
# config.py에 추가
SENSOR_LIMITS = {
    "ph": {
        "min": float(os.getenv("PH_MIN", 5.5)),
        "max": float(os.getenv("PH_MAX", 7.5)),
        "unit": "pH"
    },
    "ec": {
        "min": float(os.getenv("EC_MIN", 0.5)),
        "max": float(os.getenv("EC_MAX", 3.0)),
        "unit": "mS/cm"
    },
    "temperature": {
        "min": float(os.getenv("TEMP_MIN", 15.0)),
        "max": float(os.getenv("TEMP_MAX", 35.0)),
        "unit": "°C"
    },
    "co2": {
        "min": float(os.getenv("CO2_MIN", 300.0)),
        "max": float(os.getenv("CO2_MAX", 2000.0)),
        "valid_min": 0,
        "valid_max": 10000,
        "unit": "ppm"
    }
}

# 사용 예시
limits = SENSOR_LIMITS["ph"]
if not (limits["min"] <= ph_value <= limits["max"]):
    logger.warning(f"pH out of range: {ph_value}")
```

---

## 4. 타임아웃 값

### 위치 및 하드코딩된 값

#### AtlasI2C.py (I2C 센서 읽기)
- [drivers/AtlasI2C.py](drivers/AtlasI2C.py#L13)
```python
LONG_TIMEOUT = 1.5  # I2C 센서 읽기 타임아웃 (초)
```

- [drivers/AtlasI2C.py](drivers/AtlasI2C.py#L15)
```python
SHORT_TIMEOUT = .3  # I2C 센서 짧은 타임아웃 (초)
```

#### nutrient_manager.py (양액 관리)
- [managers/nutrient_manager.py](managers/nutrient_manager.py#L608)
```python
timeout = 300  # 물 배수 타임아웃 (5분)
```

- [managers/nutrient_manager.py](managers/nutrient_manager.py#L659)
```python
timeout = 600  # 물 공급 타임아웃 (10분)
```

- [managers/nutrient_manager.py](managers/nutrient_manager.py#L723)
```python
timeout = 300  # 양액 주입 타임아웃 (5분)
```

- [managers/nutrient_manager.py](managers/nutrient_manager.py#L495)
```python
mixing_duration: float = 60.0  # 기본 양액 혼합 시간 (초)
```

#### resource_manager.py
- [managers/resource_manager.py](managers/resource_manager.py#L16)
```python
timeout: int = 10  # 리소스 초기화 타임아웃 (초)
```

### 타임아웃 값 정리

| 작업 | 타임아웃 | 단위 | 용도 | 파일 |
|------|---------|------|------|------|
| I2C 센서 읽기 (긴) | 1.5 | 초 | Atlas 센서 안정화 대기 | AtlasI2C.py |
| I2C 센서 읽기 (짧은) | 0.3 | 초 | 빠른 센서 읽기 | AtlasI2C.py |
| 물 배수 | 300 | 초 (5분) | 양액통 배수 완료 대기 | nutrient_manager.py |
| 물 공급 | 600 | 초 (10분) | 양액통 급수 완료 대기 | nutrient_manager.py |
| 양액 주입 | 300 | 초 (5분) | 양액 주입 완료 대기 | nutrient_manager.py |
| 양액 혼합 | 60 | 초 (1분) | 양액 혼합 시간 | nutrient_manager.py |
| 리소스 초기화 | 10 | 초 | MQTT 연결 대기 | resource_manager.py |

### 개선 방안
```python
# config.py에 추가
# I2C 타임아웃
ATLAS_LONG_TIMEOUT = float(os.getenv("ATLAS_LONG_TIMEOUT", 1.5))
ATLAS_SHORT_TIMEOUT = float(os.getenv("ATLAS_SHORT_TIMEOUT", 0.3))

# 양액 관리 타임아웃
DRAIN_TIMEOUT = int(os.getenv("DRAIN_TIMEOUT", 300))
FILL_TIMEOUT = int(os.getenv("FILL_TIMEOUT", 600))
INJECT_TIMEOUT = int(os.getenv("INJECT_TIMEOUT", 300))
DEFAULT_MIX_DURATION = float(os.getenv("DEFAULT_MIX_DURATION", 60.0))

# 리소스 초기화
RESOURCE_INIT_TIMEOUT = int(os.getenv("RESOURCE_INIT_TIMEOUT", 10))
```

---

## 5. 폴링/슬립 간격

### 위치 및 하드코딩된 값

#### nutrient_manager.py
- [managers/nutrient_manager.py](managers/nutrient_manager.py#L245)
```python
time.sleep(2)  # DHT22 센서 재시도 지연
```

- [managers/nutrient_manager.py](managers/nutrient_manager.py#L616)
```python
time.sleep(1)  # 수위 센서 폴링 간격 (배수)
```

- [managers/nutrient_manager.py](managers/nutrient_manager.py#L667)
```python
time.sleep(2)  # 수위 센서 폴링 간격 (급수)
```

- [managers/nutrient_manager.py](managers/nutrient_manager.py#L742)
```python
time.sleep(0.5)  # 유량 센서 폴링 간격
```

#### resource_manager.py
- [managers/resource_manager.py](managers/resource_manager.py#L67)
```python
time.sleep(0.1)  # MQTT 연결 확인 간격
```

#### thread_manager.py
- [managers/thread_manager.py](managers/thread_manager.py#L67)
```python
60  # 상태 보고 간격 (1분)
```

### 폴링/슬립 간격 정리

| 작업 | 간격 | 단위 | 용도 | 파일 |
|------|-----|------|------|------|
| DHT22 재시도 | 2 | 초 | 센서 읽기 실패 시 재시도 | nutrient_manager.py |
| 수위 폴링 (배수) | 1 | 초 | 수위 센서 상태 확인 | nutrient_manager.py |
| 수위 폴링 (급수) | 2 | 초 | 수위 센서 상태 확인 | nutrient_manager.py |
| 유량 폴링 | 0.5 | 초 | 유량 센서 데이터 읽기 | nutrient_manager.py |
| MQTT 연결 확인 | 0.1 | 초 | 연결 상태 체크 | resource_manager.py |
| 상태 보고 | 60 | 초 | 주기적 상태 로그 | thread_manager.py |

### 개선 방안
```python
# config.py에 추가
# 센서 폴링 간격
DHT_RETRY_DELAY = float(os.getenv("DHT_RETRY_DELAY", 2))
WATER_LEVEL_POLL_INTERVAL_DRAIN = float(os.getenv("WATER_LEVEL_POLL_INTERVAL_DRAIN", 1))
WATER_LEVEL_POLL_INTERVAL_FILL = float(os.getenv("WATER_LEVEL_POLL_INTERVAL_FILL", 2))
FLOW_POLL_INTERVAL = float(os.getenv("FLOW_POLL_INTERVAL", 0.5))

# 시스템 간격
MQTT_CHECK_INTERVAL = float(os.getenv("MQTT_CHECK_INTERVAL", 0.1))
STATUS_REPORT_INTERVAL = int(os.getenv("STATUS_REPORT_INTERVAL", 60))
```

---

## 6. 센서 타입 매핑

### 위치
- [managers/nutrient_manager.py](managers/nutrient_manager.py#L43-L49)

### 하드코딩된 값
```python
sensor_name_mapping = {
    "RTD": "water_temperature",  # 수온 센서
    "PH": "ph",                   # pH 센서
    "EC": "ec",                   # EC 센서
    "co2": "co2",                 # CO2 센서
    "temperature": "temperature"  # 온도 센서
}
```

### 센서 모듈 타입 → 데이터베이스 이름 매핑

| 센서 모듈 | 데이터베이스 이름 | 설명 |
|----------|-----------------|------|
| `RTD` | `water_temperature` | Atlas Scientific RTD 수온 센서 |
| `PH` | `ph` | Atlas Scientific pH 센서 |
| `EC` | `ec` | Atlas Scientific EC 센서 |
| `co2` | `co2` | CO2 센서 |
| `temperature` | `temperature` | DHT22 온도 |

### 용도
I2C 센서 모듈 타입을 데이터베이스 센서 이름으로 변환

### 개선 방안
```python
# constants.py 또는 config.py에 추가
SENSOR_NAME_MAPPING = {
    "RTD": "water_temperature",
    "PH": "ph",
    "EC": "ec",
    "co2": "co2",
    "temperature": "temperature",
    "humidity": "humidity"
}

# 새 센서 추가 시
SENSOR_NAME_MAPPING["NEW_SENSOR_MODULE"] = "new_sensor_name"
```

---

## 7. 자동화 타입

### 위치
- [models/automation/factory.py](models/automation/factory.py#L21-L25)

### 하드코딩된 값
```python
automation_types = {
    'range': RangeAutomation,      # 범위 자동화 (LED 시간 제어)
    'interval': IntervalAutomation, # 주기 자동화 (분무기)
    'target': TargetAutomation     # 목표값 자동화 (온도, 습도 등)
}
```

### 자동화 타입 설명

| 타입 | 클래스 | 용도 | 예시 |
|------|--------|------|------|
| `range` | RangeAutomation | 시간 범위 제어 | LED 06:00-18:00 ON |
| `interval` | IntervalAutomation | 주기적 실행 | 30분마다 5분간 분무 |
| `target` | TargetAutomation | 목표값 기반 제어 | 온도 25℃ ±5℃ 유지 |

### 개선 방안
```python
# constants.py에 추가
AUTOMATION_TYPES = ['range', 'interval', 'target']

# 검증 함수
def validate_automation_type(automation_type: str) -> bool:
    return automation_type in AUTOMATION_TYPES
```

---

## 8. Redis 키

### 위치
- [store.py](store.py#L51-L58)

### 하드코딩된 값
```python
# Redis 캐시 키
'environment_type'                # 환경 센서 타입 목록
'environments'                    # 환경 센서 값 목록
'switches'                        # 스위치 상태 목록
'machines'                        # 기계 목록
'sensors'                         # 센서 목록
'automations'                     # 자동화 설정 목록
'interval_automated_switches'     # 주기 자동화 상태
'currents'                        # 전류 측정값 목록
```

### 추가 Redis 키 패턴
- [models/automation/interval.py](models/automation/interval.py#L207)
```python
'interval_automated_switches'  # 주기 자동화 스위치 상태
```

### Redis 키 구조 정리

| 키 | 타입 | 용도 | 값 형식 |
|----|------|------|---------|
| `environment_type` | String (JSON) | 센서 타입 목록 | `[{id, name}, ...]` |
| `environments` | String (JSON) | 센서 현재값 목록 | `[{name, value, ...}, ...]` |
| `switches` | String (JSON) | 스위치 상태 목록 | `[{name, status, ...}, ...]` |
| `machines` | String (JSON) | 기계 목록 | `[{id, name, ...}, ...]` |
| `sensors` | String (JSON) | 센서 목록 | `[{id, name, ...}, ...]` |
| `automations` | String (JSON) | 자동화 설정 | `[{id, device, ...}, ...]` |
| `interval_automated_switches` | Hash | 주기 자동화 상태 | `{device_name: state}` |
| `currents` | String (JSON) | 전류 측정값 | `[{device, current, ...}, ...]` |

### 개선 방안
```python
# config.py 또는 constants.py에 추가
REDIS_KEYS = {
    'ENVIRONMENT_TYPE': 'environment_type',
    'ENVIRONMENTS': 'environments',
    'SWITCHES': 'switches',
    'MACHINES': 'machines',
    'SENSORS': 'sensors',
    'AUTOMATIONS': 'automations',
    'INTERVAL_AUTOMATED_SWITCHES': 'interval_automated_switches',
    'CURRENTS': 'currents'
}

# 사용 예시
redis_client.get(REDIS_KEYS['ENVIRONMENTS'])
```

---

## 9. 디바이스 이름 (데이터베이스 기반)

### 위치
- [managers/nutrient_manager.py](managers/nutrient_manager.py)

### 하드코딩된 디바이스 이름

| 라인 | 디바이스 이름 | 타입 | 용도 |
|------|-------------|------|------|
| 594 | `"drain_valve"` | 기계 | 양액통 배수 밸브 |
| 645 | `"fill_valve"` | 기계 | 양액통 급수 밸브 |
| 706-707 | `f"nutrient_{type}_pump"` | 기계 | 양액 펌프 (A, B 등) |
| 706-707 | `f"nutrient_{type}_flow"` | 센서 | 양액 유량 센서 |
| 768 | `"mixer"` | 기계 | 양액 믹서 |
| 184, 530, 600, 651 | `"waterlevel"` | 센서 | 수위 센서 |

### 디바이스 명명 규칙

#### 밸브류
- `drain_valve` - 배수 밸브
- `fill_valve` - 급수 밸브

#### 양액 펌프/센서
- `nutrient_a_pump` - 양액 A 펌프
- `nutrient_b_pump` - 양액 B 펌프
- `nutrient_a_flow` - 양액 A 유량 센서
- `nutrient_b_flow` - 양액 B 유량 센서

#### 기타
- `mixer` - 양액 믹서
- `waterlevel` - 수위 센서

### ⚠️ 중요
이들은 **데이터베이스에서 관리**되는 값입니다. 코드에서는 데이터베이스에서 가져온 디바이스 이름을 사용하지만, 특정 기능(양액 관리 등)을 위해 **표준 명명 규칙**을 따라야 합니다.

### 권장 사항
```python
# constants.py에 문서화
class DeviceNames:
    """
    표준 디바이스 명명 규칙

    데이터베이스의 device.name 필드는 이 규칙을 따라야 함
    """
    # 밸브
    DRAIN_VALVE = "drain_valve"
    FILL_VALVE = "fill_valve"

    # 양액 관리
    NUTRIENT_PUMP_FORMAT = "nutrient_{type}_pump"  # type: a, b, c, ...
    NUTRIENT_FLOW_FORMAT = "nutrient_{type}_flow"

    # 믹서
    MIXER = "mixer"

    # 센서
    WATER_LEVEL = "waterlevel"

    @staticmethod
    def nutrient_pump(nutrient_type: str) -> str:
        """양액 펌프 이름 생성 (예: nutrient_a_pump)"""
        return f"nutrient_{nutrient_type.lower()}_pump"

    @staticmethod
    def nutrient_flow(nutrient_type: str) -> str:
        """양액 유량 센서 이름 생성 (예: nutrient_a_flow)"""
        return f"nutrient_{nutrient_type.lower()}_flow"
```

---

## 10. 이미 잘 정리된 상수들 ✅

### constants.py
- [constants.py](constants.py#L56-L57)

```python
# 기계 상태
ON = 1
OFF = 0
```

### nutrient_manager.py (클래스 상수)
- [managers/nutrient_manager.py](managers/nutrient_manager.py#L72-L73)

```python
# 수위 센서 상태
WATER_LEVEL_LOW = 1
WATER_LEVEL_HIGH = 0
```

### models/automation/models.py
- [models/automation/models.py](models/automation/models.py#L62-L67)

```python
class TopicType(Enum):
    """MQTT 토픽 타입"""
    automation = "automation"
    current = "current"
    switch = "switch"
    environment = "environment"
```

### config.py ✅
대부분의 설정이 **환경변수**로 잘 관리되고 있습니다:

```python
# 데이터베이스
db_host: str = os.getenv("DB_HOST", "localhost")
db_port: int = int(os.getenv("DB_PORT", 5432))
db_name: str = os.getenv("DB_NAME", "plantpoint")
db_user: str = os.getenv("DB_USER", "llewyn")
db_password: str = os.getenv("DB_PASSWORD", "1234")

# MQTT
mqtt_host: str = os.getenv("MQTT_HOST", "localhost")
mqtt_port: int = int(os.getenv("MQTT_PORT", 1883))

# Redis
redis_host: str = os.getenv("REDIS_HOST", "localhost")
redis_port: int = int(os.getenv("REDIS_PORT", 6379))

# API 엔드포인트
api_base_url: str = os.getenv("API_BASE_URL", "http://localhost:3000")

# 자동화
target_required_count: int = int(os.getenv("TARGET_REQUIRED_COUNT", 3))
```

✅ **좋은 사례:** 환경변수로 설정 가능, 기본값 제공

---

## 11. 새 디바이스 추가 체크리스트

### ✅ 센서 추가 시

#### 1. 데이터베이스
- [ ] `device` 테이블에 센서 추가
```sql
INSERT INTO device (name, type, sensor_pin)
VALUES ('new_sensor', 'sensor', 1);
```
- [ ] `environment_type` 테이블에 센서 타입 추가
```sql
INSERT INTO environment_type (name)
VALUES ('new_sensor');
```

#### 2. 센서 드라이버 구현
- [ ] `drivers/` 또는 `managers/` 에 센서 읽기 함수 구현
- [ ] I2C 센서인 경우: `AtlasI2C.py` 참고
- [ ] GPIO 센서인 경우: DHT22 예시 참고
- [ ] SPI 센서인 경우: 별도 드라이버 작성

#### 3. 센서 이름 매핑 (I2C 센서인 경우)
- [ ] `managers/nutrient_manager.py`의 `sensor_name_mapping`에 추가
```python
sensor_name_mapping = {
    "RTD": "water_temperature",
    "PH": "ph",
    "EC": "ec",
    "NEW_MODULE": "new_sensor"  # 추가
}
```

#### 4. 센서 측정 범위 설정 (필요시)
- [ ] `managers/nutrient_manager.py`에 안전 범위 상수 추가
```python
NEW_SENSOR_MIN = 0.0
NEW_SENSOR_MAX = 100.0
```

#### 5. MQTT 발행
- [ ] 센서 값을 MQTT로 발행하는 코드 추가
```python
mqtt_client.publish(f"environment/{sensor_name}", value)
```

#### 6. Redis 캐시 (필요시)
- [ ] `store.py`의 환경 센서 목록 업데이트 확인

#### 7. 테스트
- [ ] 센서 읽기 테스트
- [ ] MQTT 발행 확인
- [ ] 백엔드 데이터 저장 확인
- [ ] 프론트엔드 표시 확인

### ✅ 기계 추가 시

#### 1. 데이터베이스
- [ ] `device` 테이블에 기계 추가
```sql
INSERT INTO device (name, type, relay_pin, current_pin)
VALUES ('new_machine', 'machine', 62, 22);
```

#### 2. GPIO 제어
- [ ] `models/Machine.py` 또는 별도 클래스 생성
- [ ] GPIO 핀 번호는 데이터베이스에서 가져옴
- [ ] 릴레이 ON/OFF 제어 로직 구현

#### 3. MQTT 구독
- [ ] `resources/mqtt.py`에서 자동으로 처리됨
- [ ] 토픽: `switch/{machine_name}`
- [ ] 메시지 형식: `{"name": "machine_name", "status": 1}`

#### 4. 자동화 타입 결정
- [ ] **Interval:** 주기적 실행 (예: 분무기)
  - `models/automation/interval.py` 참고
- [ ] **Range:** 시간 범위 제어 (예: LED)
  - `models/automation/range.py` 참고
- [ ] **Target:** 목표값 기반 제어 (예: 팬)
  - `models/automation/target.py` 참고

#### 5. 자동화 모델 연결
- [ ] `models/automation/base.py` 상속
- [ ] `update()` 메서드 구현
- [ ] 센서 값 기반 제어 로직 작성

#### 6. Redis 캐시
- [ ] `store.py`의 기계 목록/스위치 상태 업데이트 확인

#### 7. 테스트
- [ ] GPIO 제어 테스트
- [ ] MQTT 명령 수신 확인
- [ ] 자동화 동작 테스트
- [ ] 전류 측정 확인 (있는 경우)

### ✅ 양액 관리 디바이스 추가 시

**표준 명명 규칙을 따라야 함!**

#### 양액 펌프/유량 센서
- [ ] 데이터베이스 이름: `nutrient_{type}_pump`, `nutrient_{type}_flow`
- [ ] 예: `nutrient_a_pump`, `nutrient_a_flow`

#### 밸브
- [ ] 배수: `drain_valve`
- [ ] 급수: `fill_valve`

#### 믹서
- [ ] `mixer`

#### 수위 센서
- [ ] `waterlevel`

### ✅ 공통

1. **환경변수 설정**
   - [ ] `.env` 파일에 필요한 설정 추가
   - [ ] GPIO 핀, I2C 주소 등

2. **백엔드 연동**
   - [ ] 백엔드에 디바이스 등록 확인
   - [ ] 데이터베이스 동기화

3. **프론트엔드 연동**
   - [ ] 프론트엔드에서 디바이스 표시 확인
   - [ ] 자동화 설정 가능 확인

4. **문서 업데이트**
   - [ ] 이 문서 업데이트
   - [ ] 디바이스 명명 규칙 문서화
   - [ ] GPIO 핀 할당 문서화

---

## 12. 권장 상수 파일 구조

Python 프로젝트 개선을 위한 권장 디렉토리 구조:

```
plantpoint-automation/
├── config.py                    # ✅ 환경변수 설정 (이미 잘 정리됨)
├── constants.py                 # ✅ 기본 상수 (ON, OFF)
├── settings/                    # 새로 생성 권장
│   ├── __init__.py
│   ├── mqtt_topics.py          # MQTT 토픽 패턴
│   ├── sensor_limits.py        # 센서 측정 범위
│   ├── timeouts.py             # 타임아웃 값들
│   ├── polling_intervals.py    # 폴링 간격
│   └── redis_keys.py           # Redis 키 패턴
├── models/
├── managers/
├── drivers/
└── ...
```

### 예시: settings/mqtt_topics.py
```python
"""MQTT 토픽 패턴 정의"""

class MQTTTopics:
    SWITCH = "switch/{name}"
    AUTOMATION = "automation/{name}"
    ENVIRONMENT = "environment/{name}"

    SUBSCRIBED = ["environment/#", "automation/#", "switch/#"]

    @staticmethod
    def switch(name: str) -> str:
        return f"switch/{name}"

    @staticmethod
    def automation(name: str) -> str:
        return f"automation/{name}"

    @staticmethod
    def environment(name: str) -> str:
        return f"environment/{name}"
```

### 예시: settings/sensor_limits.py
```python
"""센서 측정 범위 및 안전 임계값"""
import os

SENSOR_LIMITS = {
    "ph": {
        "min": float(os.getenv("PH_MIN", 5.5)),
        "max": float(os.getenv("PH_MAX", 7.5)),
        "unit": "pH"
    },
    "ec": {
        "min": float(os.getenv("EC_MIN", 0.5)),
        "max": float(os.getenv("EC_MAX", 3.0)),
        "unit": "mS/cm"
    },
    "temperature": {
        "min": float(os.getenv("TEMP_MIN", 15.0)),
        "max": float(os.getenv("TEMP_MAX", 35.0)),
        "unit": "°C"
    },
    "co2": {
        "min": float(os.getenv("CO2_MIN", 300.0)),
        "max": float(os.getenv("CO2_MAX", 2000.0)),
        "valid_min": 0,
        "valid_max": 10000,
        "unit": "ppm"
    }
}
```

---

## 13. 우선순위별 개선 작업

### 🔴 우선순위 1 (즉시 수정)

1. **MQTT 토픽 패턴 중앙화**
   - `settings/mqtt_topics.py` 생성
   - 모든 토픽 패턴을 한 곳에서 관리
   - 영향: 6개 이상 파일

2. **센서 측정 범위 환경변수화**
   - `settings/sensor_limits.py` 생성
   - 환경변수로 커스터마이징 가능
   - 영향: 안전 제어 로직

### 🟠 우선순위 2 (높음)

1. **타임아웃 값 환경변수화**
   - `settings/timeouts.py` 생성
   - 모든 타임아웃 값을 `config.py`에 추가
   - 영향: 양액 관리, 센서 읽기

2. **GPIO 핀 환경변수화**
   - `config.py`에 GPIO 핀 설정 추가
   - DHT_PIN, I2C_BUS 등
   - 영향: 하드웨어 변경 시

3. **Redis 키 상수화**
   - `settings/redis_keys.py` 생성
   - `REDIS_KEYS` 딕셔너리로 관리
   - 영향: 캐시 일관성

### 🟡 우선순위 3 (중간)

1. **폴링 간격 환경변수화**
   - `settings/polling_intervals.py` 생성
   - 모든 `time.sleep()` 값을 상수로

2. **센서 이름 매핑 상수화**
   - `constants.py`에 `SENSOR_NAME_MAPPING` 추가

3. **디바이스 명명 규칙 문서화**
   - `DeviceNames` 클래스 생성
   - 표준 명명 규칙 정의

### 🟢 우선순위 4 (낮음 - 문서화)

1. **GPIO 핀 할당 문서**
   - 사용 중인 핀 목록
   - 예약된 핀 표시

2. **센서 추가 가이드**
   - 단계별 체크리스트
   - 예시 코드

---

## 14. 추가 참고 사항

### 🔗 관련 문서
- 프론트엔드 하드코딩 분석: `../plantpoint-frontend-vite/HARDCODED_VALUES.md`
- 백엔드 하드코딩 분석: `../plantpoint-backend/HARDCODED_VALUES.md`

### 📊 하드코딩 항목 요약

| 카테고리 | 항목 수 | 우선순위 1 | 우선순위 2 |
|---------|--------|-----------|-----------|
| MQTT 토픽 | 10+ | ✓ | |
| GPIO 핀 | 4 | | ✓ |
| 센서 범위 | 8+ | ✓ | |
| 타임아웃 | 7 | | ✓ |
| 폴링 간격 | 6 | | |
| Redis 키 | 8 | | ✓ |

### ⚠️ 주의사항

1. **환경변수 변경 시**
   - `.env` 파일 업데이트
   - 서비스 재시작 필요

2. **MQTT 토픽 변경 시**
   - 백엔드와 동시 수정 필요
   - 구독/발행 모두 확인

3. **GPIO 핀 변경 시**
   - 하드웨어 연결 확인
   - 충돌 방지 (다른 디바이스와)

4. **디바이스 명명 규칙**
   - 양액 관리 기능은 특정 이름 패턴에 의존
   - 변경 시 코드 수정 필요

---

**마지막 업데이트:** 2025-10-22
**담당자:** Automation Team
**버전:** 1.0
