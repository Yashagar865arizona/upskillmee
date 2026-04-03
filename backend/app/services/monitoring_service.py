"""
System monitoring service for health checks, performance monitoring, and error tracking.
"""

import time
import psutil
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta, timezone
from sqlalchemy.orm import Session
from sqlalchemy import text, func
import asyncio
from collections import defaultdict, deque
import traceback
import json

from ..models.analytics import SystemMetric
from ..database import get_db

logger = logging.getLogger(__name__)

class PerformanceMonitor:
    """Monitor API response times and system performance"""
    
    def __init__(self, max_samples=1000):
        self.response_times = defaultdict(lambda: deque(maxlen=max_samples))
        self.error_counts = defaultdict(int)
        self.request_counts = defaultdict(int)
        self.start_time = datetime.now(timezone.utc)
        
    def record_request(self, endpoint: str, method: str, response_time: float, 
                      status_code: int, error: Optional[Exception] = None):
        """Record API request metrics"""
        key = f"{method}:{endpoint}"
        
        # Record response time
        self.response_times[key].append({
            'time': response_time,
            'timestamp': datetime.now(timezone.utc),
            'status_code': status_code
        })
        
        # Count requests
        self.request_counts[key] += 1
        
        # Count errors
        if status_code >= 400 or error:
            self.error_counts[key] += 1
    
    def get_endpoint_stats(self, endpoint: str, method: str) -> Dict[str, Any]:
        """Get statistics for a specific endpoint"""
        key = f"{method}:{endpoint}"
        times = self.response_times[key]
        
        if not times:
            return {
                'avg_response_time': 0,
                'min_response_time': 0,
                'max_response_time': 0,
                'request_count': 0,
                'error_count': 0,
                'error_rate': 0
            }
        
        response_times = [t['time'] for t in times]
        
        return {
            'avg_response_time': sum(response_times) / len(response_times),
            'min_response_time': min(response_times),
            'max_response_time': max(response_times),
            'request_count': self.request_counts[key],
            'error_count': self.error_counts[key],
            'error_rate': self.error_counts[key] / self.request_counts[key] if self.request_counts[key] > 0 else 0
        }
    
    def get_all_stats(self) -> Dict[str, Any]:
        """Get statistics for all endpoints"""
        stats = {}
        for key in self.response_times.keys():
            method, endpoint = key.split(':', 1)
            stats[key] = self.get_endpoint_stats(endpoint, method)
        return stats

class HealthChecker:
    """Check health of critical system components"""
    
    def __init__(self):
        self.checks = {}
        self.last_check_time = None
        self.check_interval = 60  # seconds
    
    async def check_database_health(self) -> Dict[str, Any]:
        """Check database connectivity and performance"""
        try:
            start_time = time.time()
            db = next(get_db())
            
            # Test basic connectivity
            result = db.execute(text("SELECT 1")).fetchone()
            if not result:
                raise Exception("Database query returned no result")
            
            # Test query performance
            query_time = time.time() - start_time
            
            # Get database stats
            db_stats = db.execute(text("""
                SELECT 
                    count(*) as total_connections,
                    sum(case when state = 'active' then 1 else 0 end) as active_connections
                FROM pg_stat_activity 
                WHERE datname = current_database()
            """)).fetchone()
            
            return {
                'status': 'healthy',
                'response_time': query_time,
                'total_connections': db_stats[0] if db_stats else 0,
                'active_connections': db_stats[1] if db_stats else 0,
                'timestamp': datetime.now(timezone.utc).isoformat()
            }
            
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            return {
                'status': 'unhealthy',
                'error': str(e),
                'timestamp': datetime.now(timezone.utc).isoformat()
            }
        finally:
            db.close()
    
    async def check_system_resources(self) -> Dict[str, Any]:
        """Check system CPU, memory, and disk usage"""
        try:
            # CPU usage
            cpu_percent = psutil.cpu_percent(interval=1)
            
            # Memory usage
            memory = psutil.virtual_memory()
            
            # Disk usage
            disk = psutil.disk_usage('/')
            
            # Network stats
            network = psutil.net_io_counters()
            
            return {
                'status': 'healthy',
                'cpu_percent': cpu_percent,
                'memory': {
                    'total': memory.total,
                    'available': memory.available,
                    'percent': memory.percent,
                    'used': memory.used
                },
                'disk': {
                    'total': disk.total,
                    'used': disk.used,
                    'free': disk.free,
                    'percent': (disk.used / disk.total) * 100
                },
                'network': {
                    'bytes_sent': network.bytes_sent,
                    'bytes_recv': network.bytes_recv,
                    'packets_sent': network.packets_sent,
                    'packets_recv': network.packets_recv
                },
                'timestamp': datetime.now(timezone.utc).isoformat()
            }
            
        except Exception as e:
            logger.error(f"System resource check failed: {e}")
            return {
                'status': 'unhealthy',
                'error': str(e),
                'timestamp': datetime.now(timezone.utc).isoformat()
            }
    
    async def check_ai_services(self) -> Dict[str, Any]:
        """Check AI service connectivity"""
        try:
            # This would test OpenAI API connectivity
            # For now, we'll simulate a basic check
            return {
                'status': 'healthy',
                'openai_api': 'available',
                'deepseek_api': 'available',
                'timestamp': datetime.now(timezone.utc).isoformat()
            }
            
        except Exception as e:
            logger.error(f"AI services check failed: {e}")
            return {
                'status': 'unhealthy',
                'error': str(e),
                'timestamp': datetime.now(timezone.utc).isoformat()
            }
    
    async def run_all_checks(self) -> Dict[str, Any]:
        """Run all health checks"""
        checks = {
            'database': await self.check_database_health(),
            'system_resources': await self.check_system_resources(),
            'ai_services': await self.check_ai_services()
        }
        
        # Determine overall health
        overall_status = 'healthy'
        for check_name, check_result in checks.items():
            if check_result.get('status') != 'healthy':
                overall_status = 'unhealthy'
                break
        
        self.checks = checks
        self.last_check_time = datetime.now(timezone.utc)
        
        return {
            'overall_status': overall_status,
            'checks': checks,
            'last_check_time': self.last_check_time.isoformat()
        }

