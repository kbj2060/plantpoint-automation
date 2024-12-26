from datetime import datetime, timezone, timedelta
from loguru import logger

KST = timezone(timedelta(hours=9))
korean_time = datetime.now(tz=KST)

banner_level = logger.level("BANNER", no=10, color="<fg #d9d8d2>")
switch_level = logger.level("SWITCH", no=11, color="<fg #cf1578>")
stay_level = logger.level("STAY", no=13, color="<fg #a2d5c6>")
disabled_level = logger.level("DISABLED", no=14, color="<fg #e8d21d>")

logger.add(f".logs/{korean_time}.log",
            colorize=True,
            rotation="12:00",
            retention="1 days",
            compression="zip",
            format="{time:YYYY-MM-DD at HH:mm:ss} | {level:8} | {message}",
            enqueue=True)

custom_logger = logger
