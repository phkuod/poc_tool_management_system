import logging
import os
from logging.handlers import RotatingFileHandler

class SystemLogger:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(SystemLogger, cls).__new__(cls)
            cls._instance.logger = cls._instance._setup_logger()
        return cls._instance

    def _setup_logger(self):
        if not os.path.exists('logs'):
            os.makedirs('logs')

        logger = logging.getLogger("OutsourcingQcSystemLogger")
        logger.setLevel(logging.INFO)

        # Create a rotating file handler
        handler = RotatingFileHandler(
            'logs/outsourcing_qc_system.log',
            maxBytes=5*1024*1024,  # 5 MB
            backupCount=2
        )

        # Create a logging format
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)

        # Add the handlers to the logger
        logger.addHandler(handler)

        return logger

    def get_logger(self):
        return self.logger
