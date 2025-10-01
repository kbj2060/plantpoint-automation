# Quick Start Guide

## 실행 환경 선택

### 🖥️ Windows 로컬에서 실행 (권장 - 현재 설정)

**언제 사용?**
- Windows에서 직접 개발하고 테스트할 때
- IDE 디버깅이 필요할 때
- 빠른 코드 수정 및 테스트

**설정:**
```bash
cd plantpoint-automation
cp .env.development .env
```

**실행:**
```bash
python main.py
```

**현재 설정 확인:**
```bash
python -c "from config import settings; print('MQTT:', settings.mqtt_host)"
# 출력: MQTT: 127.0.0.1 ✓
```

---

### 🐳 Docker 컨테이너 내부에서 실행

**언제 사용?**
- 프로덕션 환경
- Docker Compose로 전체 스택 실행
- Raspberry Pi에서 실행

**설정:**
```bash
cd plantpoint-automation
cp .env.docker .env
```

**실행 방법 1 - Docker Compose:**
```bash
docker-compose up automation
```

**실행 방법 2 - 기존 컨테이너에서:**
```bash
docker exec -it automation python main.py
```

**현재 설정 확인:**
```bash
docker exec automation python -c "from config import settings; print('MQTT:', settings.mqtt_host)"
# 출력: MQTT: mqtt ✓
```

---

## ⚠️ 일반적인 오류

### `[Errno 11001] getaddrinfo failed` - MQTT 연결 실패

**원인**: 잘못된 환경 설정

**증상:**
```
MQTT 브로커 연결 실패: mqtt:1883
에러: [Errno 11001] getaddrinfo failed
```

**해결:**

**Windows 로컬에서 실행하는 경우:**
```bash
# .env를 로컬 개발용으로 전환
cp .env.development .env

# 확인
python -c "from config import settings; print(settings.mqtt_host)"
# 반드시 127.0.0.1이 출력되어야 함
```

**Docker 내부에서 실행하는 경우:**
```bash
# .env를 Docker용으로 전환
cp .env.docker .env

# 확인
docker exec automation python -c "from config import settings; print(settings.mqtt_host)"
# 반드시 mqtt가 출력되어야 함
```

---

## 현재 상태

✅ **Windows 로컬 개발 환경으로 설정됨**

```
MQTT_HOST: 127.0.0.1     (localhost)
REDIS_HOST: 127.0.0.1    (localhost)
DB_HOST: 127.0.0.1       (localhost)
API_BASE_URL: http://127.0.0.1:9000
USE_REAL_GPIO: False     (Fake GPIO)
```

**실행 명령:**
```bash
python main.py
```

---

## 환경 전환

### Windows 로컬 → Docker 컨테이너

```bash
# 1. Docker용 설정으로 전환
cp .env.docker .env

# 2. Docker에서 실행
docker-compose up automation
```

### Docker 컨테이너 → Windows 로컬

```bash
# 1. 로컬 개발용 설정으로 전환
cp .env.development .env

# 2. 로컬에서 실행
python main.py
```

---

## 디버깅

### 현재 어떤 환경인지 모를 때

```bash
python -c "
from config import settings
env = 'Docker' if settings.mqtt_host == 'mqtt' else 'Local'
print(f'현재 환경: {env}')
print(f'MQTT_HOST: {settings.mqtt_host}')
"
```

### Docker 서비스 상태 확인

```bash
docker ps | grep -E "mqtt|redis|postgres|frontend"
```

출력 예시:
```
mqtt       0.0.0.0:1883->1883/tcp
redis      0.0.0.0:6379->6379/tcp
postgres   0.0.0.0:5432->5432/tcp
frontend   0.0.0.0:3000->80/tcp
```

### Python 캐시 문제

설정을 변경했는데도 반영이 안 될 때:
```bash
# Python 캐시 삭제
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null

# 다시 실행
python main.py
```

---

## 요약

| 실행 환경 | .env 파일 | MQTT_HOST | 실행 명령 |
|----------|----------|-----------|----------|
| **Windows 로컬** | `.env.development` | `127.0.0.1` | `python main.py` |
| **Docker 컨테이너** | `.env.docker` | `mqtt` | `docker-compose up automation` |

**현재**: Windows 로컬 환경 (✓)

**바로 실행**: `python main.py`
