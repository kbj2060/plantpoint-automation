# Environment Files Guide

## 파일 구조

```
plantpoint-automation/
├── .env                  # 실제 사용되는 설정 파일 (git ignored)
├── .env.development      # 로컬 개발용 템플릿 (git tracked)
└── .env.docker           # Docker 배포용 템플릿 (git tracked)
```

## Settings 클래스가 설정을 로드하는 방식

`config.py`의 `Settings` 클래스는 Pydantic Settings를 사용하여 환경 변수를 로드합니다:

```python
class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=[".env.development", ".env"],
        # ...
    )
```

### ⚠️ 중요: Pydantic의 우선순위

Pydantic은 **리스트의 모든 파일을 순서대로 읽고 병합**하며, **나중에 읽은 값이 우선**합니다:

1. `.env.development` 읽기
2. `.env` 읽기 ← **최종 우선권**
3. 환경 변수 (OS environment) ← **최고 우선권**

따라서:
- `.env` 파일이 있으면 **`.env`의 값이 최종적으로 사용됨**
- `.env` 파일이 없으면 `.env.development`의 값 사용
- OS 환경 변수가 설정되어 있으면 **환경 변수가 최우선**

## 환경별 설정

### 🔧 로컬 개발 (Local Development)

Docker 외부에서 개발할 때 사용합니다.

**설정 방법:**
```bash
# 1. .env.development를 .env로 복사
cd plantpoint-automation
cp .env.development .env

# 2. 실행
python main.py
```

**주요 설정값:**
```bash
MQTT_HOST=127.0.0.1          # localhost
REDIS_HOST=127.0.0.1         # localhost
DB_HOST=127.0.0.1            # localhost
USE_REAL_GPIO=false          # Fake GPIO for testing
API_BASE_URL=http://127.0.0.1:9000
```

**전제 조건:**
- Docker에서 MQTT, Redis, PostgreSQL, Backend 서비스가 실행 중이어야 함
- 포트가 localhost로 매핑되어 있어야 함 (docker-compose.yml 확인)

---

### 🐳 Docker 배포 (Docker Deployment)

Docker 컨테이너 내부에서 실행할 때 사용합니다.

**설정 방법:**
```bash
# 1. .env.docker를 .env로 복사
cd plantpoint-automation
cp .env.docker .env

# 2. Docker Compose로 실행
docker-compose up automation
```

**주요 설정값:**
```bash
MQTT_HOST=mqtt               # Docker service name
REDIS_HOST=redis             # Docker service name
DB_HOST=postgres             # Docker service name
USE_REAL_GPIO=true           # Real GPIO on Raspberry Pi
API_BASE_URL=http://frontend/api
```

---

## 파일별 설명

### `.env.development` (템플릿 - Git 추적)

**용도**: 로컬 개발용 설정 템플릿

**특징**:
- Git에 커밋됨 (팀원들과 공유)
- localhost/127.0.0.1 사용
- Fake GPIO 사용
- 민감한 정보는 더미 값으로 설정

**수정 시기**:
- 새로운 환경 변수 추가
- 개발 환경의 기본값 변경

### `.env.docker` (템플릿 - Git 추적)

**용도**: Docker 배포용 설정 템플릿

**특징**:
- Git에 커밋됨
- Docker 서비스 이름 사용 (mqtt, redis, postgres, frontend)
- Real GPIO 사용
- 민감한 정보는 더미 값으로 설정

**수정 시기**:
- Docker 서비스 이름 변경
- Docker 배포 환경 변경

### `.env` (실제 사용 - Git 무시)

**용도**: 실제로 사용되는 설정 파일

**특징**:
- Git에서 무시됨 (`.gitignore`에 포함)
- 개발자마다 다를 수 있음
- 실제 비밀번호/토큰 포함 가능

**생성 방법**:
```bash
# 로컬 개발
cp .env.development .env

# Docker 배포
cp .env.docker .env
```

---

## 설정 확인 방법

### 현재 로드된 설정 확인

```bash
cd plantpoint-automation
python -c "
from config import settings
print(f'MQTT_HOST: {settings.mqtt_host}')
print(f'REDIS_HOST: {settings.redis_host}')
print(f'DB_HOST: {settings.db_host}')
print(f'USE_REAL_GPIO: {settings.use_real_gpio}')
"
```

### .env 파일 내용 확인

```bash
# 어떤 템플릿을 사용 중인지 확인
head -5 .env

# 로컬 개발 설정이면
# Output: # Development Environment Configuration

# Docker 설정이면
# Output: USERNAME = llewyn
```

---

## 문제 해결

### ❌ MQTT 연결 실패: `[Errno 11001] getaddrinfo failed`

**원인**: Docker 호스트명(`mqtt`)을 로컬에서 해석할 수 없음

**해결**:
```bash
# .env 파일이 Docker 설정을 사용 중
# 로컬 개발 설정으로 변경
cp .env.development .env
```

### ❌ 설정이 적용되지 않음

**가능한 원인**:
1. `.env` 파일이 없음 → 템플릿을 복사하세요
2. OS 환경 변수가 설정되어 있음 → 환경 변수가 최우선입니다
3. Python 캐시 문제 → `__pycache__` 폴더 삭제

**확인 방법**:
```bash
# 1. .env 파일 존재 확인
ls -la .env

# 2. 설정 값 확인
python -c "from config import settings; print(settings.mqtt_host)"

# 3. 캐시 삭제 (필요시)
find . -type d -name __pycache__ -exec rm -rf {} +
```

### ❌ Git에서 .env가 추적됨

**해결**:
```bash
# .env 파일을 Git 추적에서 제거
git rm --cached .env

# .gitignore 확인
cat .gitignore | grep ".env"
# Output: .env가 포함되어 있어야 함
```

---

## 모범 사례 (Best Practices)

### ✅ DO (권장)

1. **템플릿 파일 사용**
   ```bash
   cp .env.development .env  # 로컬 개발
   cp .env.docker .env       # Docker 배포
   ```

2. **민감한 정보 관리**
   - 실제 비밀번호는 `.env`에만 저장
   - 템플릿 파일에는 더미 값 사용

3. **팀원과 공유**
   - `.env.development`, `.env.docker`를 Git에 커밋
   - `.env`는 각자 로컬에서 관리

4. **새 환경 변수 추가 시**
   - 두 템플릿 파일 모두 업데이트
   - `config.py`의 `Settings` 클래스에 추가

### ❌ DON'T (비권장)

1. **`.env`를 Git에 커밋하지 마세요**
   - 민감한 정보 노출 위험

2. **환경 파일을 직접 편집하지 마세요**
   - 템플릿을 수정하고 `.env`로 복사

3. **여러 환경을 한 파일에 섞지 마세요**
   - Docker/Local 설정을 명확히 분리

---

## 요약

| 파일 | Git 추적 | 용도 | 예시 호스트 |
|------|---------|------|------------|
| `.env.development` | ✅ 추적 | 로컬 개발 템플릿 | 127.0.0.1 |
| `.env.docker` | ✅ 추적 | Docker 배포 템플릿 | mqtt, redis |
| `.env` | ❌ 무시 | 실제 사용 파일 | (복사본) |

**간단 요약:**
- 로컬 개발: `cp .env.development .env`
- Docker 배포: `cp .env.docker .env`
- Settings는 `.env` 파일 우선 사용
