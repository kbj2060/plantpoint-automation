from logger.custom_logger import custom_logger


def BasicLogger(msg):
    def decorate(func):
        def wrapper(*args, **kwargs):
            try:
                result = func(*args, **kwargs)
                custom_logger.success(msg['success_msg'])
            except BaseException:
                custom_logger.error(msg['error_msg'])
            return result
        return wrapper
    return decorate
