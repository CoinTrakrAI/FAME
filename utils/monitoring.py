#!/usr/bin/env python3
"""
FAME AGI - System Health Monitoring
Real-time system metrics and health checks
"""

import psutil
import time
import logging
from typing import Dict, Any, Optional
from datetime import datetime, timezone

logger = logging.getLogger(__name__)


class SystemMonitor:
    """System health monitoring and metrics collection"""
    
    def __init__(self):
        self.metrics: Dict[str, Any] = {}
        self.alert_thresholds = {
            "memory_percent": 85.0,
            "cpu_percent": 90.0,
            "disk_percent": 90.0
        }
        self.alert_callbacks = []
    
    def add_alert_callback(self, callback):
        """Add callback function for alerts"""
        self.alert_callbacks.append(callback)
    
    async def check_health(self) -> Dict[str, Any]:
        """Check system health and return metrics"""
        try:
            health = {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "cpu_percent": psutil.cpu_percent(interval=0.1),
                "cpu_count": psutil.cpu_count(),
                "memory": {
                    "total": psutil.virtual_memory().total,
                    "available": psutil.virtual_memory().available,
                    "percent": psutil.virtual_memory().percent,
                    "used": psutil.virtual_memory().used
                },
                "disk": {
                    "total": psutil.disk_usage('/').total,
                    "used": psutil.disk_usage('/').used,
                    "free": psutil.disk_usage('/').free,
                    "percent": psutil.disk_usage('/').percent
                },
                "boot_time": psutil.boot_time(),
                "status": "healthy"
            }
            
            # Check thresholds and alert
            alerts = []
            if health["memory"]["percent"] > self.alert_thresholds["memory_percent"]:
                alerts.append("high_memory_usage")
                health["status"] = "degraded"
            
            if health["cpu_percent"] > self.alert_thresholds["cpu_percent"]:
                alerts.append("high_cpu_usage")
                health["status"] = "degraded"
            
            if health["disk"]["percent"] > self.alert_thresholds["disk_percent"]:
                alerts.append("high_disk_usage")
                health["status"] = "critical"
            
            if alerts:
                for alert_type in alerts:
                    self.alert(alert_type, health)
            
            self.metrics = health
            return health
            
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "status": "error",
                "error": str(e)
            }
    
    def alert(self, alert_type: str, data: Dict[str, Any]):
        """Trigger alert"""
        alert_data = {
            "type": alert_type,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "data": data
        }
        
        logger.warning(f"🚨 SYSTEM ALERT: {alert_type} - {data}")
        
        # Call registered callbacks
        for callback in self.alert_callbacks:
            try:
                callback(alert_data)
            except Exception as e:
                logger.error(f"Alert callback failed: {e}")
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get current performance metrics"""
        return {
            "system": self.metrics,
            "timestamp": time.time(),
            "uptime_seconds": time.time() - (self.metrics.get("boot_time", time.time()) if self.metrics else time.time())
        }
    
    def get_cpu_usage(self) -> float:
        """Get current CPU usage percentage"""
        return psutil.cpu_percent(interval=0.1)
    
    def get_memory_usage(self) -> Dict[str, Any]:
        """Get current memory usage"""
        mem = psutil.virtual_memory()
        return {
            "total": mem.total,
            "available": mem.available,
            "percent": mem.percent,
            "used": mem.used
        }
    
    def get_disk_usage(self) -> Dict[str, Any]:
        """Get current disk usage"""
        disk = psutil.disk_usage('/')
        return {
            "total": disk.total,
            "used": disk.used,
            "free": disk.free,
            "percent": disk.percent
        }

