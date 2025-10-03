# 베이스 이미지 선택
FROM python:3.13-slim

# GPIO 사용 여부를 선택하는 ARG 추가
# 실제 GPIO 사용 (라즈베리파이): docker build -t kbj2060/plantpoint-automation:latest .
# GPIO 모의 사용 (맥 등): docker build --build-arg USE_REAL_GPIO=false -t kbj2060/plantpoint-automation:latest .
ARG USE_REAL_GPIO=false
ENV USE_REAL_GPIO=${USE_REAL_GPIO}

# 필수 패키지 설치
RUN apt-get update && apt-get install -y \
    build-essential \
    python3-dev \
    cron \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# pip 및 setuptools 최신화
RUN pip install --upgrade pip setuptools wheel

# 작업 디렉토리 설정
WORKDIR /app

# 의존성 파일 복사 및 설치 (requirements.txt가 있는 경우)
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# 앱 코드 복사
COPY . .
COPY .env .env

# 기본 실행 명령어 (컨테이너가 계속 작동하도록 설정)
CMD ["python3", "main.py"]
