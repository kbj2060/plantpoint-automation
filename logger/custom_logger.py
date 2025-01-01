import os
import logging
from datetime import datetime
from logging.handlers import RotatingFileHandler
from threading import current_thread

class ThreadLogger:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ThreadLogger, cls).__new__(cls)
            cls._instance.loggers = {}
            cls._instance.base_log_dir = '.logs'
            
            # 기본 로그 디렉토리 생성
            if not os.path.exists(cls._instance.base_log_dir):
                os.makedirs(cls._instance.base_log_dir)

        return cls._instance

    def __init__(self):
        # __new__에서 이미 초기화했으므로 여기서는 생략
        pass

    def get_normalized_thread_name(self, thread_name: str, machine_name: str = None) -> str:
        """스레드 이름을 정규화"""
        if machine_name:
            return f'automation/{machine_name}'
            
        # 기본 스레드 매핑
        thread_map = {
            'MainThread': 'main',
            'Thread-1': 'mqtt',
            'Thread-2': 'websocket',
        }
        
        if thread_name in thread_map:
            return thread_map[thread_name]
            
        if '_connect' in thread_name:
            return 'mqtt_connect'
            
        return 'other'

    def get_logger(self, machine_name=None):
        """현재 스레드에 대한 로거 반환"""
        thread_name = current_thread().name
        normalized_name = self.get_normalized_thread_name(thread_name, machine_name)
        
        if normalized_name not in self.loggers:
            # 새 로거 생성
            logger = logging.getLogger(normalized_name)
            logger.setLevel(logging.DEBUG)
            
            # 이미 핸들러가 있다면 제거
            for handler in logger.handlers[:]:
                logger.removeHandler(handler)
            
            # 콘솔 핸들러
            console_handler = logging.StreamHandler()
            console_handler.setLevel(logging.DEBUG)
            console_formatter = logging.Formatter(
                '%(asctime)s | [%(levelname)s] | %(threadName)s: %(message)s',
                datefmt='%Y-%m-%d %H-%M-%S'
            )
            console_handler.setFormatter(console_formatter)
            logger.addHandler(console_handler)
            
            # 오늘 날짜의 로그 디렉토리 생성
            today = datetime.now().strftime('%Y-%m-%d')
            today_log_dir = os.path.join(self.base_log_dir, today)
            if not os.path.exists(today_log_dir):
                os.makedirs(today_log_dir)
                
            # automation 디렉토리 생성 (필요한 경우)
            if machine_name:
                today_log_dir = os.path.join(today_log_dir, 'automation')
                if not os.path.exists(today_log_dir):
                    os.makedirs(today_log_dir)
            
            # 파일 핸들러
            file_name = f'{normalized_name.split("/")[-1]}.log'  # automation/name -> name.log
            file_path = os.path.join(today_log_dir, file_name)
            
            file_handler = RotatingFileHandler(
                file_path,
                maxBytes=10*1024*1024,
                backupCount=5,
                encoding='utf-8'
            )
            file_handler.setLevel(logging.DEBUG)
            file_formatter = logging.Formatter(
                '%(asctime)s | [%(levelname)s]: %(message)s',
                datefmt='%Y-%m-%d %H-%M-%S'
            )
            file_handler.setFormatter(file_formatter)
            logger.addHandler(file_handler)
            
            self.loggers[normalized_name] = logger
            
        return self.loggers[normalized_name]

class CustomLogger:
    def __init__(self):
        self.machine_name = None
        self._thread_logger = ThreadLogger()

    def set_machine(self, machine_name):
        """자동화 머신 이름 설정"""
        self.machine_name = machine_name
        return self

    def debug(self, msg): 
        self._thread_logger.get_logger(self.machine_name).debug(msg)
    def info(self, msg): 
        self._thread_logger.get_logger(self.machine_name).info(msg)
    def warning(self, msg): 
        self._thread_logger.get_logger(self.machine_name).warning(msg)
    def error(self, msg): 
        self._thread_logger.get_logger(self.machine_name).error(msg)
    def critical(self, msg): 
        self._thread_logger.get_logger(self.machine_name).critical(msg)
    def exception(self, msg): 
        self._thread_logger.get_logger(self.machine_name).exception(msg)

# 전역 로거 인스턴스
custom_logger = CustomLogger()
