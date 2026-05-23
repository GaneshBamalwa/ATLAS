"""
shared/logging_config.py - Unified logger configuration
"""

import logging
import sys
from shared.config import global_config as settings

def configure_logging(service_name: str) -> None:
    """Configures system-wide logging with colored console outputs"""
    log_level_str = settings.log_level.upper()
    log_level = getattr(logging, log_level_str, logging.INFO)
    
    # Custom format
    log_format = f"%(asctime)s - [{service_name}] - %(levelname)s - %(name)s:%(funcName)s:%(lineno)d - %(message)s"
    
    # Remove existing handlers
    root_logger = logging.getLogger()
    if root_logger.handlers:
        for handler in root_logger.handlers:
            root_logger.removeHandler(handler)
            
    logging.basicConfig(
        level=log_level,
        format=log_format,
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    # Disable excessively verbose loggers from dependencies
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("chromadb").setLevel(logging.WARNING)
    logging.getLogger("asyncio").setLevel(logging.WARNING)
    
    logger = logging.getLogger(service_name)
    logger.info(f"Logging initialized at {log_level_str} level.")
