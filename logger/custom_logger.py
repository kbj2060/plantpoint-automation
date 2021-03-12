from datetime import datetime, timezone, timedelta
from loguru import logger

KST = timezone(timedelta(hours=9))
korean_time = datetime.now(tz=KST).strftime('%Y-%m-%d')


banner_level = logger.level("BANNER", no=10, color="<fg #d9d8d2>")
on_level = logger.level("ON", no=11, color="<bg yellow>", icon="🐍")
off_level = logger.level("OFF", no=12, color="<bg red>", icon="🐍")
stay_level = logger.level("STAY", no=13, color="<bg blue>", icon="🐍")
disabled_level = logger.level("DISABLED", no=14, color="<bg white>", icon="🐍")

logger.add(f"logs/{korean_time}.log", colorize=True, rotation="12:00", retention="10 days", compression="zip", format="{time:YYYY-MM-DD at HH:mm:ss} | {level} | {message}")
custom_logger = logger



# logger.error("hello world", format="{time:YYYY-MM-DD at HH:mm:ss} | {level} | {message}")
# logger.success("hello world", format="{time:YYYY-MM-DD at HH:mm:ss} | {level} | {message}")
# logger.exception("hello world", format="{time:YYYY-MM-DD at HH:mm:ss} | {level} | {message}")
# logger.info("hello world", )
