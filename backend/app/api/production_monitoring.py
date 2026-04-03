"""
Production monitoring API endpoints for dashboards, incidents, and backup management.
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Dict, List, Optional, Any
import logging

from ..services.production_monitoring import production_monitoring
from ..services.backup_monitoring_service import backup_monitoring
from ..dependencies import get_current_user
from ..models.user import User

logger = logging.getLogger(__name__)

production_router = APIRouter()

@production_router.get("/dashboard")
async def get_production_dashboard(
    current_user: User = Depends(get_current_user)
):
    """Get comprehensive production monitoring dashboard"""
    try:
        # Only admin users can access production dashboard
        if not getattr(current_user, 'is_admin', False):
            raise HTTPException(status_code=403, detail="Admin access required")
        
        dashboard_data = await production_monitoring.get_production_dashboard()
        return {
            "status": "success",
            "dashboard": dashboard_data
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get production dashboard: {e}")
        raise HTTPException(status_code=500, detail="Failed to get production dashboard")

@production_router.get("/logs/analysis")
async def get_log_analysis(
    current_user: User = Depends(get_current_user)
):
    """Get log aggregation and analysis"""
    try:
        # Only admin users can access log analysis
        if not getattr(current_user, 'is_admin', False):
            raise HTTPException(status_code=403, detail="Admin access required")
        
        log_analysis = await production_monitoring.log_aggregator.collect_logs()
        return {
            "status": "success",
            "log_analysis": log_analysis
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get log analysis: {e}")
        raise HTTPException(status_code=500, detail="Failed to get log analysis")

@production_router.get("/incidents")
async def get_incidents(
    active_only: bool = Query(False, description="Return only active incidents"),
    hours: int = Query(24, description="Hours of history for resolved incidents"),
    current_user: User = Depends(get_current_user)
):
    """Get incidents (active and/or historical)"""
    try:
        # Only admin users can access incidents
        if not getattr(current_user, 'is_admin', False):
            raise HTTPException(status_code=403, detail="Admin access required")
        
        incident_manager = production_monitoring.incident_manager
        
        if active_only:
            incidents = incident_manager.get_active_incidents()
            return {
                "status": "success",
                "active_incidents": [incident.to_dict() for incident in incidents],
                "count": len(incidents)
            }
        else:
            active_incidents = incident_manager.get_active_incidents()
            incident_history = incident_manager.get_incident_history(hours)
            
            return {
                "status": "success",
                "active_incidents": [incident.to_dict() for incident in active_incidents],
                "incident_history": [incident.to_dict() for incident in incident_history],
                "active_count": len(active_incidents),
                "history_count": len(incident_history)
            }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get incidents: {e}")
        raise HTTPException(status_code=500, detail="Failed to get incidents")

@production_router.post("/incidents")
async def create_incident(
    incident_data: Dict[str, Any],
    current_user: User = Depends(get_current_user)
):
    """Create a new incident"""
    try:
        # Only admin users can create incidents
        if not getattr(current_user, 'is_admin', False):
            raise HTTPException(status_code=403, detail="Admin access required")
        
        # Validate required fields
        required_fields = ["title", "description", "severity"]
        for field in required_fields:
            if field not in incident_data:
                raise HTTPException(status_code=400, detail=f"Missing required field: {field}")
        
        # Import severity enum
        from ..services.alerting_service import AlertSeverity
        
        # Parse severity
        try:
            severity = AlertSeverity(incident_data["severity"])
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid severity level")
        
        # Create incident
        incident = await production_monitoring.incident_manager.create_incident(
            title=incident_data["title"],
            description=incident_data["description"],
            severity=severity,
            affected_services=incident_data.get("affected_services", [])
        )
        
        return {
            "status": "success",
            "incident": incident.to_dict(),
            "message": f"Incident {incident.id} created successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to create incident: {e}")
        raise HTTPException(status_code=500, detail="Failed to create incident")

@production_router.put("/incidents/{incident_id}/status")
async def update_incident_status(
    incident_id: str,
    status_data: Dict[str, Any],
    current_user: User = Depends(get_current_user)
):
    """Update incident status"""
    try:
        # Only admin users can update incidents
        if not getattr(current_user, 'is_admin', False):
            raise HTTPException(status_code=403, detail="Admin access required")
        
        # Validate required fields
        if "status" not in status_data:
            raise HTTPException(status_code=400, detail="Missing required field: status")
        
        # Import status enum
        from ..services.production_monitoring import IncidentStatus
        
        # Parse status
        try:
            status = IncidentStatus(status_data["status"])
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid status")
        
        # Update incident
        success = await production_monitoring.incident_manager.update_incident_status(
            incident_id=incident_id,
            status=status,
            description=status_data.get("description"),
            user=current_user.email or "admin"
        )
        
        if success:
            return {
                "status": "success",
                "message": f"Incident {incident_id} status updated to {status.value}"
            }
        else:
            raise HTTPException(status_code=404, detail="Incident not found")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update incident status: {e}")
        raise HTTPException(status_code=500, detail="Failed to update incident status")

@production_router.get("/incidents/{incident_id}/runbook")
async def get_incident_runbook(
    incident_id: str,
    incident_type: str = Query(..., description="Type of incident for runbook lookup"),
    current_user: User = Depends(get_current_user)
):
    """Get runbook for incident type"""
    try:
        # Only admin users can access runbooks
        if not getattr(current_user, 'is_admin', False):
            raise HTTPException(status_code=403, detail="Admin access required")
        
        runbook = production_monitoring.incident_manager.get_runbook(incident_type)
        
        if runbook:
            return {
                "status": "success",
                "incident_id": incident_id,
                "incident_type": incident_type,
                "runbook": runbook
            }
        else:
            return {
                "status": "not_found",
                "message": f"No runbook found for incident type: {incident_type}",
                "available_types": list(production_monitoring.incident_manager.runbooks.keys())
            }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get runbook: {e}")
        raise HTTPException(status_code=500, detail="Failed to get runbook")

@production_router.get("/backup/status")
async def get_backup_status(
    current_user: User = Depends(get_current_user)
):
    """Get backup system status and health"""
    try:
        # Only admin users can access backup status
        if not getattr(current_user, 'is_admin', False):
            raise HTTPException(status_code=403, detail="Admin access required")
        
        # Get backup health
        health_status = await backup_monitoring.check_backup_health()
        
        # Get backup jobs
        backup_jobs = backup_monitoring.get_backup_jobs()
        
        return {
            "status": "success",
            "health": health_status,
            "jobs": backup_jobs
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get backup status: {e}")
        raise HTTPException(status_code=500, detail="Failed to get backup status")

@production_router.post("/backup/run/{job_id}")
async def run_backup_job(
    job_id: str,
    current_user: User = Depends(get_current_user)
):
    """Run a specific backup job manually"""
    try:
        # Only admin users can run backups
        if not getattr(current_user, 'is_admin', False):
            raise HTTPException(status_code=403, detail="Admin access required")
        
        result = await backup_monitoring.run_backup(job_id)
        
        if result["success"]:
            return {
                "status": "success",
                "job_id": job_id,
                "message": f"Backup job {job_id} completed successfully",
                "duration": result.get("duration"),
                "size": result.get("size")
            }
        else:
            return {
                "status": "failed",
                "job_id": job_id,
                "error": result.get("error"),
                "message": f"Backup job {job_id} failed"
            }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to run backup job {job_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to run backup job")

@production_router.get("/backup/history")
async def get_backup_history(
    hours: int = Query(24, description="Hours of backup history to retrieve"),
    current_user: User = Depends(get_current_user)
):
    """Get backup execution history"""
    try:
        # Only admin users can access backup history
        if not getattr(current_user, 'is_admin', False):
            raise HTTPException(status_code=403, detail="Admin access required")
        
        history = backup_monitoring.get_backup_history(hours)
        
        return {
            "status": "success",
            "period_hours": hours,
            "backup_count": len(history),
            "history": history
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get backup history: {e}")
        raise HTTPException(status_code=500, detail="Failed to get backup history")

@production_router.post("/backup/restore")
async def restore_from_backup(
    restore_data: Dict[str, Any],
    current_user: User = Depends(get_current_user)
):
    """Restore from backup (DANGEROUS OPERATION)"""
    try:
        # Only admin users can restore backups
        if not getattr(current_user, 'is_admin', False):
            raise HTTPException(status_code=403, detail="Admin access required")
        
        # Validate required fields
        required_fields = ["backup_file", "restore_type"]
        for field in required_fields:
            if field not in restore_data:
                raise HTTPException(status_code=400, detail=f"Missing required field: {field}")
        
        # Additional confirmation required for restore operations
        if not restore_data.get("confirm_restore", False):
            raise HTTPException(
                status_code=400, 
                detail="Restore operations require explicit confirmation. Set 'confirm_restore': true"
            )
        
        result = await backup_monitoring.restore_from_backup(
            backup_file=restore_data["backup_file"],
            restore_type=restore_data["restore_type"]
        )
        
        if result["success"]:
            return {
                "status": "success",
                "message": "Backup restoration completed successfully",
                "output": result.get("output")
            }
        else:
            return {
                "status": "failed",
                "error": result.get("error"),
                "message": "Backup restoration failed"
            }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to restore from backup: {e}")
        raise HTTPException(status_code=500, detail="Failed to restore from backup")

@production_router.get("/service-health")
async def get_service_health(
    current_user: User = Depends(get_current_user)
):
    """Get health status of all services"""
    try:
        # Only admin users can access service health
        if not getattr(current_user, 'is_admin', False):
            raise HTTPException(status_code=403, detail="Admin access required")
        
        service_health = await production_monitoring._get_service_health()
        
        return {
            "status": "success",
            "services": service_health,
            "timestamp": production_monitoring.last_dashboard_update.isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get service health: {e}")
        raise HTTPException(status_code=500, detail="Failed to get service health")

@production_router.get("/performance-metrics")
async def get_performance_metrics(
    current_user: User = Depends(get_current_user)
):
    """Get key performance metrics"""
    try:
        # Only admin users can access performance metrics
        if not getattr(current_user, 'is_admin', False):
            raise HTTPException(status_code=403, detail="Admin access required")
        
        performance_metrics = await production_monitoring._get_performance_metrics()
        
        return {
            "status": "success",
            "metrics": performance_metrics,
            "timestamp": production_monitoring.last_dashboard_update.isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get performance metrics: {e}")
        raise HTTPException(status_code=500, detail="Failed to get performance metrics")

@production_router.post("/check-incidents")
async def trigger_incident_check(
    current_user: User = Depends(get_current_user)
):
    """Manually trigger incident detection check"""
    try:
        # Only admin users can trigger incident checks
        if not getattr(current_user, 'is_admin', False):
            raise HTTPException(status_code=403, detail="Admin access required")
        
        await production_monitoring.check_for_incidents()
        
        return {
            "status": "success",
            "message": "Incident check completed"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to check for incidents: {e}")
        raise HTTPException(status_code=500, detail="Failed to check for incidents")

# Create router instance
router = production_router