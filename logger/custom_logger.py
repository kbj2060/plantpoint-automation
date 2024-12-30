from datetime import datetime, timezone, timedelta
from loguru import logger
import sys

KST = timezone(timedelta(hours=9))
korean_time = datetime.now(tz=KST)

banner_level = logger.level("BANNER", no=10, color="<fg #d9d8d2>")
switch_level = logger.level("SWITCH", no=11, color="<fg #cf1578>")
stay_level = logger.level("STAY", no=13, color="<fg #a2d5c6>")
disabled_level = logger.level("DISABLED", no=14, color="<fg #e8d21d>")

# # 파일 로깅 설정 유지
# logger.add(f".logs/{korean_time}.log",
#           colorize=True,
#           rotation="12:00",
#           retention="1 days",
#           compression="zip",
#           format="{time:YYYY-MM-DD at HH:mm:ss} | {level:8} | {message}",
#           enqueue=True)

# 일반 로그 포맷 (파일 위치 없음)
default_format = "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <level>{message}</level>"

# 오류 로그 포맷 (파일 위치 포함)
error_format = "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>"

# 기본 핸들러 제거
logger.remove()

# 일반 로그용 핸들러 추가 (INFO, SUCCESS 등)
logger.add(
    sys.stdout,
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <level>{message}</level>",
    filter=lambda record: record["level"].name not in ["ERROR", "CRITICAL"],
    colorize=True
)

# 오류 로그용 핸들러 추가 (ERROR, CRITICAL)
logger.add(
    sys.stdout,
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <red>{name}</red>:<red>{function}</red>:<red>{line}</red> | <level>{message}</level>",
    filter=lambda record: record["level"].name in ["ERROR", "CRITICAL"],
    colorize=True,
    backtrace=True,
    diagnose=True
)

# 파일 로깅 설정
logger.add(
    f".logs/{korean_time}.log",
    format="{time:YYYY-MM-DD HH:mm:ss} | {level:<8} | {name}:{function}:{line} | {message}",
    rotation="12:00",
    retention="1 days",
    compression="zip",
    enqueue=True
)

custom_logger = logger