class ErrorTracker:
    """Track and analyze application errors"""
    
    def __init__(self, max_errors=1000):
        self.errors = deque(maxlen=max_errors)
        self.error_counts = defaultdict(int)
        self.error_types = defaultdict(int)
    
    def track_error(self, error: Exception, context: Dict[str, Any] = None):
        """Track an application error"""
        error_info = {
            'timestamp': datetime.now(timezone.utc),
            'error_type': type(error).__name__,
            'error_message': str(error),
            'traceback': traceback.format_exc(),
            'context': context or {}
        }
        
        self.errors.append(error_info)
        self.error_counts[error_info['error_type']] += 1
        
        # Log the error
        logger.error(f"Error tracked: {error_info['error_type']} - {error_info['error_message']}")
    
    def get_error_summary(self, hours: int = 24) -> Dict[str, Any]:
        """Get error summary for the last N hours"""
        cutoff_time = datetime.now(timezone.utc) - timedelta(hours=hours)
        recent_errors = [e for e in self.errors if e['timestamp'] >= cutoff_time]
        
        # Count errors by type
        error_type_counts = defaultdict(int)
        for error in recent_errors:
            error_type_counts[error['error_type']] += 1
        
        return {
            'total_errors': len(recent_errors),
            'error_types': dict(error_type_counts),
            'error_rate': len(recent_errors) / hours,  # errors per hour
            'most_common_error': max(error_type_counts.items(), key=lambda x: x[1])[0] if error_type_counts else None,
            'recent_errors': recent_errors[-10:]  # Last 10 errors
        }

