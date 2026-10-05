"""
AJAX AI - Structured Logging System
Supports multiple specialized log files, console output with formatting,
and automatic sanitization of sensitive keys, passwords, and tokens.
"""

import os
import re
import logging
from logging.handlers import RotatingFileHandler
from typing import Optional

LOGS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "logs")
os.makedirs(LOGS_DIR, exist_ok=True)

# Regex patterns for sensitive information redaction
SENSITIVE_PATTERNS = [
    re.compile(r'(api[_-]?key|secret|token|password|auth|authorization)["\']?\s*[:=]\s*["\']?([^"\'\s,]+)', re.IGNORECASE),
    re.compile(r'(sk-[a-zA-Z0-9]{20,})', re.IGNORECASE),
    re.compile(r'(gsk_[a-zA-Z0-9]{20,})', re.IGNORECASE),
]

class SanitizedFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        msg = super().format(record)
        for pattern in SENSITIVE_PATTERNS:
            msg = pattern.sub(r'\1: [REDACTED]', msg)
        return msg

def setup_logger(name: str, log_filename: str, level=logging.INFO) -> logging.Logger:
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    if not logger.handlers:
        file_path = os.path.join(LOGS_DIR, log_filename)
        file_handler = RotatingFileHandler(
            file_path, maxBytes=5 * 1024 * 1024, backupCount=5, encoding="utf-8"
        )
        formatter = SanitizedFormatter(
            fmt="%(asctime)s [%(levelname)s] [%(name)s]: %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
        
        # Console output for main loggers
        if name in ("ajax", "security", "error"):
            console_handler = logging.StreamHandler()
            console_formatter = SanitizedFormatter(
                fmt="%(asctime)s [%(levelname)s] %(message)s",
                datefmt="%H:%M:%S"
            )
            console_handler.setFormatter(console_formatter)
            logger.addHandler(console_handler)
            
    return logger

# Preconfigured subsystem loggers
ajax_logger = setup_logger("ajax", "ajax.log")
error_logger = setup_logger("error", "error.log", level=logging.WARNING)
security_logger = setup_logger("security", "security.log")
tools_logger = setup_logger("tools", "tools.log")
voice_logger = setup_logger("voice", "voice.log")
training_logger = setup_logger("training", "training.log")
