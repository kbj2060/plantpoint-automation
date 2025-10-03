# 환경 전환 가이드 (Environment Switch Guide)

## 현재 설정 확인

```bash
python -c "from config import settings; print('MQTT:', settings.mqtt_host, '| REDIS:', settings.redis_host, '| DB:', settings.db_host)"
```

**출력 예시:**
- `MQTT: mqtt` → Docker 환경
- `MQTT: 127.0.0.1` → 로컬 개발 환경

---

## 🐳 Docker 환경으로 전환 (현재 설정)

**언제 사용?**
- Docker 컨테이너 내부에서 실행할 때
- Docker Compose로 전체 스택 실행 시
- 프로덕션 배포

**전환 방법:**
```bash
cd plantpoint-automation
cp .env.docker .env
```

**설정 값:**
```
MQTT_HOST=mqtt
REDIS_HOST=redis
DB_HOST=postgres
API_BASE_URL=http://frontend/api
USE_REAL_GPIO=true
```

**실행:**
```bash
docker-compose up automation
# 또는
docker exec -it automation python main.py
```

---

## 💻 로컬 개발 환경으로 전환

**언제 사용?**
- Docker 외부에서 로컬 개발할 때
- IDE에서 직접 디버깅할 때
- 빠른 코드 테스트

**전환 방법:**
```bash
cd plantpoint-automation
cp .env.development .env
```

**설정 값:**
```
MQTT_HOST=127.0.0.1
REDIS_HOST=127.0.0.1
DB_HOST=127.0.0.1
API_BASE_URL=http://127.0.0.1:9000
USE_REAL_GPIO=false
```

**전제 조건:**
Docker에서 서비스들이 localhost 포트로 노출되어 있어야 함:
```bash
docker ps | grep -E "mqtt|redis|postgres"
# 출력 예시:
# mqtt      0.0.0.0:1883->1883/tcp
# redis     0.0.0.0:6379->6379/tcp
# postgres  0.0.0.0:5432->5432/tcp
```

**실행:**
```bash
python main.py
```

---

## 빠른 전환 명령어

### Docker → 로컬
```bash
cp .env.development .env && echo "로컬 개발 환경으로 전환 완료"
```

### 로컬 → Docker
```bash
cp .env.docker .env && echo "Docker 환경으로 전환 완료"
```

---

## 문제 해결

### MQTT 연결 오류: `[Errno 11001] getaddrinfo failed`

**원인:** 로컬 환경인데 Docker 설정(`mqtt`)을 사용 중

**해결:**
```bash
cp .env.development .env
python -c "from config import settings; print('MQTT:', settings.mqtt_host)"
# 출력이 127.0.0.1이어야 함
```

### Docker에서 localhost로 연결 시도

**원인:** Docker 환경인데 로컬 설정(`127.0.0.1`)을 사용 중

**해결:**
```bash
cp .env.docker .env
python -c "from config import settings; print('MQTT:', settings.mqtt_host)"
# 출력이 mqtt여야 함
```

---

## 파일 구조

```
plantpoint-automation/
├── .env                  # 실제 사용 (git ignored)
├── .env.development      # 로컬 개발 템플릿 (git tracked)
└── .env.docker           # Docker 템플릿 (git tracked)
```

## 현재 상태

✅ **Docker 환경으로 설정 완료**

```
MQTT_HOST: mqtt
REDIS_HOST: redis
DB_HOST: postgres
API_BASE_URL: http://frontend/api
```

로컬 개발이 필요하면 위의 "로컬 개발 환경으로 전환" 섹션을 참고하세요.
