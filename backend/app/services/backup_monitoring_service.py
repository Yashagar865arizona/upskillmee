"""
Backup monitoring service that integrates with the production monitoring system.
Monitors backup health, schedules, and provides automated recovery procedures.
"""

import logging
import asyncio
import subprocess
import json
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Any
from pathlib import Path
from dataclasses import dataclass
from enum import Enum

from .alerting_service import alerting_service, AlertType, AlertSeverity
from ..config import settings

logger = logging.getLogger(__name__)

class BackupStatus(Enum):
    """Backup status levels"""
    SUCCESS = "success"
    FAILED = "failed"
    IN_PROGRESS = "in_progress"
    SCHEDULED = "scheduled"
    OVERDUE = "overdue"

class BackupType(Enum):
    """Types of backups"""
    DATABASE = "database"
    FILESYSTEM = "filesystem"
    DOCKER_VOLUMES = "docker_volumes"
    CONFIGURATION = "configuration"
    FULL_SYSTEM = "full_system"

@dataclass
class BackupJob:
    """Backup job data structure"""
    id: str
    type: BackupType
    schedule: str  # cron format
    last_run: Optional[datetime]
    next_run: datetime
    status: BackupStatus
    duration: Optional[float]  # seconds
    size: Optional[int]  # bytes
    error_message: Optional[str] = None
    retention_days: int = 30
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert backup job to dictionary"""
        return {
            "id": self.id,
            "type": self.type.value,
            "schedule": self.schedule,
            "last_run": self.last_run.isoformat() if self.last_run else None,
            "next_run": self.next_run.isoformat(),
            "status": self.status.value,
            "duration": self.duration,
            "size": self.size,
            "error_message": self.error_message,
            "retention_days": self.retention_days
        }

class BackupMonitoringService:
    """Service for monitoring backup operations and health"""
    
    def __init__(self):
        self.backup_jobs: Dict[str, BackupJob] = {}
        self.backup_history: List[Dict[str, Any]] = []
        self.max_history = 1000
        self.backup_script_path = Path("/opt/ponder/infrastructure/scripts/backup-system.sh")
        self.backup_base_dir = Path("/var/backups/ponder")
        self.monitoring_enabled = True
        
        # Initialize default backup jobs
        self._initialize_backup_jobs()
    
    def _initialize_backup_jobs(self):
        """Initialize default backup jobs"""
        now = datetime.now(timezone.utc)
        
        # Daily database backup
        self.backup_jobs["daily_database"] = BackupJob(
            id="daily_database",
            type=BackupType.DATABASE,
            schedule="0 2 * * *",  # 2 AM daily
            last_run=None,
            next_run=now.replace(hour=2, minute=0, second=0, microsecond=0),
            status=BackupStatus.SCHEDULED,
            duration=None,
            size=None,
            retention_days=7
        )
        
        # Daily filesystem backup
        self.backup_jobs["daily_filesystem"] = BackupJob(
            id="daily_filesystem",
            type=BackupType.FILESYSTEM,
            schedule="0 3 * * *",  # 3 AM daily
            last_run=None,
            next_run=now.replace(hour=3, minute=0, second=0, microsecond=0),
            status=BackupStatus.SCHEDULED,
            duration=None,
            size=None,
            retention_days=7
        )
        
        # Weekly full backup
        self.backup_jobs["weekly_full"] = BackupJob(
            id="weekly_full",
            type=BackupType.FULL_SYSTEM,
            schedule="0 1 * * 0",  # 1 AM on Sundays
            last_run=None,
            next_run=now.replace(hour=1, minute=0, second=0, microsecond=0),
            status=BackupStatus.SCHEDULED,
            duration=None,
            size=None,
            retention_days=30
        )
        
        # Monthly archive backup
        self.backup_jobs["monthly_archive"] = BackupJob(
            id="monthly_archive",
            type=BackupType.FULL_SYSTEM,
            schedule="0 0 1 * *",  # Midnight on 1st of month
            last_run=None,
            next_run=now.replace(day=1, hour=0, minute=0, second=0, microsecond=0),
            status=BackupStatus.SCHEDULED,
            duration=None,
            size=None,
            retention_days=365
        )
    
    async def run_backup(self, job_id: str) -> Dict[str, Any]:
        """Run a specific backup job"""
        if job_id not in self.backup_jobs:
            return {"success": False, "error": f"Backup job {job_id} not found"}
        
        job = self.backup_jobs[job_id]
        
        try:
            logger.info(f"Starting backup job: {job_id}")
            job.status = BackupStatus.IN_PROGRESS
            start_time = datetime.now(timezone.utc)
            
            # Run the backup script
            result = await self._execute_backup_script(job)
            
            # Update job status
            end_time = datetime.now(timezone.utc)
            job.duration = (end_time - start_time).total_seconds()
            job.last_run = start_time
            
            if result["success"]:
                job.status = BackupStatus.SUCCESS
                job.error_message = None
                job.size = result.get("size")
                
                # Schedule next run
                job.next_run = self._calculate_next_run(job.schedule)
                
                logger.info(f"Backup job {job_id} completed successfully")
                
                # Record success in history
                self._record_backup_history(job, True, None)
                
                return {"success": True, "duration": job.duration, "size": job.size}
                
            else:
                job.status = BackupStatus.FAILED
                job.error_message = result.get("error", "Unknown error")
                
                logger.error(f"Backup job {job_id} failed: {job.error_message}")
                
                # Create alert for failed backup
                await alerting_service.create_alert(
                    AlertType.CUSTOM,
                    AlertSeverity.HIGH,
                    f"Backup Failed: {job_id}",
                    f"Backup job {job_id} failed: {job.error_message}",
                    {"job_id": job_id, "backup_type": job.type.value, "error": job.error_message}
                )
                
                # Record failure in history
                self._record_backup_history(job, False, job.error_message)
                
                return {"success": False, "error": job.error_message}
                
        except Exception as e:
            job.status = BackupStatus.FAILED
            job.error_message = str(e)
            
            logger.error(f"Exception during backup job {job_id}: {e}")
            
            # Create critical alert for backup exception
            await alerting_service.create_alert(
                AlertType.CUSTOM,
                AlertSeverity.CRITICAL,
                f"Backup Exception: {job_id}",
                f"Backup job {job_id} encountered an exception: {str(e)}",
                {"job_id": job_id, "backup_type": job.type.value, "exception": str(e)}
            )
            
            self._record_backup_history(job, False, str(e))
            
            return {"success": False, "error": str(e)}
    
    async def _execute_backup_script(self, job: BackupJob) -> Dict[str, Any]:
        """Execute the backup script for a specific job"""
        try:
            # Determine backup type argument
            backup_type_map = {
                BackupType.DATABASE: "daily",
                BackupType.FILESYSTEM: "daily",
                BackupType.DOCKER_VOLUMES: "daily",
                BackupType.FULL_SYSTEM: "weekly" if "weekly" in job.id else "monthly"
            }
            
            backup_arg = backup_type_map.get(job.type, "daily")
            
            # Execute backup script
            process = await asyncio.create_subprocess_exec(
                str(self.backup_script_path),
                backup_arg,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            if process.returncode == 0:
                # Parse output for backup size if available
                output = stdout.decode('utf-8')
                size = self._extract_backup_size(output)
                
                return {"success": True, "output": output, "size": size}
            else:
                error_output = stderr.decode('utf-8')
                return {"success": False, "error": error_output}
                
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def _extract_backup_size(self, output: str) -> Optional[int]:
        """Extract backup size from script output"""
        try:
            # Look for size information in output
            lines = output.split('\n')
            for line in lines:
                if 'backup created' in line.lower() and 'bytes' in line.lower():
                    # Extract size from line
                    import re
                    size_match = re.search(r'(\d+)\s*bytes', line)
                    if size_match:
                        return int(size_match.group(1))
        except Exception:
            pass
        
        return None
    
    def _calculate_next_run(self, cron_schedule: str) -> datetime:
        """Calculate next run time from cron schedule"""
        # Simple implementation - in production, use croniter library
        now = datetime.now(timezone.utc)
        
        # Parse basic cron patterns
        if cron_schedule == "0 2 * * *":  # Daily at 2 AM
            next_run = now.replace(hour=2, minute=0, second=0, microsecond=0)
            if next_run <= now:
                next_run += timedelta(days=1)
        elif cron_schedule == "0 3 * * *":  # Daily at 3 AM
            next_run = now.replace(hour=3, minute=0, second=0, microsecond=0)
            if next_run <= now:
                next_run += timedelta(days=1)
        elif cron_schedule == "0 1 * * 0":  # Weekly on Sunday at 1 AM
            next_run = now.replace(hour=1, minute=0, second=0, microsecond=0)
            days_until_sunday = (6 - now.weekday()) % 7
            if days_until_sunday == 0 and next_run <= now:
                days_until_sunday = 7
            next_run += timedelta(days=days_until_sunday)
        elif cron_schedule == "0 0 1 * *":  # Monthly on 1st at midnight
            if now.day == 1 and now.hour == 0:
                # Next month
                if now.month == 12:
                    next_run = now.replace(year=now.year + 1, month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
                else:
                    next_run = now.replace(month=now.month + 1, day=1, hour=0, minute=0, second=0, microsecond=0)
            else:
                # This month or next month
                try:
                    next_run = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
                    if next_run <= now:
                        if now.month == 12:
                            next_run = now.replace(year=now.year + 1, month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
                        else:
                            next_run = now.replace(month=now.month + 1, day=1, hour=0, minute=0, second=0, microsecond=0)
                except ValueError:
                    # Handle month with fewer days
                    next_run = now.replace(month=now.month + 1, day=1, hour=0, minute=0, second=0, microsecond=0)
        else:
            # Default to next day
            next_run = now + timedelta(days=1)
        
        return next_run
    
    def _record_backup_history(self, job: BackupJob, success: bool, error: Optional[str]):
        """Record backup execution in history"""
        history_entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "job_id": job.id,
            "type": job.type.value,
            "success": success,
            "duration": job.duration,
            "size": job.size,
            "error": error
        }
        
        self.backup_history.append(history_entry)
        
        # Trim history if needed
        if len(self.backup_history) > self.max_history:
            self.backup_history = self.backup_history[-self.max_history:]
    
    async def check_backup_health(self) -> Dict[str, Any]:
        """Check overall backup system health"""
        try:
            health_status = {
                "overall_status": "healthy",
                "jobs_status": {},
                "overdue_jobs": [],
                "failed_jobs": [],
                "storage_status": {},
                "recent_failures": 0,
                "last_successful_backup": None
            }
            
            now = datetime.now(timezone.utc)
            recent_failures = 0
            last_successful_backup = None
            
            # Check each backup job
            for job_id, job in self.backup_jobs.items():
                job_status = {
                    "status": job.status.value,
                    "last_run": job.last_run.isoformat() if job.last_run else None,
                    "next_run": job.next_run.isoformat(),
                    "overdue": False
                }
                
                # Check if job is overdue
                if job.next_run < now and job.status != BackupStatus.IN_PROGRESS:
                    job_status["overdue"] = True
                    health_status["overdue_jobs"].append(job_id)
                    health_status["overall_status"] = "degraded"
                
                # Check for failed jobs
                if job.status == BackupStatus.FAILED:
                    health_status["failed_jobs"].append({
                        "job_id": job_id,
                        "error": job.error_message,
                        "last_run": job.last_run.isoformat() if job.last_run else None
                    })
                    health_status["overall_status"] = "unhealthy"
                
                # Track recent failures and successful backups
                if job.last_run:
                    if job.last_run >= now - timedelta(hours=24):
                        if job.status == BackupStatus.FAILED:
                            recent_failures += 1
                        elif job.status == BackupStatus.SUCCESS:
                            if not last_successful_backup or job.last_run > last_successful_backup:
                                last_successful_backup = job.last_run
                
                health_status["jobs_status"][job_id] = job_status
            
            health_status["recent_failures"] = recent_failures
            health_status["last_successful_backup"] = last_successful_backup.isoformat() if last_successful_backup else None
            
            # Check backup storage
            storage_status = await self._check_backup_storage()
            health_status["storage_status"] = storage_status
            
            if storage_status.get("available_space_gb", 0) < 1:  # Less than 1GB available
                health_status["overall_status"] = "critical"
            
            return health_status
            
        except Exception as e:
            logger.error(f"Error checking backup health: {e}")
            return {
                "overall_status": "unknown",
                "error": str(e)
            }
    
    async def _check_backup_storage(self) -> Dict[str, Any]:
        """Check backup storage status"""
        try:
            import shutil
            
            if self.backup_base_dir.exists():
                total, used, free = shutil.disk_usage(self.backup_base_dir)
                
                return {
                    "total_space_gb": total / (1024**3),
                    "used_space_gb": used / (1024**3),
                    "available_space_gb": free / (1024**3),
                    "usage_percent": (used / total) * 100,
                    "status": "healthy" if free > 1024**3 else "low_space"  # 1GB threshold
                }
            else:
                return {
                    "status": "directory_missing",
                    "error": f"Backup directory {self.backup_base_dir} does not exist"
                }
                
        except Exception as e:
            return {
                "status": "error",
                "error": str(e)
            }
    
    async def schedule_backup_monitoring(self):
        """Run periodic backup monitoring checks"""
        while self.monitoring_enabled:
            try:
                # Check for overdue backups
                await self._check_overdue_backups()
                
                # Check backup health
                health_status = await self.check_backup_health()
                
                # Create alerts for critical issues
                if health_status["overall_status"] == "critical":
                    await alerting_service.create_alert(
                        AlertType.CUSTOM,
                        AlertSeverity.CRITICAL,
                        "Backup System Critical",
                        "Backup system is in critical state",
                        health_status
                    )
                elif health_status["overall_status"] == "unhealthy":
                    await alerting_service.create_alert(
                        AlertType.CUSTOM,
                        AlertSeverity.HIGH,
                        "Backup System Unhealthy",
                        "Backup system has health issues",
                        health_status
                    )
                
                # Wait before next check
                await asyncio.sleep(3600)  # Check every hour
                
            except Exception as e:
                logger.error(f"Error in backup monitoring: {e}")
                await asyncio.sleep(300)  # Wait 5 minutes on error
    
    async def _check_overdue_backups(self):
        """Check for overdue backup jobs and create alerts"""
        now = datetime.now(timezone.utc)
        
        for job_id, job in self.backup_jobs.items():
            if job.next_run < now and job.status not in [BackupStatus.IN_PROGRESS, BackupStatus.FAILED]:
                # Mark as overdue
                job.status = BackupStatus.OVERDUE
                
                # Create alert
                await alerting_service.create_alert(
                    AlertType.CUSTOM,
                    AlertSeverity.MEDIUM,
                    f"Backup Overdue: {job_id}",
                    f"Backup job {job_id} is overdue (scheduled for {job.next_run.isoformat()})",
                    {"job_id": job_id, "scheduled_time": job.next_run.isoformat(), "backup_type": job.type.value}
                )
    
    def get_backup_jobs(self) -> Dict[str, Dict[str, Any]]:
        """Get all backup jobs"""
        return {job_id: job.to_dict() for job_id, job in self.backup_jobs.items()}
    
    def get_backup_history(self, hours: int = 24) -> List[Dict[str, Any]]:
        """Get backup history for the last N hours"""
        cutoff_time = datetime.now(timezone.utc) - timedelta(hours=hours)
        return [
            entry for entry in self.backup_history
            if datetime.fromisoformat(entry["timestamp"]) >= cutoff_time
        ]
    
    async def restore_from_backup(self, backup_file: str, restore_type: str) -> Dict[str, Any]:
        """Initiate backup restoration"""
        try:
            logger.warning(f"Starting backup restoration: {backup_file} ({restore_type})")
            
            # Create incident for restoration
            from .production_monitoring import production_monitoring
            await production_monitoring.incident_manager.create_incident(
                f"Backup Restoration: {restore_type}",
                f"Restoring from backup file: {backup_file}",
                AlertSeverity.HIGH,
                ["backup", "restoration", restore_type]
            )
            
            # Execute restoration script
            process = await asyncio.create_subprocess_exec(
                str(self.backup_script_path),
                "restore",
                backup_file,
                restore_type,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            if process.returncode == 0:
                logger.info(f"Backup restoration completed successfully")
                return {"success": True, "output": stdout.decode('utf-8')}
            else:
                error_output = stderr.decode('utf-8')
                logger.error(f"Backup restoration failed: {error_output}")
                return {"success": False, "error": error_output}
                
        except Exception as e:
            logger.error(f"Exception during backup restoration: {e}")
            return {"success": False, "error": str(e)}

# Global backup monitoring service instance
backup_monitoring = BackupMonitoringService()