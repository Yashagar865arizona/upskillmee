"""
Alerting service for system monitoring and error notifications.
Provides email, webhook, and logging-based alerts for critical system events.
"""

import logging
import smtplib
import json
import asyncio
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Any
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import httpx
from dataclasses import dataclass
from enum import Enum

from ..config import settings

logger = logging.getLogger(__name__)

class AlertSeverity(Enum):
    """Alert severity levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class AlertType(Enum):
    """Types of alerts"""
    HEALTH_CHECK = "health_check"
    PERFORMANCE = "performance"
    ERROR_RATE = "error_rate"
    RESOURCE_USAGE = "resource_usage"
    DATABASE = "database"
    AI_SERVICE = "ai_service"
    CUSTOM = "custom"

@dataclass
class Alert:
    """Alert data structure"""
    id: str
    type: AlertType
    severity: AlertSeverity
    title: str
    message: str
    details: Dict[str, Any]
    timestamp: datetime
    resolved: bool = False
    resolved_at: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert alert to dictionary"""
        return {
            "id": self.id,
            "type": self.type.value,
            "severity": self.severity.value,
            "title": self.title,
            "message": self.message,
            "details": self.details,
            "timestamp": self.timestamp.isoformat(),
            "resolved": self.resolved,
            "resolved_at": self.resolved_at.isoformat() if self.resolved_at else None
        }

