"""
Comprehensive health check service for all system components.
Provides detailed health status for monitoring and alerting.
"""

import asyncio
import logging
import time
import psutil
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import aiohttp
import json

logger = logging.getLogger(__name__)

class HealthStatus(Enum):
    """Health status levels"""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"

@dataclass
class HealthCheck:
    """Individual health check result"""
    name: str
    status: HealthStatus
    message: str
    details: Dict[str, Any]
    timestamp: datetime
    response_time_ms: float
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "status": self.status.value,
            "message": self.message,
            "details": self.details,
            "timestamp": self.timestamp.isoformat(),
            "response_time_ms": self.response_time_ms
        }

class ComprehensiveHealthService:
    """Service for comprehensive health monitoring of all system components"""
    
    def __init__(self):
        self.health_checks = {}
        self.health_history = []
        self.max_history_size = 1000
        self.check_timeout = 10.0  # seconds
        
    async def run_all_health_checks(self) -> Dict[str, Any]:
        """Run all health checks and return comprehensive status"""
        logger.info("Running comprehensive health checks...")
        
        # Define all health checks
        health_check_functions = [
            ("database", self._check_database_health),
            ("redis", self._check_redis_health),
            ("system_resources", self._check_system_resources),
            ("disk_space", self._check_disk_space),
            ("memory_usage", self._check_memory_usage),
            ("cpu_usage", self._check_cpu_usage),
            ("network_connectivity", self._check_network_connectivity),
            ("ai_services", self._check_ai_services),
            ("background_tasks", self._check_background_tasks),
            ("log_system", self._check_log_system),
            ("monitoring_system", self._check_monitoring_system),
            ("security_services", self._check_security_services)
        ]
        
        # Run all checks concurrently
        check_tasks = []
        for check_name, check_func in health_check_functions:
            task = asyncio.create_task(self._run_single_check(check_name, check_func))
            check_tasks.append(task)
        
        # Wait for all checks to complete
        check_results = await asyncio.gather(*check_tasks, return_exceptions=True)
        
        # Process results
        health_status = {}
        for i, result in enumerate(check_results):
            check_name = health_check_functions[i][0]
            if isinstance(result, Exception):
                health_status[check_name] = HealthCheck(
                    name=check_name,
                    status=HealthStatus.UNKNOWN,
                    message=f"Health check failed: {str(result)}",
                    details={"error": str(result)},
                    timestamp=datetime.now(timezone.utc),
                    response_time_ms=0.0
                )
            else:
                health_status[check_name] = result
        
        # Store results
        self.health_checks = health_status
        self._store_health_history(health_status)
        
        # Calculate overall health
        overall_status = self._calculate_overall_health(health_status)
        
        return {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "overall_status": overall_status.value,
            "checks": {name: check.to_dict() for name, check in health_status.items()},
            "summary": self._generate_health_summary(health_status)
        }
    
    async def _run_single_check(self, check_name: str, check_func) -> HealthCheck:
        """Run a single health check with timeout"""
        start_time = time.time()
        
        try:
            result = await asyncio.wait_for(check_func(), timeout=self.check_timeout)
            response_time = (time.time() - start_time) * 1000
            
            if isinstance(result, HealthCheck):
                result.response_time_ms = response_time
                return result
            else:
                # If function returns a dict, convert to HealthCheck
                return HealthCheck(
                    name=check_name,
                    status=result.get('status', HealthStatus.UNKNOWN),
                    message=result.get('message', 'No message'),
                    details=result.get('details', {}),
                    timestamp=datetime.now(timezone.utc),
                    response_time_ms=response_time
                )
                
        except asyncio.TimeoutError:
            return HealthCheck(
                name=check_name,
                status=HealthStatus.UNHEALTHY,
                message=f"Health check timed out after {self.check_timeout}s",
                details={"timeout": True},
                timestamp=datetime.now(timezone.utc),
                response_time_ms=self.check_timeout * 1000
            )
        except Exception as e:
            return HealthCheck(
                name=check_name,
                status=HealthStatus.UNHEALTHY,
                message=f"Health check failed: {str(e)}",
                details={"error": str(e)},
                timestamp=datetime.now(timezone.utc),
                response_time_ms=(time.time() - start_time) * 1000
            )
    
    async def _check_database_health(self) -> HealthCheck:
        """Check database connectivity and performance"""
        try:
            from ..database.database import engine
            from sqlalchemy import text
            
            start_time = time.time()
            with engine.connect() as conn:
                result = conn.execute(text("SELECT 1")).scalar()
                query_time = (time.time() - start_time) * 1000
            
            if result != 1:
                return HealthCheck(
                    name="database",
                    status=HealthStatus.UNHEALTHY,
                    message="Database query returned unexpected result",
                    details={"result": result},
                    timestamp=datetime.now(timezone.utc),
                    response_time_ms=0
                )
            
            # Check connection pool status
            pool_status = {
                "size": engine.pool.size(),
                "checked_in": engine.pool.checkedin(),
                "checked_out": engine.pool.checkedout(),
                "overflow": engine.pool.overflow(),
                "invalid": engine.pool.invalid()
            }
            
            # Determine status based on pool health
            status = HealthStatus.HEALTHY
            message = "Database is healthy"
            
            if pool_status["invalid"] > 2:
                status = HealthStatus.DEGRADED
                message = f"Database has {pool_status['invalid']} invalid connections"
            elif query_time > 1000:  # 1 second
                status = HealthStatus.DEGRADED
                message = f"Database query is slow: {query_time:.1f}ms"
            
            return HealthCheck(
                name="database",
                status=status,
                message=message,
                details={
                    "query_time_ms": query_time,
                    "pool_status": pool_status
                },
                timestamp=datetime.now(timezone.utc),
                response_time_ms=0
            )
            
        except Exception as e:
            return HealthCheck(
                name="database",
                status=HealthStatus.UNHEALTHY,
                message=f"Database connection failed: {str(e)}",
                details={"error": str(e)},
                timestamp=datetime.now(timezone.utc),
                response_time_ms=0
            )
    
    async def _check_redis_health(self) -> HealthCheck:
        """Check Redis connectivity"""
        try:
            from ..main import redis_client
            
            if not redis_client:
                return HealthCheck(
                    name="redis",
                    status=HealthStatus.UNKNOWN,
                    message="Redis client not configured",
                    details={"configured": False},
                    timestamp=datetime.now(timezone.utc),
                    response_time_ms=0
                )
            
            start_time = time.time()
            redis_client.ping()
            ping_time = (time.time() - start_time) * 1000
            
            # Get Redis info
            info = redis_client.info()
            memory_usage = info.get('used_memory', 0)
            connected_clients = info.get('connected_clients', 0)
            
            status = HealthStatus.HEALTHY
            message = "Redis is healthy"
            
            if ping_time > 100:  # 100ms
                status = HealthStatus.DEGRADED
                message = f"Redis response is slow: {ping_time:.1f}ms"
            
            return HealthCheck(
                name="redis",
                status=status,
                message=message,
                details={
                    "ping_time_ms": ping_time,
                    "memory_usage": memory_usage,
                    "connected_clients": connected_clients
                },
                timestamp=datetime.now(timezone.utc),
                response_time_ms=0
            )
            
        except Exception as e:
            return HealthCheck(
                name="redis",
                status=HealthStatus.UNHEALTHY,
                message=f"Redis connection failed: {str(e)}",
                details={"error": str(e)},
                timestamp=datetime.now(timezone.utc),
                response_time_ms=0
            )
    
    async def _check_system_resources(self) -> HealthCheck:
        """Check overall system resource health"""
        try:
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            # Determine status based on resource usage
            status = HealthStatus.HEALTHY
            issues = []
            
            if cpu_percent > 90:
                status = HealthStatus.UNHEALTHY
                issues.append(f"Critical CPU usage: {cpu_percent:.1f}%")
            elif cpu_percent > 80:
                status = HealthStatus.DEGRADED
                issues.append(f"High CPU usage: {cpu_percent:.1f}%")
            
            if memory.percent > 90:
                status = HealthStatus.UNHEALTHY
                issues.append(f"Critical memory usage: {memory.percent:.1f}%")
            elif memory.percent > 80:
                if status == HealthStatus.HEALTHY:
                    status = HealthStatus.DEGRADED
                issues.append(f"High memory usage: {memory.percent:.1f}%")
            
            disk_percent = (disk.used / disk.total) * 100
            if disk_percent > 95:
                status = HealthStatus.UNHEALTHY
                issues.append(f"Critical disk usage: {disk_percent:.1f}%")
            elif disk_percent > 85:
                if status == HealthStatus.HEALTHY:
                    status = HealthStatus.DEGRADED
                issues.append(f"High disk usage: {disk_percent:.1f}%")
            
            message = "System resources are healthy" if not issues else "; ".join(issues)
            
            return HealthCheck(
                name="system_resources",
                status=status,
                message=message,
                details={
                    "cpu_percent": cpu_percent,
                    "memory_percent": memory.percent,
                    "disk_percent": disk_percent,
                    "memory_available_gb": memory.available / (1024**3),
                    "disk_free_gb": disk.free / (1024**3)
                },
                timestamp=datetime.now(timezone.utc),
                response_time_ms=0
            )
            
        except Exception as e:
            return HealthCheck(
                name="system_resources",
                status=HealthStatus.UNHEALTHY,
                message=f"Failed to check system resources: {str(e)}",
                details={"error": str(e)},
                timestamp=datetime.now(timezone.utc),
                response_time_ms=0
            )
    
    async def _check_disk_space(self) -> HealthCheck:
        """Check disk space availability"""
        try:
            disk = psutil.disk_usage('/')
            disk_percent = (disk.used / disk.total) * 100
            free_gb = disk.free / (1024**3)
            
            status = HealthStatus.HEALTHY
            message = f"Disk space is healthy: {free_gb:.1f}GB free"
            
            if disk_percent > 95:
                status = HealthStatus.UNHEALTHY
                message = f"Critical: Only {free_gb:.1f}GB free ({disk_percent:.1f}% used)"
            elif disk_percent > 85:
                status = HealthStatus.DEGRADED
                message = f"Warning: Only {free_gb:.1f}GB free ({disk_percent:.1f}% used)"
            
            return HealthCheck(
                name="disk_space",
                status=status,
                message=message,
                details={
                    "total_gb": disk.total / (1024**3),
                    "used_gb": disk.used / (1024**3),
                    "free_gb": free_gb,
                    "percent_used": disk_percent
                },
                timestamp=datetime.now(timezone.utc),
                response_time_ms=0
            )
            
        except Exception as e:
            return HealthCheck(
                name="disk_space",
                status=HealthStatus.UNHEALTHY,
                message=f"Failed to check disk space: {str(e)}",
                details={"error": str(e)},
                timestamp=datetime.now(timezone.utc),
                response_time_ms=0
            )
    
    async def _check_memory_usage(self) -> HealthCheck:
        """Check memory usage details"""
        try:
            memory = psutil.virtual_memory()
            swap = psutil.swap_memory()
            
            status = HealthStatus.HEALTHY
            issues = []
            
            if memory.percent > 90:
                status = HealthStatus.UNHEALTHY
                issues.append(f"Critical memory usage: {memory.percent:.1f}%")
            elif memory.percent > 80:
                status = HealthStatus.DEGRADED
                issues.append(f"High memory usage: {memory.percent:.1f}%")
            
            if swap.percent > 50:
                if status == HealthStatus.HEALTHY:
                    status = HealthStatus.DEGRADED
                issues.append(f"High swap usage: {swap.percent:.1f}%")
            
            message = "Memory usage is healthy" if not issues else "; ".join(issues)
            
            return HealthCheck(
                name="memory_usage",
                status=status,
                message=message,
                details={
                    "memory_percent": memory.percent,
                    "memory_available_gb": memory.available / (1024**3),
                    "memory_total_gb": memory.total / (1024**3),
                    "swap_percent": swap.percent,
                    "swap_used_gb": swap.used / (1024**3)
                },
                timestamp=datetime.now(timezone.utc),
                response_time_ms=0
            )
            
        except Exception as e:
            return HealthCheck(
                name="memory_usage",
                status=HealthStatus.UNHEALTHY,
                message=f"Failed to check memory usage: {str(e)}",
                details={"error": str(e)},
                timestamp=datetime.now(timezone.utc),
                response_time_ms=0
            )
    
    async def _check_cpu_usage(self) -> HealthCheck:
        """Check CPU usage details"""
        try:
            cpu_percent = psutil.cpu_percent(interval=1)
            cpu_count = psutil.cpu_count()
            load_avg = psutil.getloadavg() if hasattr(psutil, 'getloadavg') else (0, 0, 0)
            
            status = HealthStatus.HEALTHY
            message = f"CPU usage is healthy: {cpu_percent:.1f}%"
            
            if cpu_percent > 90:
                status = HealthStatus.UNHEALTHY
                message = f"Critical CPU usage: {cpu_percent:.1f}%"
            elif cpu_percent > 80:
                status = HealthStatus.DEGRADED
                message = f"High CPU usage: {cpu_percent:.1f}%"
            
            return HealthCheck(
                name="cpu_usage",
                status=status,
                message=message,
                details={
                    "cpu_percent": cpu_percent,
                    "cpu_count": cpu_count,
                    "load_average_1m": load_avg[0],
                    "load_average_5m": load_avg[1],
                    "load_average_15m": load_avg[2]
                },
                timestamp=datetime.now(timezone.utc),
                response_time_ms=0
            )
            
        except Exception as e:
            return HealthCheck(
                name="cpu_usage",
                status=HealthStatus.UNHEALTHY,
                message=f"Failed to check CPU usage: {str(e)}",
                details={"error": str(e)},
                timestamp=datetime.now(timezone.utc),
                response_time_ms=0
            )
    
    async def _check_network_connectivity(self) -> HealthCheck:
        """Check network connectivity"""
        try:
            # Test external connectivity
            test_urls = [
                "https://api.openai.com",
                "https://www.google.com",
                "https://httpbin.org/status/200"
            ]
            
            successful_connections = 0
            connection_times = []
            
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=5)) as session:
                for url in test_urls:
                    try:
                        start_time = time.time()
                        async with session.get(url) as response:
                            if response.status < 400:
                                successful_connections += 1
                                connection_times.append((time.time() - start_time) * 1000)
                    except:
                        pass
            
            success_rate = successful_connections / len(test_urls)
            avg_response_time = sum(connection_times) / len(connection_times) if connection_times else 0
            
            if success_rate >= 0.8:
                status = HealthStatus.HEALTHY
                message = f"Network connectivity is healthy ({successful_connections}/{len(test_urls)} successful)"
            elif success_rate >= 0.5:
                status = HealthStatus.DEGRADED
                message = f"Network connectivity is degraded ({successful_connections}/{len(test_urls)} successful)"
            else:
                status = HealthStatus.UNHEALTHY
                message = f"Network connectivity is poor ({successful_connections}/{len(test_urls)} successful)"
            
            return HealthCheck(
                name="network_connectivity",
                status=status,
                message=message,
                details={
                    "successful_connections": successful_connections,
                    "total_tests": len(test_urls),
                    "success_rate": success_rate,
                    "avg_response_time_ms": avg_response_time
                },
                timestamp=datetime.now(timezone.utc),
                response_time_ms=0
            )
            
        except Exception as e:
            return HealthCheck(
                name="network_connectivity",
                status=HealthStatus.UNHEALTHY,
                message=f"Failed to check network connectivity: {str(e)}",
                details={"error": str(e)},
                timestamp=datetime.now(timezone.utc),
                response_time_ms=0
            )
    
    async def _check_ai_services(self) -> HealthCheck:
        """Check AI services availability"""
        try:
            from ..config import settings
            
            # Check if API keys are configured
            api_keys_configured = {
                "openai": bool(settings.OPENAI_API_KEY),
                "deepseek": bool(settings.DEEPSEEK_API_KEY)
            }
            
            configured_count = sum(api_keys_configured.values())
            
            if configured_count == 0:
                status = HealthStatus.UNHEALTHY
                message = "No AI service API keys configured"
            elif configured_count == 1:
                status = HealthStatus.DEGRADED
                message = "Only one AI service configured"
            else:
                status = HealthStatus.HEALTHY
                message = "AI services are configured"
            
            return HealthCheck(
                name="ai_services",
                status=status,
                message=message,
                details={
                    "configured_services": api_keys_configured,
                    "active_model": settings.ACTIVE_MODEL
                },
                timestamp=datetime.now(timezone.utc),
                response_time_ms=0
            )
            
        except Exception as e:
            return HealthCheck(
                name="ai_services",
                status=HealthStatus.UNHEALTHY,
                message=f"Failed to check AI services: {str(e)}",
                details={"error": str(e)},
                timestamp=datetime.now(timezone.utc),
                response_time_ms=0
            )
    
    async def _check_background_tasks(self) -> HealthCheck:
        """Check background tasks status"""
        try:
            # Get current asyncio tasks
            current_tasks = asyncio.all_tasks()
            task_count = len(current_tasks)
            
            # Check for specific background tasks
            monitoring_tasks = [
                task for task in current_tasks 
                if 'monitoring' in task.get_name().lower()
            ]
            
            backup_tasks = [
                task for task in current_tasks 
                if 'backup' in task.get_name().lower()
            ]
            
            status = HealthStatus.HEALTHY
            message = f"Background tasks are running ({task_count} total tasks)"
            
            if task_count > 100:
                status = HealthStatus.DEGRADED
                message = f"High number of background tasks: {task_count}"
            
            return HealthCheck(
                name="background_tasks",
                status=status,
                message=message,
                details={
                    "total_tasks": task_count,
                    "monitoring_tasks": len(monitoring_tasks),
                    "backup_tasks": len(backup_tasks)
                },
                timestamp=datetime.now(timezone.utc),
                response_time_ms=0
            )
            
        except Exception as e:
            return HealthCheck(
                name="background_tasks",
                status=HealthStatus.UNHEALTHY,
                message=f"Failed to check background tasks: {str(e)}",
                details={"error": str(e)},
                timestamp=datetime.now(timezone.utc),
                response_time_ms=0
            )
    
    async def _check_log_system(self) -> HealthCheck:
        """Check logging system health"""
        try:
            from pathlib import Path
            
            log_dir = Path("logs")
            log_files = list(log_dir.glob("*.log")) if log_dir.exists() else []
            
            # Check log file sizes
            total_log_size = sum(f.stat().st_size for f in log_files if f.exists())
            total_log_size_mb = total_log_size / (1024 * 1024)
            
            status = HealthStatus.HEALTHY
            message = f"Log system is healthy ({len(log_files)} files, {total_log_size_mb:.1f}MB)"
            
            if total_log_size_mb > 1000:  # 1GB
                status = HealthStatus.DEGRADED
                message = f"Log files are large: {total_log_size_mb:.1f}MB"
            
            return HealthCheck(
                name="log_system",
                status=status,
                message=message,
                details={
                    "log_files_count": len(log_files),
                    "total_size_mb": total_log_size_mb,
                    "log_directory_exists": log_dir.exists()
                },
                timestamp=datetime.now(timezone.utc),
                response_time_ms=0
            )
            
        except Exception as e:
            return HealthCheck(
                name="log_system",
                status=HealthStatus.UNHEALTHY,
                message=f"Failed to check log system: {str(e)}",
                details={"error": str(e)},
                timestamp=datetime.now(timezone.utc),
                response_time_ms=0
            )
    
    async def _check_monitoring_system(self) -> HealthCheck:
        """Check monitoring system health"""
        try:
            from ..services.monitoring_service import monitoring_service
            
            # Check if monitoring service is active
            system_status = await monitoring_service.get_system_status()
            
            status = HealthStatus.HEALTHY
            message = "Monitoring system is healthy"
            
            if not system_status:
                status = HealthStatus.UNHEALTHY
                message = "Monitoring system is not responding"
            elif system_status.get('health', {}).get('overall_status') != 'healthy':
                status = HealthStatus.DEGRADED
                message = "Monitoring system reports degraded health"
            
            return HealthCheck(
                name="monitoring_system",
                status=status,
                message=message,
                details={
                    "system_status_available": bool(system_status),
                    "monitoring_active": True
                },
                timestamp=datetime.now(timezone.utc),
                response_time_ms=0
            )
            
        except Exception as e:
            return HealthCheck(
                name="monitoring_system",
                status=HealthStatus.UNHEALTHY,
                message=f"Failed to check monitoring system: {str(e)}",
                details={"error": str(e)},
                timestamp=datetime.now(timezone.utc),
                response_time_ms=0
            )
    
    async def _check_security_services(self) -> HealthCheck:
        """Check security services health"""
        try:
            from ..config import settings
            
            # Check security configuration
            security_checks = {
                "jwt_secret_configured": bool(settings.JWT_SECRET),
                "admin_api_key_configured": bool(settings.ADMIN_API_KEY),
                "cors_configured": bool(settings.CORS_ORIGINS)
            }
            
            configured_count = sum(security_checks.values())
            total_checks = len(security_checks)
            
            if configured_count == total_checks:
                status = HealthStatus.HEALTHY
                message = "Security services are properly configured"
            elif configured_count >= total_checks * 0.8:
                status = HealthStatus.DEGRADED
                message = f"Some security configurations missing ({configured_count}/{total_checks})"
            else:
                status = HealthStatus.UNHEALTHY
                message = f"Critical security configurations missing ({configured_count}/{total_checks})"
            
            return HealthCheck(
                name="security_services",
                status=status,
                message=message,
                details=security_checks,
                timestamp=datetime.now(timezone.utc),
                response_time_ms=0
            )
            
        except Exception as e:
            return HealthCheck(
                name="security_services",
                status=HealthStatus.UNHEALTHY,
                message=f"Failed to check security services: {str(e)}",
                details={"error": str(e)},
                timestamp=datetime.now(timezone.utc),
                response_time_ms=0
            )
    
    def _calculate_overall_health(self, health_checks: Dict[str, HealthCheck]) -> HealthStatus:
        """Calculate overall system health based on individual checks"""
        if not health_checks:
            return HealthStatus.UNKNOWN
        
        status_counts = {
            HealthStatus.HEALTHY: 0,
            HealthStatus.DEGRADED: 0,
            HealthStatus.UNHEALTHY: 0,
            HealthStatus.UNKNOWN: 0
        }
        
        for check in health_checks.values():
            status_counts[check.status] += 1
        
        total_checks = len(health_checks)
        
        # If any critical checks are unhealthy, overall is unhealthy
        critical_checks = ["database", "system_resources", "security_services"]
        critical_unhealthy = any(
            health_checks.get(check, HealthCheck("", HealthStatus.UNKNOWN, "", {}, datetime.now(), 0)).status == HealthStatus.UNHEALTHY
            for check in critical_checks
        )
        
        if critical_unhealthy:
            return HealthStatus.UNHEALTHY
        
        # Calculate health percentage
        healthy_percentage = (status_counts[HealthStatus.HEALTHY] / total_checks) * 100
        
        if healthy_percentage >= 90:
            return HealthStatus.HEALTHY
        elif healthy_percentage >= 70:
            return HealthStatus.DEGRADED
        else:
            return HealthStatus.UNHEALTHY
    
    def _generate_health_summary(self, health_checks: Dict[str, HealthCheck]) -> Dict[str, Any]:
        """Generate health summary statistics"""
        status_counts = {
            "healthy": 0,
            "degraded": 0,
            "unhealthy": 0,
            "unknown": 0
        }
        
        total_response_time = 0
        for check in health_checks.values():
            status_counts[check.status.value] += 1
            total_response_time += check.response_time_ms
        
        avg_response_time = total_response_time / len(health_checks) if health_checks else 0
        
        return {
            "total_checks": len(health_checks),
            "status_counts": status_counts,
            "avg_response_time_ms": avg_response_time,
            "health_percentage": (status_counts["healthy"] / len(health_checks) * 100) if health_checks else 0
        }
    
    def _store_health_history(self, health_checks: Dict[str, HealthCheck]):
        """Store health check results in history"""
        timestamp = datetime.now(timezone.utc)
        
        history_entry = {
            "timestamp": timestamp,
            "overall_status": self._calculate_overall_health(health_checks),
            "check_count": len(health_checks),
            "healthy_count": sum(1 for check in health_checks.values() if check.status == HealthStatus.HEALTHY)
        }
        
        self.health_history.append(history_entry)
        
        # Trim history
        if len(self.health_history) > self.max_history_size:
            self.health_history = self.health_history[-self.max_history_size:]
    
    def get_health_history(self, hours: int = 24) -> List[Dict[str, Any]]:
        """Get health check history"""
        cutoff_time = datetime.now(timezone.utc) - timedelta(hours=hours)
        return [
            {
                "timestamp": entry["timestamp"].isoformat(),
                "overall_status": entry["overall_status"].value,
                "check_count": entry["check_count"],
                "healthy_count": entry["healthy_count"]
            }
            for entry in self.health_history
            if entry["timestamp"] >= cutoff_time
        ]
    
    async def get_quick_health_status(self) -> Dict[str, Any]:
        """Get a quick health status without running all checks"""
        if not self.health_checks:
            return {"status": "unknown", "message": "No health checks have been run"}
        
        overall_status = self._calculate_overall_health(self.health_checks)
        summary = self._generate_health_summary(self.health_checks)
        
        return {
            "status": overall_status.value,
            "last_check": max(check.timestamp for check in self.health_checks.values()).isoformat(),
            "summary": summary
        }

# Global comprehensive health service instance
comprehensive_health_service = ComprehensiveHealthService()