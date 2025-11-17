#!/usr/bin/env python3
"""
FAME Health Monitor
Real-time system health monitoring and status tracking
"""

import asyncio
import logging
import time
import psutil
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from collections import defaultdict
import threading

logger = logging.getLogger(__name__)


class HealthMonitor:
    """
    Production-grade health monitoring system.
    Tracks module health, API connectivity, and system performance.
    """
    
    def __init__(self):
        self.module_status = {}
        self.api_status = {}
        self.performance_metrics = {
            'response_times': [],
            'error_counts': defaultdict(int),
            'success_counts': defaultdict(int),
            'last_update': datetime.now()
        }
        self.health_checks = {}
        self.monitoring_active = False
        self.monitor_thread = None
        self.voice_metrics_provider = None
        self.trading_metrics_provider = None
        
        # Thresholds
        self.max_response_time = 5.0  # seconds
        self.max_error_rate = 0.1  # 10%
        self.max_memory_usage = 0.8  # 80%
        self.max_cpu_usage = 0.9  # 90%
    
    def start_monitoring(self, interval: int = 30):
        """Start background health monitoring"""
        if self.monitoring_active:
            return
        
        self.monitoring_active = True
        
        def monitor_loop():
            while self.monitoring_active:
                try:
                    self.check_system_health()
                    time.sleep(interval)
                except Exception as e:
                    logger.error(f"Health monitor error: {e}")
        
        self.monitor_thread = threading.Thread(target=monitor_loop, daemon=True)
        self.monitor_thread.start()
        logger.info("Health monitoring started")
    
    def stop_monitoring(self):
        """Stop background health monitoring"""
        self.monitoring_active = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=5)
        logger.info("Health monitoring stopped")
    
    def check_system_health(self) -> Dict[str, Any]:
        """Perform comprehensive health check"""
        health_status = {
            'timestamp': datetime.now().isoformat(),
            'overall_status': 'healthy',
            'modules': {},
            'system': {},
            'apis': {},
            'warnings': [],
            'errors': []
        }
        
        # System resources
        try:
            cpu_percent = psutil.cpu_percent(interval=0.1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            health_status['system'] = {
                'cpu_percent': cpu_percent,
                'memory_percent': memory.percent,
                'memory_available_mb': memory.available / (1024 * 1024),
                'disk_percent': disk.percent,
                'disk_free_gb': disk.free / (1024 * 1024 * 1024)
            }
            
            # Check thresholds
            if cpu_percent > self.max_cpu_usage * 100:
                health_status['warnings'].append(f"High CPU usage: {cpu_percent:.1f}%")
                health_status['overall_status'] = 'degraded'
            
            if memory.percent > self.max_memory_usage * 100:
                health_status['warnings'].append(f"High memory usage: {memory.percent:.1f}%")
                health_status['overall_status'] = 'degraded'
            
            if disk.percent > 90:
                health_status['warnings'].append(f"Low disk space: {disk.percent:.1f}% used")
                health_status['overall_status'] = 'degraded'
        
        except Exception as e:
            logger.error(f"System health check error: {e}")
            health_status['errors'].append(f"System check failed: {str(e)}")
        
        # Module health
        for module_name, status in self.module_status.items():
            health_status['modules'][module_name] = {
                'status': status.get('status', 'unknown'),
                'last_check': status.get('last_check'),
                'error_count': status.get('error_count', 0),
                'success_count': status.get('success_count', 0)
            }
            
            # Check if module is unhealthy
            error_rate = 0.0
            if status.get('success_count', 0) + status.get('error_count', 0) > 0:
                error_rate = status.get('error_count', 0) / (
                    status.get('success_count', 0) + status.get('error_count', 0)
                )
            
            if error_rate > self.max_error_rate:
                health_status['warnings'].append(
                    f"Module {module_name} has high error rate: {error_rate:.1%}"
                )
                health_status['modules'][module_name]['status'] = 'degraded'
                health_status['overall_status'] = 'degraded'
        
        # API health
        for api_name, status in self.api_status.items():
            health_status['apis'][api_name] = {
                'status': status.get('status', 'unknown'),
                'last_check': status.get('last_check'),
                'response_time': status.get('response_time'),
                'error_count': status.get('error_count', 0)
            }
            
            if status.get('status') == 'unavailable':
                health_status['warnings'].append(f"API {api_name} is unavailable")
                health_status['overall_status'] = 'degraded'
        
        # Update overall status
        if health_status['errors']:
            health_status['overall_status'] = 'unhealthy'

        if self.voice_metrics_provider:
            try:
                voice_metrics = self.voice_metrics_provider()
                health_status['voice'] = voice_metrics
            except Exception as exc:  # pragma: no cover - defensive
                logger.debug(f"Voice metrics provider failed: {exc}")
                health_status['warnings'].append("Voice telemetry unavailable")
                health_status['overall_status'] = 'degraded'
        if self.trading_metrics_provider:
            try:
                trading_metrics = self.trading_metrics_provider()
                health_status['trading'] = trading_metrics
            except Exception as exc:  # pragma: no cover - defensive
                logger.debug(f"Trading metrics provider failed: {exc}")
                health_status['warnings'].append("Trading telemetry unavailable")
                health_status['overall_status'] = 'degraded'
        
        return health_status
    
    def record_module_execution(self, module_name: str, success: bool, 
                                response_time: Optional[float] = None):
        """Record module execution result"""
        if module_name not in self.module_status:
            self.module_status[module_name] = {
                'status': 'unknown',
                'error_count': 0,
                'success_count': 0,
                'last_check': None
            }
        
        status = self.module_status[module_name]
        
        if success:
            status['success_count'] = status.get('success_count', 0) + 1
            status['status'] = 'healthy'
        else:
            status['error_count'] = status.get('error_count', 0) + 1
            status['status'] = 'unhealthy' if status['error_count'] > 3 else 'degraded'
        
        status['last_check'] = datetime.now().isoformat()
        
        if response_time:
            if 'response_times' not in status:
                status['response_times'] = []
            status['response_times'].append(response_time)
            # Keep only last 100
            if len(status['response_times']) > 100:
                status['response_times'] = status['response_times'][-100:]
    
    def record_api_call(self, api_name: str, success: bool, 
                       response_time: Optional[float] = None):
        """Record API call result"""
        if api_name not in self.api_status:
            self.api_status[api_name] = {
                'status': 'unknown',
                'error_count': 0,
                'last_check': None
            }
        
        status = self.api_status[api_name]
        
        if success:
            status['status'] = 'available'
        else:
            status['error_count'] = status.get('error_count', 0) + 1
            if status['error_count'] > 3:
                status['status'] = 'unavailable'
        
        status['last_check'] = datetime.now().isoformat()
        
        if response_time:
            status['response_time'] = response_time
        
        # Auto-recovery: if it's been healthy for a while, reset error count
        if success and status['error_count'] > 0:
            status['error_count'] = max(0, status['error_count'] - 1)
    
    def record_response_time(self, response_time: float):
        """Record overall response time"""
        self.performance_metrics['response_times'].append({
            'time': response_time,
            'timestamp': datetime.now().isoformat()
        })
        
        # Keep only last 1000
        if len(self.performance_metrics['response_times']) > 1000:
            self.performance_metrics['response_times'] = \
                self.performance_metrics['response_times'][-1000:]

    def record_query(self) -> None:
        """Record that a query was processed."""
        metrics = self.performance_metrics
        metrics['last_update'] = datetime.now()
        metrics['total_queries'] = metrics.get('total_queries', 0) + 1
    
    def get_module_health(self, module_name: str) -> Dict[str, Any]:
        """Get health status for specific module"""
        return self.module_status.get(module_name, {
            'status': 'unknown',
            'error_count': 0,
            'success_count': 0
        })
    
    def get_api_health(self, api_name: str) -> Dict[str, Any]:
        """Get health status for specific API"""
        return self.api_status.get(api_name, {
            'status': 'unknown',
            'error_count': 0
        })
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """Get performance summary"""
        response_times = self.performance_metrics['response_times']
        
        if not response_times:
            return {
                'average_response_time': 0.0,
                'p95_response_time': 0.0,
                'p99_response_time': 0.0,
                'total_requests': 0
            }
        
        times = [r['time'] for r in response_times[-100:]]  # Last 100
        times.sort()
        
        avg = sum(times) / len(times)
        p95_idx = int(len(times) * 0.95)
        p99_idx = int(len(times) * 0.99)
        
        return {
            'average_response_time': avg,
            'p95_response_time': times[p95_idx] if p95_idx < len(times) else times[-1],
            'p99_response_time': times[p99_idx] if p99_idx < len(times) else times[-1],
            'total_requests': len(response_times)
        }
    
    def is_healthy(self) -> bool:
        """Check if system is overall healthy"""
        health = self.check_system_health()
        return health['overall_status'] in ['healthy', 'degraded']

    def register_voice_metrics_provider(self, provider):
        """Register callable returning voice metrics snapshot."""
        self.voice_metrics_provider = provider

    def register_trading_metrics_provider(self, provider):
        """Register callable returning trading metrics snapshot."""
        self.trading_metrics_provider = provider


# Singleton instance
_health_monitor: Optional[HealthMonitor] = None


def get_health_monitor() -> HealthMonitor:
    """Get or create health monitor instance"""
    global _health_monitor
    if _health_monitor is None:
        _health_monitor = HealthMonitor()
        _health_monitor.start_monitoring()
    return _health_monitor

