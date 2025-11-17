#!/usr/bin/env python3
"""
FAME AGI - Enterprise Logging System
Structured logging with JSON support for production monitoring
"""

import logging
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, Optional


class AGILogger:
    """Enterprise-grade logging for FAME AGI Core"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.log_dir = Path(self.config.get("logging", {}).get("log_dir", "./logs"))
        self.log_dir.mkdir(parents=True, exist_ok=True)
        
        # Setup logging
        log_level = self.config.get("logging", {}).get("level", "INFO")
        log_format = '%(asctime)s | %(levelname)s | %(name)s | %(message)s'
        
        # Create logger
        self.logger = logging.getLogger("FAME_AGI")
        self.logger.setLevel(getattr(logging, log_level.upper(), logging.INFO))
        
        # Remove existing handlers
        self.logger.handlers = []
        
        # Console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(logging.Formatter(log_format))
        self.logger.addHandler(console_handler)
        
        # File handler
        log_file = self.log_dir / "agi_core.log"
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(logging.Formatter(log_format))
        self.logger.addHandler(file_handler)
        
        # JSON handler for structured logs
        json_log_file = self.log_dir / "agi_core.json.log"
        json_handler = logging.FileHandler(json_log_file)
        json_handler.setFormatter(logging.Formatter('%(message)s'))
        self.logger.addHandler(json_handler)
        
        self.logger.info("AGI Logger initialized")
    
    def info(self, message: str, extra: Optional[Dict[str, Any]] = None):
        """Log info message"""
        if extra:
            self.logger.info(message, extra=extra)
        else:
            self.logger.info(message)
    
    def error(self, message: str, extra: Optional[Dict[str, Any]] = None):
        """Log error message"""
        if extra:
            self.logger.error(message, extra=extra)
        else:
            self.logger.error(message)
    
    def warning(self, message: str, extra: Optional[Dict[str, Any]] = None):
        """Log warning message"""
        if extra:
            self.logger.warning(message, extra=extra)
        else:
            self.logger.warning(message)
    
    def debug(self, message: str, extra: Optional[Dict[str, Any]] = None):
        """Log debug message"""
        if extra:
            self.logger.debug(message, extra=extra)
        else:
            self.logger.debug(message)
    
    def agi_event(self, event_type: str, data: Dict[str, Any]):
        """Structured logging for AGI events"""
        event = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "system": self.config.get("system", {}).get("name", "FAME_AGI"),
            "event_type": event_type,
            "data": data
        }
        
        # Log as JSON for structured processing
        json_message = json.dumps(event)
        self.logger.info(f"AGI Event: {event_type}", extra={"event": event})
    
    def get_logger(self) -> logging.Logger:
        """Get the underlying logger instance"""
        return self.logger

