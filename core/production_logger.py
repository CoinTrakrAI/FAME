#!/usr/bin/env python3
"""
FAME Production Logger
Enterprise-grade structured logging system
"""

import json
import logging
import os
import sys
import traceback
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

from monitoring.log_aggregator import LogAggregator
from monitoring.log_exporter import LogExporter, LogExporterConfig


class ProductionLogger:
    """
    Production-grade logging system with structured JSON output.
    """
    
    def __init__(self, log_dir: Optional[Path] = None, log_level: str = "INFO"):
        self.log_dir = log_dir or Path(__file__).parent.parent / "logs"
        # Ensure directory exists and is writable
        self.log_dir.mkdir(exist_ok=True, mode=0o775)
        
        self._aggregator_enabled = os.getenv("FAME_LOG_AGGREGATION") == "1"
        buffer_size = int(os.getenv("FAME_LOG_BUFFER", "500"))
        self._aggregator: Optional[LogAggregator] = (
            LogAggregator(max_events=buffer_size) if self._aggregator_enabled else None
        )
        self._log_exporter: Optional[LogExporter] = None
        if self._aggregator:
            exporter_config = LogExporterConfig(
                interval_seconds=float(os.getenv("FAME_LOG_EXPORT_INTERVAL", "5.0")),
                elastic_url=os.getenv("FAME_LOG_ELASTIC_URL"),
                elastic_index=os.getenv("FAME_LOG_ELASTIC_INDEX", "fame-logs"),
                splunk_url=os.getenv("FAME_LOG_SPLUNK_HEC"),
                splunk_token=os.getenv("FAME_LOG_SPLUNK_TOKEN"),
            )
            if exporter_config.elastic_url or (exporter_config.splunk_url and exporter_config.splunk_token):
                self._log_exporter = LogExporter(self._aggregator, exporter_config)
                self._log_exporter.start()

        # Setup structured logger
        self.logger = logging.getLogger("FAME")
        self.logger.setLevel(getattr(logging, log_level.upper()))
        
        # Remove existing handlers
        self.logger.handlers = []
        
        # Console handler - clean format, only show WARNING/ERROR by default
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.WARNING)  # Only warnings/errors on console
        
        # Add filter to suppress expected Windows compatibility errors and normal operation messages
        class CleanFilter(logging.Filter):
            def filter(self, record):
                # Suppress expected Windows fcntl errors (Linux-only module)
                if 'fcntl' in record.getMessage().lower():
                    return False
                # Suppress plugin loading messages
                if 'plugin' in record.getMessage().lower() and 'loaded' in record.getMessage().lower():
                    return False
                # Suppress initialization messages
                if 'initialized' in record.getMessage().lower():
                    return False
                # Suppress health monitor startup (normal operation)
                if 'health monitoring started' in record.getMessage().lower():
                    return False
                # Suppress query/response logging (too verbose for console)
                if 'query' in record.getMessage().lower() or 'response' in record.getMessage().lower():
                    return False
                # Suppress routing messages
                if 'routing query' in record.getMessage().lower():
                    return False
                return True
        
        console_handler.addFilter(CleanFilter())
        
        # Simple formatter for console
        console_formatter = logging.Formatter(
            '%(levelname)s: %(message)s'
        )
        console_handler.setFormatter(console_formatter)
        self.logger.addHandler(console_handler)
        
        # Also suppress INFO level for root logger and common loggers
        # (logging module already imported at top of file)
        logging.getLogger('core').setLevel(logging.WARNING)
        logging.getLogger('core.health_monitor').setLevel(logging.WARNING)
        logging.getLogger('core.autonomous_decision_engine').setLevel(logging.WARNING)
        logging.getLogger('FAME').setLevel(logging.WARNING)
        
        # File handler for detailed logs
        file_handler = logging.FileHandler(
            self.log_dir / f"fame_{datetime.now().strftime('%Y%m%d')}.log"
        )
        file_handler.setLevel(logging.DEBUG)
        file_formatter = logging.Formatter(
            '%(asctime)s | %(levelname)-8s | %(name)s | %(funcName)s:%(lineno)d | %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        file_handler.setFormatter(file_formatter)
        self.logger.addHandler(file_handler)
        
        # Error log handler
        error_handler = logging.FileHandler(
            self.log_dir / f"fame_errors_{datetime.now().strftime('%Y%m%d')}.log"
        )
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(file_formatter)
        self.logger.addHandler(error_handler)
    
    def log_query(self, query: Dict[str, Any], level: str = "INFO"):
        """Log a user query"""
        log_entry = {
            'type': 'query',
            'timestamp': datetime.now().isoformat(),
            'query_text': query.get('text', ''),
            'source': query.get('source', 'unknown'),
            'session_id': query.get('session_id'),
            'metadata': query.get('metadata', {})
        }
        
        self._log(level, "QUERY", json.dumps(log_entry))
    
    def log_response(self, response: Dict[str, Any], query_id: Optional[str] = None, 
                    level: str = "INFO"):
        """Log a system response"""
        log_entry = {
            'type': 'response',
            'timestamp': datetime.now().isoformat(),
            'query_id': query_id,
            'response': response.get('response', '')[:500],  # Truncate long responses
            'confidence': response.get('confidence'),
            'source': response.get('source'),
            'metadata': response.get('metadata', {})
        }
        
        self._log(level, "RESPONSE", json.dumps(log_entry))
    
    def log_module_execution(self, module_name: str, success: bool, 
                           response_time: Optional[float] = None,
                           error: Optional[str] = None):
        """Log module execution"""
        log_entry = {
            'type': 'module_execution',
            'timestamp': datetime.now().isoformat(),
            'module': module_name,
            'success': success,
            'response_time': response_time,
            'error': error
        }
        
        level = "ERROR" if not success else "INFO"
        self._log(level, "MODULE", json.dumps(log_entry))
    
    def log_api_call(self, api_name: str, success: bool, 
                    response_time: Optional[float] = None,
                    error: Optional[str] = None):
        """Log API call"""
        log_entry = {
            'type': 'api_call',
            'timestamp': datetime.now().isoformat(),
            'api': api_name,
            'success': success,
            'response_time': response_time,
            'error': error
        }
        
        level = "ERROR" if not success else "DEBUG"
        self._log(level, "API", json.dumps(log_entry))
    
    def log_error(self, error: Exception, context: Optional[Dict[str, Any]] = None):
        """Log an error with full traceback"""
        log_entry = {
            'type': 'error',
            'timestamp': datetime.now().isoformat(),
            'error_type': type(error).__name__,
            'error_message': str(error),
            'traceback': traceback.format_exc(),
            'context': context or {}
        }
        
        self._log("ERROR", "ERROR", json.dumps(log_entry))
    
    def log_health_check(self, health_status: Dict[str, Any]):
        """Log health check results"""
        log_entry = {
            'type': 'health_check',
            'timestamp': datetime.now().isoformat(),
            'overall_status': health_status.get('overall_status'),
            'warnings': health_status.get('warnings', []),
            'errors': health_status.get('errors', [])
        }
        
        level = "ERROR" if health_status.get('overall_status') == 'unhealthy' else "INFO"
        self._log(level, "HEALTH", json.dumps(log_entry))

    def shutdown(self) -> None:
        if self._log_exporter:
            self._log_exporter.stop()
    
    def _log(self, level: str, category: str, message: str):
        """Internal logging method"""
        log_method = getattr(self.logger, level.lower(), self.logger.info)
        log_method(f"[{category}] {message}")
        if self._aggregator:
            self._aggregator.emit_json(
                {
                    "level": level.upper(),
                    "category": category,
                    "message": message,
                }
            )
    
    def get_logger(self) -> logging.Logger:
        """Get the underlying logger"""
        return self.logger

    def recent_events(self, limit: int = 100) -> Dict[str, Any]:
        if not self._aggregator:
            return {"events": [], "count": 0}
        events = self._aggregator.recent(limit)
        return {"events": events, "count": len(events)}


# Singleton instance
_production_logger: Optional[ProductionLogger] = None


def get_production_logger(log_dir: Optional[Path] = None) -> ProductionLogger:
    """Get or create production logger instance"""
    global _production_logger
    if _production_logger is None:
        _production_logger = ProductionLogger(log_dir)
    return _production_logger


# Convenience functions
def log_query(query: Dict[str, Any]):
    """Log a query"""
    get_production_logger().log_query(query)


def log_response(response: Dict[str, Any], query_id: Optional[str] = None):
    """Log a response"""
    get_production_logger().log_response(response, query_id)


def log_error(error: Exception, context: Optional[Dict[str, Any]] = None):
    """Log an error"""
    get_production_logger().log_error(error, context)

