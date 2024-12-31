# 베이스 이미지 선택
FROM python:3.9-slim

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
CMD ["tail", "-f", "/dev/null"]
