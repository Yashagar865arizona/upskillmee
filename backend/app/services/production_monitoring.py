"""
Production monitoring service with comprehensive dashboards, log aggregation, and incident response.
Extends the existing monitoring system with production-ready features.
"""

import logging
import json
import asyncio
import aiofiles
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Any
from pathlib import Path
import psutil
try:
    import docker
    DOCKER_AVAILABLE = True
except ImportError:
    DOCKER_AVAILABLE = False
    docker = None
from dataclasses import dataclass, asdict
from enum import Enum

from .monitoring_service import monitoring_service
from .alerting_service import alerting_service, AlertType, AlertSeverity
from ..config import settings

logger = logging.getLogger(__name__)

class IncidentStatus(Enum):
    """Incident status levels"""
    OPEN = "open"
    INVESTIGATING = "investigating"
    IDENTIFIED = "identified"
    MONITORING = "monitoring"
    RESOLVED = "resolved"

@dataclass
class Incident:
    """Incident data structure"""
    id: str
    title: str
    description: str
    status: IncidentStatus
    severity: AlertSeverity
    created_at: datetime
    updated_at: datetime
    resolved_at: Optional[datetime] = None
    affected_services: List[str] = None
    timeline: List[Dict[str, Any]] = None
    
    def __post_init__(self):
        if self.affected_services is None:
            self.affected_services = []
        if self.timeline is None:
            self.timeline = []
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert incident to dictionary"""
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "status": self.status.value,
            "severity": self.severity.value,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "resolved_at": self.resolved_at.isoformat() if self.resolved_at else None,
            "affected_services": self.affected_services,
            "timeline": self.timeline
        }

class LogAggregator:
    """Centralized log aggregation and analysis"""
    
    def __init__(self):
        self.log_dir = Path("logs")
        self.log_dir.mkdir(exist_ok=True)
        self.aggregated_logs = []
        self.max_logs = 10000
        self.log_patterns = {
            "error": ["ERROR", "CRITICAL", "Exception", "Traceback"],
            "warning": ["WARNING", "WARN"],
            "performance": ["slow", "timeout", "performance"],
            "security": ["authentication", "authorization", "security", "login", "failed"]
        }
    
    async def collect_logs(self) -> Dict[str, Any]:
        """Collect and analyze logs from all sources"""
        try:
            logs_summary = {
                "total_logs": 0,
                "error_count": 0,
                "warning_count": 0,
                "recent_errors": [],
                "log_sources": {},
                "patterns": {pattern: 0 for pattern in self.log_patterns.keys()}
            }
            
            # Collect application logs
            app_logs = await self._collect_app_logs()
            logs_summary["log_sources"]["application"] = len(app_logs)
            logs_summary["total_logs"] += len(app_logs)
            
            # Collect Docker container logs
            docker_logs = await self._collect_docker_logs()
            logs_summary["log_sources"]["docker"] = len(docker_logs)
            logs_summary["total_logs"] += len(docker_logs)
            
            # Analyze all logs
            all_logs = app_logs + docker_logs
            for log_entry in all_logs:
                # Count by level
                if "ERROR" in log_entry.get("level", "").upper():
                    logs_summary["error_count"] += 1
                    if len(logs_summary["recent_errors"]) < 10:
                        logs_summary["recent_errors"].append(log_entry)
                elif "WARNING" in log_entry.get("level", "").upper():
                    logs_summary["warning_count"] += 1
                
                # Pattern matching
                message = log_entry.get("message", "").lower()
                for pattern_name, keywords in self.log_patterns.items():
                    if any(keyword.lower() in message for keyword in keywords):
                        logs_summary["patterns"][pattern_name] += 1
            
            return logs_summary
            
        except Exception as e:
            logger.error(f"Error collecting logs: {e}")
            return {"error": str(e)}
    
    async def _collect_app_logs(self) -> List[Dict[str, Any]]:
        """Collect application logs"""
        logs = []
        try:
            log_file = self.log_dir / "app.log"
            if log_file.exists():
                async with aiofiles.open(log_file, 'r') as f:
                    lines = await f.readlines()
                    # Parse last 1000 lines
                    for line in lines[-1000:]:
                        if line.strip():
                            log_entry = self._parse_log_line(line.strip())
                            if log_entry:
                                logs.append(log_entry)
        except Exception as e:
            logger.error(f"Error reading app logs: {e}")
        
        return logs
    
    async def _collect_docker_logs(self) -> List[Dict[str, Any]]:
        """Collect Docker container logs"""
        logs = []
        if not DOCKER_AVAILABLE:
            logger.warning("Docker not available for log collection")
            return logs
            
        try:
            client = docker.from_env()
            containers = client.containers.list()
            
            for container in containers:
                if 'ponder' in container.name.lower():
                    try:
                        # Get last 100 log lines
                        container_logs = container.logs(tail=100, timestamps=True).decode('utf-8')
                        for line in container_logs.split('\n'):
                            if line.strip():
                                log_entry = self._parse_docker_log_line(line.strip(), container.name)
                                if log_entry:
                                    logs.append(log_entry)
                    except Exception as e:
                        logger.warning(f"Error reading logs from container {container.name}: {e}")
        except Exception as e:
            logger.error(f"Error accessing Docker logs: {e}")
        
        return logs
    
    def _parse_log_line(self, line: str) -> Optional[Dict[str, Any]]:
        """Parse application log line"""
        try:
            # Expected format: timestamp - logger - level - message
            parts = line.split(' - ', 3)
            if len(parts) >= 4:
                return {
                    "timestamp": parts[0],
                    "logger": parts[1],
                    "level": parts[2],
                    "message": parts[3],
                    "source": "application"
                }
        except Exception:
            pass
        
        return {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": "INFO",
            "message": line,
            "source": "application"
        }
    
    def _parse_docker_log_line(self, line: str, container_name: str) -> Optional[Dict[str, Any]]:
        """Parse Docker container log line"""
        try:
            # Docker logs format: timestamp message
            if ' ' in line:
                timestamp, message = line.split(' ', 1)
                return {
                    "timestamp": timestamp,
                    "level": "INFO",
                    "message": message,
                    "source": f"docker:{container_name}"
                }
        except Exception:
            pass
        
        return {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": "INFO",
            "message": line,
            "source": f"docker:{container_name}"
        }

class IncidentManager:
    """Incident response and management system"""
    
    def __init__(self):
        self.incidents: Dict[str, Incident] = {}
        self.incident_history: List[Incident] = []
        self.runbooks = self._load_runbooks()
    
    async def create_incident(self, title: str, description: str, severity: AlertSeverity,
                            affected_services: List[str] = None) -> Incident:
        """Create a new incident"""
        import uuid
        
        incident = Incident(
            id=str(uuid.uuid4()),
            title=title,
            description=description,
            status=IncidentStatus.OPEN,
            severity=severity,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
            affected_services=affected_services or []
        )
        
        # Add initial timeline entry
        incident.timeline.append({
            "timestamp": incident.created_at.isoformat(),
            "action": "incident_created",
            "description": f"Incident created: {title}",
            "user": "system"
        })
        
        self.incidents[incident.id] = incident
        self.incident_history.append(incident)
        
        # Create alert for incident
        await alerting_service.create_alert(
            AlertType.CUSTOM,
            severity,
            f"Incident Created: {title}",
            description,
            {"incident_id": incident.id, "affected_services": affected_services}
        )
        
        logger.critical(f"Incident created: {incident.id} - {title}")
        return incident
    
    async def update_incident_status(self, incident_id: str, status: IncidentStatus,
                                   description: str = None, user: str = "system") -> bool:
        """Update incident status"""
        if incident_id not in self.incidents:
            return False
        
        incident = self.incidents[incident_id]
        old_status = incident.status
        incident.status = status
        incident.updated_at = datetime.now(timezone.utc)
        
        # Add timeline entry
        timeline_entry = {
            "timestamp": incident.updated_at.isoformat(),
            "action": "status_changed",
            "description": description or f"Status changed from {old_status.value} to {status.value}",
            "user": user,
            "old_status": old_status.value,
            "new_status": status.value
        }
        incident.timeline.append(timeline_entry)
        
        # If resolved, set resolved timestamp and remove from active incidents
        if status == IncidentStatus.RESOLVED:
            incident.resolved_at = datetime.now(timezone.utc)
            del self.incidents[incident_id]
        
        logger.info(f"Incident {incident_id} status updated to {status.value}")
        return True
    
    def get_active_incidents(self) -> List[Incident]:
        """Get all active incidents"""
        return list(self.incidents.values())
    
    def get_incident_history(self, hours: int = 24) -> List[Incident]:
        """Get incident history"""
        cutoff_time = datetime.now(timezone.utc) - timedelta(hours=hours)
        return [incident for incident in self.incident_history if incident.created_at >= cutoff_time]
    
    def get_runbook(self, incident_type: str) -> Optional[Dict[str, Any]]:
        """Get runbook for incident type"""
        return self.runbooks.get(incident_type)
    
    def _load_runbooks(self) -> Dict[str, Dict[str, Any]]:
        """Load incident response runbooks"""
        return {
            "database_down": {
                "title": "Database Connection Issues",
                "steps": [
                    "Check database container status",
                    "Verify database connectivity",
                    "Check database logs for errors",
                    "Restart database container if needed",
                    "Verify application connectivity",
                    "Monitor for recovery"
                ],
                "contacts": ["database-admin@ponder.school"],
                "escalation_time": 15  # minutes
            },
            "high_error_rate": {
                "title": "High Application Error Rate",
                "steps": [
                    "Check application logs for error patterns",
                    "Identify root cause of errors",
                    "Check system resources (CPU, memory)",
                    "Review recent deployments",
                    "Implement fix or rollback",
                    "Monitor error rate recovery"
                ],
                "contacts": ["dev-team@ponder.school"],
                "escalation_time": 30
            },
            "system_overload": {
                "title": "System Resource Overload",
                "steps": [
                    "Check CPU and memory usage",
                    "Identify resource-intensive processes",
                    "Scale resources if possible",
                    "Implement rate limiting",
                    "Monitor system recovery",
                    "Plan capacity improvements"
                ],
                "contacts": ["ops-team@ponder.school"],
                "escalation_time": 20
            }
        }

class ProductionMonitoringService:
    """Enhanced production monitoring service"""
    
    def __init__(self):
        self.log_aggregator = LogAggregator()
        self.incident_manager = IncidentManager()
        self.dashboard_data = {}
        self.last_dashboard_update = datetime.now(timezone.utc)
        self.dashboard_update_interval = 60  # seconds
    
    async def get_production_dashboard(self) -> Dict[str, Any]:
        """Get comprehensive production monitoring dashboard"""
        try:
            # Check if we need to update dashboard data
            if self._should_update_dashboard():
                await self._update_dashboard_data()
            
            return self.dashboard_data
            
        except Exception as e:
            logger.error(f"Error getting production dashboard: {e}")
            return {"error": str(e)}
    
    def _should_update_dashboard(self) -> bool:
        """Check if dashboard data needs updating"""
        return (datetime.now(timezone.utc) - self.last_dashboard_update).total_seconds() >= self.dashboard_update_interval
    
    async def _update_dashboard_data(self):
        """Update dashboard data"""
        try:
            # Get system status
            system_status = await monitoring_service.get_system_status()
            
            # Get log analysis
            log_analysis = await self.log_aggregator.collect_logs()
            
            # Get active incidents
            active_incidents = self.incident_manager.get_active_incidents()
            
            # Get active alerts
            active_alerts = alerting_service.get_active_alerts()
            alert_summary = alerting_service.get_alert_summary()
            
            # Get service health
            service_health = await self._get_service_health()
            
            # Get performance metrics
            performance_metrics = await self._get_performance_metrics()
            
            self.dashboard_data = {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "system_status": system_status,
                "service_health": service_health,
                "performance_metrics": performance_metrics,
                "log_analysis": log_analysis,
                "active_incidents": [incident.to_dict() for incident in active_incidents],
                "active_alerts": [alert.to_dict() for alert in active_alerts],
                "alert_summary": alert_summary,
                "uptime": (datetime.now(timezone.utc) - monitoring_service.performance_monitor.start_time).total_seconds()
            }
            
            self.last_dashboard_update = datetime.now(timezone.utc)
            
        except Exception as e:
            logger.error(f"Error updating dashboard data: {e}")
            self.dashboard_data = {"error": str(e)}
    
    async def _get_service_health(self) -> Dict[str, Any]:
        """Get health status of all services"""
        services = {
            "database": "healthy",
            "redis": "healthy",
            "ai_services": "healthy",
            "web_server": "healthy",
            "background_tasks": "healthy"
        }
        
        if DOCKER_AVAILABLE:
            try:
                # Check Docker containers
                client = docker.from_env()
                containers = client.containers.list()
                
                for container in containers:
                    if 'ponder' in container.name.lower():
                        if container.status != 'running':
                            if 'db' in container.name or 'postgres' in container.name:
                                services["database"] = "unhealthy"
                            elif 'redis' in container.name:
                                services["redis"] = "unhealthy"
                            elif 'backend' in container.name:
                                services["web_server"] = "unhealthy"
                            elif 'frontend' in container.name:
                                services["web_server"] = "degraded"
            
            except Exception as e:
                logger.error(f"Error checking service health: {e}")
                services["docker"] = "unhealthy"
        else:
            logger.warning("Docker not available for service health checks")
            services["docker"] = "unavailable"
        
        return services
    
    async def _get_performance_metrics(self) -> Dict[str, Any]:
        """Get key performance metrics"""
        try:
            # Get system metrics
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            # Get API performance
            api_stats = monitoring_service.performance_monitor.get_all_stats()
            
            # Calculate average response time across all endpoints
            total_response_time = 0
            total_requests = 0
            for endpoint_stats in api_stats.values():
                if endpoint_stats['request_count'] > 0:
                    total_response_time += endpoint_stats['avg_response_time'] * endpoint_stats['request_count']
                    total_requests += endpoint_stats['request_count']
            
            avg_response_time = total_response_time / total_requests if total_requests > 0 else 0
            
            return {
                "system": {
                    "cpu_percent": cpu_percent,
                    "memory_percent": memory.percent,
                    "disk_percent": (disk.used / disk.total) * 100,
                    "load_average": psutil.getloadavg()[0] if hasattr(psutil, 'getloadavg') else 0
                },
                "api": {
                    "avg_response_time": avg_response_time,
                    "total_requests": total_requests,
                    "endpoints_monitored": len(api_stats)
                }
            }
            
        except Exception as e:
            logger.error(f"Error getting performance metrics: {e}")
            return {"error": str(e)}
    
    async def check_for_incidents(self):
        """Check system status and create incidents if needed"""
        try:
            system_status = await monitoring_service.get_system_status()
            
            # Check for critical system issues
            health_status = system_status.get('health', {})
            if health_status.get('overall_status') != 'healthy':
                # Check if we already have an active incident for this
                active_incidents = self.incident_manager.get_active_incidents()
                has_system_incident = any(
                    'system health' in incident.title.lower() 
                    for incident in active_incidents
                )
                
                if not has_system_incident:
                    await self.incident_manager.create_incident(
                        "System Health Check Failed",
                        "One or more critical system health checks are failing",
                        AlertSeverity.CRITICAL,
                        ["system", "health_checks"]
                    )
            
            # Check for high error rates
            error_info = system_status.get('errors', {})
            error_rate = error_info.get('error_rate', 0)
            if error_rate > 50:  # More than 50 errors per hour
                active_incidents = self.incident_manager.get_active_incidents()
                has_error_incident = any(
                    'error rate' in incident.title.lower() 
                    for incident in active_incidents
                )
                
                if not has_error_incident:
                    await self.incident_manager.create_incident(
                        f"High Error Rate: {error_rate:.1f} errors/hour",
                        f"Application error rate is critically high: {error_rate:.1f} errors/hour",
                        AlertSeverity.HIGH,
                        ["application", "errors"]
                    )
            
        except Exception as e:
            logger.error(f"Error checking for incidents: {e}")

# Global production monitoring service instance
production_monitoring = ProductionMonitoringService()