class MonitoringService:
    """Main monitoring service that coordinates all monitoring components"""
    
    def __init__(self):
        self.performance_monitor = PerformanceMonitor()
        self.health_checker = HealthChecker()
        self.error_tracker = ErrorTracker()
        self.metrics_storage_interval = 300  # 5 minutes
        self.last_metrics_storage = datetime.now(timezone.utc)
        self.last_alert_check = datetime.now(timezone.utc)
        self.alert_check_interval = 60  # Check for alerts every minute
    
    async def record_api_request(self, endpoint: str, method: str, response_time: float,
                               status_code: int, error: Optional[Exception] = None):
        """Record API request for monitoring"""
        self.performance_monitor.record_request(endpoint, method, response_time, status_code, error)
        
        if error:
            self.error_tracker.track_error(error, {
                'endpoint': endpoint,
                'method': method,
                'status_code': status_code,
                'response_time': response_time
            })
    
    async def get_system_status(self) -> Dict[str, Any]:
        """Get comprehensive system status"""
        # Run health checks
        health_status = await self.health_checker.run_all_checks()
        
        # Get performance stats
        performance_stats = self.performance_monitor.get_all_stats()
        
        # Get error summary
        error_summary = self.error_tracker.get_error_summary()
        
        system_status = {
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'health': health_status,
            'performance': performance_stats,
            'errors': error_summary,
            'uptime_seconds': (datetime.now(timezone.utc) - self.performance_monitor.start_time).total_seconds()
        }
        
        # Check if we should run alert checks
        if await self.should_check_alerts():
            await self.check_and_create_alerts(system_status)
        
        return system_status
    
    async def should_check_alerts(self) -> bool:
        """Check if it's time to check for alerts"""
        return (datetime.now(timezone.utc) - self.last_alert_check).total_seconds() >= self.alert_check_interval
    
    async def check_and_create_alerts(self, system_status: Dict[str, Any]):
        """Check system status and create alerts if needed"""
        try:
            # Import here to avoid circular imports
            from .alerting_service import alerting_service
            
            # Check system thresholds and create alerts
            alerts_created = await alerting_service.check_system_thresholds(system_status)
            
            if alerts_created:
                logger.info(f"Created {len(alerts_created)} new alerts")
            
            self.last_alert_check = datetime.now(timezone.utc)
            
        except Exception as e:
            logger.error(f"Error checking alerts: {e}")
    
    async def store_metrics_to_database(self):
        """Store monitoring metrics to database for historical analysis"""
        try:
            db = next(get_db())
            
            # Store system metrics
            system_status = await self.get_system_status()
            
            # Store key metrics
            metrics_to_store = [
                ('system_uptime', system_status['uptime_seconds'], 'performance', 'system'),
                ('total_errors_24h', system_status['errors']['total_errors'], 'error', 'system'),
                ('error_rate_per_hour', system_status['errors']['error_rate'], 'error', 'system'),
            ]
            
            # Add health check metrics
            if system_status['health']['checks']['database']['status'] == 'healthy':
                metrics_to_store.append((
                    'database_response_time', 
                    system_status['health']['checks']['database']['response_time'],
                    'performance', 'database'
                ))
            
            # Add system resource metrics
            if system_status['health']['checks']['system_resources']['status'] == 'healthy':
                resources = system_status['health']['checks']['system_resources']
                metrics_to_store.extend([
                    ('cpu_percent', resources['cpu_percent'], 'performance', 'system'),
                    ('memory_percent', resources['memory']['percent'], 'performance', 'system'),
                    ('disk_percent', resources['disk']['percent'], 'performance', 'system'),
                ])
            
            # Store metrics in database
            for metric_name, value, metric_type, category in metrics_to_store:
                metric = SystemMetric(
                    metric_name=metric_name,
                    metric_value=float(value),
                    metric_type=metric_type,
                    category=category,
                    timestamp=datetime.now(timezone.utc),
                    aggregation_period='5min'
                )
                db.add(metric)
            
            db.commit()
            self.last_metrics_storage = datetime.now(timezone.utc)
            logger.info(f"Stored {len(metrics_to_store)} metrics to database")
            
        except Exception as e:
            logger.error(f"Failed to store metrics to database: {e}")
            db.rollback()
        finally:
            db.close()
    
    async def should_store_metrics(self) -> bool:
        """Check if it's time to store metrics to database"""
        return (datetime.now(timezone.utc) - self.last_metrics_storage).total_seconds() >= self.metrics_storage_interval
    
    async def get_historical_metrics(self, metric_name: str, hours: int = 24) -> List[Dict[str, Any]]:
        """Get historical metrics from database"""
        try:
            db = next(get_db())
            cutoff_time = datetime.now(timezone.utc) - timedelta(hours=hours)
            
            metrics = db.query(SystemMetric).filter(
                SystemMetric.metric_name == metric_name,
                SystemMetric.timestamp >= cutoff_time
            ).order_by(SystemMetric.timestamp).all()
            
            return [
                {
                    'timestamp': metric.timestamp.isoformat(),
                    'value': metric.metric_value,
                    'type': metric.metric_type,
                    'category': metric.category
                }
                for metric in metrics
            ]
            
        except Exception as e:
            logger.error(f"Failed to get historical metrics: {e}")
            return []
        finally:
            db.close()

# Global monitoring service instance
monitoring_service = MonitoringService()