import sys
import logging
import structlog
from datetime import datetime, timezone, timedelta

# ANSI 색상 코드
COLORS = {
    'grey': '\033[38;5;240m',
    'red': '\033[31m',
    'green': '\033[32m',
    'yellow': '\033[33m',
    'blue': '\033[34m',
    'magenta': '\033[35m',
    'cyan': '\033[36m',
    'white': '\033[37m',
    'reset': '\033[0m'
}

# 로그 레벨별 색상
LEVEL_COLORS = {
    'debug': COLORS['grey'],
    'info': COLORS['green'],
    'warning': COLORS['yellow'],
    'error': COLORS['red'],
    'critical': COLORS['red']
}

# 로깅 기본 설정
logging.basicConfig(
    format="%(message)s",
    stream=sys.stdout,
    level=logging.INFO,
)

def add_timestamp(logger, method_name, event_dict):
    """타임스탬프 추가"""
    KST = timezone(timedelta(hours=9))
    event_dict["timestamp"] = datetime.now(KST).strftime("%Y-%m-%d %H:%M:%S")
    return event_dict

def console_formatter(logger, method_name, event_dict):
    """콘솔 출력 형식 지정 (색상 포함)"""
    timestamp = event_dict.pop("timestamp", "")
    level = event_dict.pop("level", method_name).upper()
    event = event_dict.pop("event", "")
    
    # 나머지 키워드 인자들을 문자열로 변환
    extra = " ".join(f"{k}={v}" for k, v in event_dict.items())
    
    # 로그 레벨에 따른 색상 적용
    level_color = LEVEL_COLORS.get(method_name.lower(), COLORS['white'])
    
    return (
        f"{COLORS['cyan']}{timestamp}{COLORS['reset']} | "
        f"{level_color}{level:8}{COLORS['reset']} | "
        f"{COLORS['white']}{event} {extra}{COLORS['reset']}"
    )

# structlog 설정
structlog.configure(
    processors=[
        add_timestamp,
        structlog.stdlib.add_log_level,
        structlog.processors.format_exc_info,
        console_formatter,
    ],
    logger_factory=structlog.PrintLoggerFactory(),
    cache_logger_on_first_use=True,
)

# 로거 인스턴스 생성
custom_logger = structlog.get_logger()