class AlertingService:
    """Service for managing system alerts and notifications"""
    
    def __init__(self):
        self.active_alerts: Dict[str, Alert] = {}
        self.alert_history: List[Alert] = []
        self.max_history = 1000
        
        # Alert thresholds (configurable)
        self.thresholds = {
            "cpu_percent": 80.0,
            "memory_percent": 85.0,
            "disk_percent": 90.0,
            "error_rate_per_hour": 10.0,
            "database_response_time": 1.0,  # seconds
            "api_response_time": 2.0,  # seconds
            "failed_health_checks": 3,  # consecutive failures
        }
        
        # Notification settings
        self.email_enabled = getattr(settings, 'ALERT_EMAIL_ENABLED', False)
        self.webhook_enabled = getattr(settings, 'ALERT_WEBHOOK_ENABLED', False)
        self.webhook_url = getattr(settings, 'ALERT_WEBHOOK_URL', None)
        self.admin_emails = getattr(settings, 'ADMIN_EMAILS', [])
        
        # Rate limiting for alerts (prevent spam)
        self.alert_cooldown = {}  # alert_key -> last_sent_time
        self.cooldown_period = 300  # 5 minutes
    
    async def create_alert(self, alert_type: AlertType, severity: AlertSeverity,
                          title: str, message: str, details: Dict[str, Any] = None) -> Alert:
        """Create a new alert"""
        import uuid
        
        alert = Alert(
            id=str(uuid.uuid4()),
            type=alert_type,
            severity=severity,
            title=title,
            message=message,
            details=details or {},
            timestamp=datetime.now(timezone.utc)
        )
        
        # Store alert
        self.active_alerts[alert.id] = alert
        self.alert_history.append(alert)
        
        # Trim history if needed
        if len(self.alert_history) > self.max_history:
            self.alert_history = self.alert_history[-self.max_history:]
        
        # Send notifications
        await self._send_notifications(alert)
        
        logger.warning(f"Alert created: {alert.title} ({alert.severity.value})")
        return alert
    
    async def resolve_alert(self, alert_id: str) -> bool:
        """Resolve an active alert"""
        if alert_id in self.active_alerts:
            alert = self.active_alerts[alert_id]
            alert.resolved = True
            alert.resolved_at = datetime.now(timezone.utc)
            
            # Remove from active alerts
            del self.active_alerts[alert_id]
            
            logger.info(f"Alert resolved: {alert.title}")
            return True
        
        return False
    
    async def check_system_thresholds(self, system_status: Dict[str, Any]) -> List[Alert]:
        """Check system metrics against thresholds and create alerts"""
        alerts_created = []
        
        try:
            # Check health status
            if system_status.get('health', {}).get('overall_status') != 'healthy':
                alert = await self._check_and_create_alert(
                    "system_health",
                    AlertType.HEALTH_CHECK,
                    AlertSeverity.CRITICAL,
                    "System Health Check Failed",
                    "One or more system health checks are failing",
                    {"health_status": system_status.get('health', {})}
                )
                if alert:
                    alerts_created.append(alert)
            
            # Check system resources
            health_checks = system_status.get('health', {}).get('checks', {})
            system_resources = health_checks.get('system_resources', {})
            
            if system_resources.get('status') == 'healthy':
                # CPU check
                cpu_percent = system_resources.get('cpu_percent', 0)
                if cpu_percent > self.thresholds['cpu_percent']:
                    alert = await self._check_and_create_alert(
                        "high_cpu",
                        AlertType.RESOURCE_USAGE,
                        AlertSeverity.HIGH if cpu_percent > 90 else AlertSeverity.MEDIUM,
                        f"High CPU Usage: {cpu_percent:.1f}%",
                        f"CPU usage is above threshold ({self.thresholds['cpu_percent']}%)",
                        {"cpu_percent": cpu_percent, "threshold": self.thresholds['cpu_percent']}
                    )
                    if alert:
                        alerts_created.append(alert)
                
                # Memory check
                memory_percent = system_resources.get('memory', {}).get('percent', 0)
                if memory_percent > self.thresholds['memory_percent']:
                    alert = await self._check_and_create_alert(
                        "high_memory",
                        AlertType.RESOURCE_USAGE,
                        AlertSeverity.HIGH if memory_percent > 95 else AlertSeverity.MEDIUM,
                        f"High Memory Usage: {memory_percent:.1f}%",
                        f"Memory usage is above threshold ({self.thresholds['memory_percent']}%)",
                        {"memory_percent": memory_percent, "threshold": self.thresholds['memory_percent']}
                    )
                    if alert:
                        alerts_created.append(alert)
                
                # Disk check
                disk_percent = system_resources.get('disk', {}).get('percent', 0)
                if disk_percent > self.thresholds['disk_percent']:
                    alert = await self._check_and_create_alert(
                        "high_disk",
                        AlertType.RESOURCE_USAGE,
                        AlertSeverity.CRITICAL if disk_percent > 95 else AlertSeverity.HIGH,
                        f"High Disk Usage: {disk_percent:.1f}%",
                        f"Disk usage is above threshold ({self.thresholds['disk_percent']}%)",
                        {"disk_percent": disk_percent, "threshold": self.thresholds['disk_percent']}
                    )
                    if alert:
                        alerts_created.append(alert)
            
            # Check database performance
            db_health = health_checks.get('database', {})
            if db_health.get('status') == 'healthy':
                response_time = db_health.get('response_time', 0)
                if response_time > self.thresholds['database_response_time']:
                    alert = await self._check_and_create_alert(
                        "slow_database",
                        AlertType.DATABASE,
                        AlertSeverity.MEDIUM,
                        f"Slow Database Response: {response_time:.3f}s",
                        f"Database response time is above threshold ({self.thresholds['database_response_time']}s)",
                        {"response_time": response_time, "threshold": self.thresholds['database_response_time']}
                    )
                    if alert:
                        alerts_created.append(alert)
            elif db_health.get('status') == 'unhealthy':
                alert = await self._check_and_create_alert(
                    "database_unhealthy",
                    AlertType.DATABASE,
                    AlertSeverity.CRITICAL,
                    "Database Health Check Failed",
                    "Database is not responding or has errors",
                    {"database_status": db_health}
                )
                if alert:
                    alerts_created.append(alert)
            
            # Check error rates
            error_info = system_status.get('errors', {})
            error_rate = error_info.get('error_rate', 0)
            if error_rate > self.thresholds['error_rate_per_hour']:
                alert = await self._check_and_create_alert(
                    "high_error_rate",
                    AlertType.ERROR_RATE,
                    AlertSeverity.HIGH if error_rate > 50 else AlertSeverity.MEDIUM,
                    f"High Error Rate: {error_rate:.1f} errors/hour",
                    f"Error rate is above threshold ({self.thresholds['error_rate_per_hour']} errors/hour)",
                    {"error_rate": error_rate, "threshold": self.thresholds['error_rate_per_hour'], "error_details": error_info}
                )
                if alert:
                    alerts_created.append(alert)
            
        except Exception as e:
            logger.error(f"Error checking system thresholds: {e}")
        
        return alerts_created
    
    async def _check_and_create_alert(self, alert_key: str, alert_type: AlertType,
                                    severity: AlertSeverity, title: str, message: str,
                                    details: Dict[str, Any]) -> Optional[Alert]:
        """Check cooldown and create alert if needed"""
        now = datetime.now(timezone.utc)
        
        # Check if we're in cooldown period for this alert type
        if alert_key in self.alert_cooldown:
            last_sent = self.alert_cooldown[alert_key]
            if (now - last_sent).total_seconds() < self.cooldown_period:
                return None  # Skip alert due to cooldown
        
        # Create the alert
        alert = await self.create_alert(alert_type, severity, title, message, details)
        self.alert_cooldown[alert_key] = now
        
        return alert
    
    async def _send_notifications(self, alert: Alert):
        """Send notifications for an alert"""
        try:
            # Always log the alert
            log_level = {
                AlertSeverity.LOW: logging.INFO,
                AlertSeverity.MEDIUM: logging.WARNING,
                AlertSeverity.HIGH: logging.ERROR,
                AlertSeverity.CRITICAL: logging.CRITICAL
            }.get(alert.severity, logging.WARNING)
            
            logger.log(log_level, f"ALERT [{alert.severity.value.upper()}] {alert.title}: {alert.message}")
            
            # Send email notifications
            if self.email_enabled and self.admin_emails:
                await self._send_email_alert(alert)
            
            # Send webhook notifications
            if self.webhook_enabled and self.webhook_url:
                await self._send_webhook_alert(alert)
                
        except Exception as e:
            logger.error(f"Error sending notifications for alert {alert.id}: {e}")
    
    async def _send_email_alert(self, alert: Alert):
        """Send email notification for alert"""
        try:
            # Email configuration from settings
            smtp_server = getattr(settings, 'SMTP_SERVER', 'localhost')
            smtp_port = getattr(settings, 'SMTP_PORT', 587)
            smtp_username = getattr(settings, 'SMTP_USERNAME', '')
            smtp_password = getattr(settings, 'SMTP_PASSWORD', '')
            smtp_use_tls = getattr(settings, 'SMTP_USE_TLS', True)
            
            # Create email message
            msg = MIMEMultipart()
            msg['From'] = smtp_username or 'alerts@ponder.school'
            msg['To'] = ', '.join(self.admin_emails)
            msg['Subject'] = f"[PONDER ALERT] {alert.title}"
            
            # Email body
            body = f"""
Alert Details:
--------------
Severity: {alert.severity.value.upper()}
Type: {alert.type.value}
Time: {alert.timestamp.strftime('%Y-%m-%d %H:%M:%S UTC')}
Message: {alert.message}

Additional Details:
{json.dumps(alert.details, indent=2)}

Alert ID: {alert.id}

This is an automated alert from the Ponder monitoring system.
"""
            
            msg.attach(MIMEText(body, 'plain'))
            
            # Send email
            if smtp_username and smtp_password:
                server = smtplib.SMTP(smtp_server, smtp_port)
                if smtp_use_tls:
                    server.starttls()
                server.login(smtp_username, smtp_password)
                server.send_message(msg)
                server.quit()
                
                logger.info(f"Email alert sent for {alert.id}")
            else:
                logger.warning("Email credentials not configured, skipping email alert")
                
        except Exception as e:
            logger.error(f"Failed to send email alert: {e}")
    
    async def _send_webhook_alert(self, alert: Alert):
        """Send webhook notification for alert"""
        try:
            payload = {
                "alert": alert.to_dict(),
                "service": "ponder-backend",
                "environment": getattr(settings, 'ENVIRONMENT', 'unknown')
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    self.webhook_url,
                    json=payload,
                    timeout=10.0
                )
                
                if response.status_code == 200:
                    logger.info(f"Webhook alert sent for {alert.id}")
                else:
                    logger.warning(f"Webhook alert failed with status {response.status_code}")
                    
        except Exception as e:
            logger.error(f"Failed to send webhook alert: {e}")
    
    def get_active_alerts(self) -> List[Alert]:
        """Get all active alerts"""
        return list(self.active_alerts.values())
    
    def get_alert_history(self, hours: int = 24) -> List[Alert]:
        """Get alert history for the last N hours"""
        cutoff_time = datetime.now(timezone.utc) - timedelta(hours=hours)
        return [alert for alert in self.alert_history if alert.timestamp >= cutoff_time]
    
    def get_alert_summary(self) -> Dict[str, Any]:
        """Get summary of alerts"""
        active_alerts = self.get_active_alerts()
        recent_alerts = self.get_alert_history(24)
        
        # Count by severity
        severity_counts = {severity.value: 0 for severity in AlertSeverity}
        for alert in active_alerts:
            severity_counts[alert.severity.value] += 1
        
        # Count by type
        type_counts = {alert_type.value: 0 for alert_type in AlertType}
        for alert in recent_alerts:
            type_counts[alert.type.value] += 1
        
        return {
            "active_alerts_count": len(active_alerts),
            "recent_alerts_count": len(recent_alerts),
            "severity_breakdown": severity_counts,
            "type_breakdown": type_counts,
            "most_recent_alert": recent_alerts[-1].to_dict() if recent_alerts else None
        }
    
    def update_thresholds(self, new_thresholds: Dict[str, float]):
        """Update alert thresholds"""
        self.thresholds.update(new_thresholds)
        logger.info(f"Updated alert thresholds: {new_thresholds}")

# Global alerting service instance
alerting_service = AlertingService()