"""
Monitoring API endpoints for system health, performance metrics, and error tracking.
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Dict, List, Optional, Any
import logging

from ..services.monitoring_service import monitoring_service
from ..dependencies import get_current_user
from ..models.user import User

logger = logging.getLogger(__name__)

monitoring_router = APIRouter()

@monitoring_router.get("/health")
async def get_health_status():
    """Get system health status - public endpoint"""
    try:
        health_status = await monitoring_service.health_checker.run_all_checks()
        return health_status
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=500, detail="Health check failed")

@monitoring_router.get("/health/database")
async def get_database_health():
    """Get database health status - public endpoint"""
    try:
        db_health = await monitoring_service.health_checker.check_database_health()
        return db_health
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        raise HTTPException(status_code=500, detail="Database health check failed")

@monitoring_router.get("/database/detailed")
async def get_detailed_database_health(
    current_user: User = Depends(get_current_user)
):
    """Get detailed database health and performance metrics - requires admin access"""
    try:
        # Only admin users can access detailed database metrics
        if not getattr(current_user, 'is_admin', False):
            raise HTTPException(status_code=403, detail="Admin access required")
        
        # Import enhanced database monitoring
        from ..services.enhanced_db_monitoring import enhanced_db_monitor
        
        # Get comprehensive database health
        detailed_health = await enhanced_db_monitor.check_database_health()
        performance_summary = enhanced_db_monitor.get_performance_summary()
        
        return {
            "status": "success",
            "database_health": detailed_health,
            "performance_summary": performance_summary
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get detailed database health: {e}")
        raise HTTPException(status_code=500, detail="Failed to get detailed database health")

@monitoring_router.get("/database/query-analysis")
async def get_database_query_analysis(
    current_user: User = Depends(get_current_user)
):
    """Get database query analysis and recommendations - requires admin access"""
    try:
        # Only admin users can access query analysis
        if not getattr(current_user, 'is_admin', False):
            raise HTTPException(status_code=403, detail="Admin access required")
        
        # Import enhanced database monitoring
        from ..services.enhanced_db_monitoring import enhanced_db_monitor
        
        # Get query analysis
        query_analyzer = enhanced_db_monitor.query_analyzer
        
        return {
            "status": "success",
            "slow_queries": [
                {
                    "query": q["normalized_query"][:200] + "..." if len(q["normalized_query"]) > 200 else q["normalized_query"],
                    "duration": q["duration"],
                    "timestamp": q["timestamp"].isoformat(),
                    "issues": q["issues"],
                    "recommendations": q["recommendations"]
                }
                for q in list(query_analyzer.slow_queries)
            ],
            "table_access_patterns": dict(query_analyzer.table_access_patterns),
            "recommendations": query_analyzer.get_query_recommendations()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get database query analysis: {e}")
        raise HTTPException(status_code=500, detail="Failed to get database query analysis")

@monitoring_router.get("/health/system")
async def get_system_health():
    """Get system resource health status - public endpoint"""
    try:
        system_health = await monitoring_service.health_checker.check_system_resources()
        return system_health
    except Exception as e:
        logger.error(f"System health check failed: {e}")
        raise HTTPException(status_code=500, detail="System health check failed")

@monitoring_router.get("/status")
async def get_system_status(
    current_user: User = Depends(get_current_user)
):
    """Get comprehensive system status - requires authentication"""
    try:
        # Only admin users can access detailed system status
        if not getattr(current_user, 'is_admin', False):
            raise HTTPException(status_code=403, detail="Admin access required")
        
        system_status = await monitoring_service.get_system_status()
        return system_status
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get system status: {e}")
        raise HTTPException(status_code=500, detail="Failed to get system status")

@monitoring_router.get("/performance")
async def get_performance_metrics(
    current_user: User = Depends(get_current_user)
):
    """Get API performance metrics - requires admin access"""
    try:
        # Only admin users can access performance metrics
        if not getattr(current_user, 'is_admin', False):
            raise HTTPException(status_code=403, detail="Admin access required")
        
        performance_stats = monitoring_service.performance_monitor.get_all_stats()
        return {
            "status": "success",
            "performance_metrics": performance_stats
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get performance metrics: {e}")
        raise HTTPException(status_code=500, detail="Failed to get performance metrics")

@monitoring_router.get("/performance/{endpoint}")
async def get_endpoint_performance(
    endpoint: str,
    method: str = Query("GET", description="HTTP method"),
    current_user: User = Depends(get_current_user)
):
    """Get performance metrics for a specific endpoint"""
    try:
        # Only admin users can access performance metrics
        if not getattr(current_user, 'is_admin', False):
            raise HTTPException(status_code=403, detail="Admin access required")
        
        # Clean up endpoint path
        if not endpoint.startswith('/'):
            endpoint = '/' + endpoint
        
        endpoint_stats = monitoring_service.performance_monitor.get_endpoint_stats(endpoint, method.upper())
        return {
            "status": "success",
            "endpoint": endpoint,
            "method": method.upper(),
            "metrics": endpoint_stats
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get endpoint performance: {e}")
        raise HTTPException(status_code=500, detail="Failed to get endpoint performance")

@monitoring_router.get("/errors")
async def get_error_summary(
    hours: int = Query(24, description="Number of hours to analyze"),
    current_user: User = Depends(get_current_user)
):
    """Get error summary - requires admin access"""
    try:
        # Only admin users can access error data
        if not getattr(current_user, 'is_admin', False):
            raise HTTPException(status_code=403, detail="Admin access required")
        
        error_summary = monitoring_service.error_tracker.get_error_summary(hours)
        return {
            "status": "success",
            "period_hours": hours,
            "error_summary": error_summary
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get error summary: {e}")
        raise HTTPException(status_code=500, detail="Failed to get error summary")

@monitoring_router.get("/metrics/historical/{metric_name}")
async def get_historical_metrics(
    metric_name: str,
    hours: int = Query(24, description="Number of hours of historical data"),
    current_user: User = Depends(get_current_user)
):
    """Get historical metrics data - requires admin access"""
    try:
        # Only admin users can access historical metrics
        if not getattr(current_user, 'is_admin', False):
            raise HTTPException(status_code=403, detail="Admin access required")
        
        historical_data = await monitoring_service.get_historical_metrics(metric_name, hours)
        return {
            "status": "success",
            "metric_name": metric_name,
            "period_hours": hours,
            "data": historical_data
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get historical metrics: {e}")
        raise HTTPException(status_code=500, detail="Failed to get historical metrics")

@monitoring_router.get("/alerts")
async def get_system_alerts(
    current_user: User = Depends(get_current_user)
):
    """Get active system alerts"""
    try:
        # Only admin users can access alerts
        if not getattr(current_user, 'is_admin', False):
            raise HTTPException(status_code=403, detail="Admin access required")
        
        # Import alerting service
        from ..services.alerting_service import alerting_service
        
        # Get active alerts
        active_alerts = alerting_service.get_active_alerts()
        alert_summary = alerting_service.get_alert_summary()
        
        return {
            "status": "success",
            "active_alerts": [alert.to_dict() for alert in active_alerts],
            "summary": alert_summary
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get system alerts: {e}")
        raise HTTPException(status_code=500, detail="Failed to get system alerts")

@monitoring_router.get("/alerts/history")
async def get_alert_history(
    hours: int = Query(24, description="Number of hours of history to retrieve"),
    current_user: User = Depends(get_current_user)
):
    """Get alert history"""
    try:
        # Only admin users can access alert history
        if not getattr(current_user, 'is_admin', False):
            raise HTTPException(status_code=403, detail="Admin access required")
        
        # Import alerting service
        from ..services.alerting_service import alerting_service
        
        # Get alert history
        alert_history = alerting_service.get_alert_history(hours)
        
        return {
            "status": "success",
            "period_hours": hours,
            "alert_count": len(alert_history),
            "alerts": [alert.to_dict() for alert in alert_history]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get alert history: {e}")
        raise HTTPException(status_code=500, detail="Failed to get alert history")

@monitoring_router.post("/alerts/{alert_id}/resolve")
async def resolve_alert(
    alert_id: str,
    current_user: User = Depends(get_current_user)
):
    """Resolve an active alert"""
    try:
        # Only admin users can resolve alerts
        if not getattr(current_user, 'is_admin', False):
            raise HTTPException(status_code=403, detail="Admin access required")
        
        # Import alerting service
        from ..services.alerting_service import alerting_service
        
        # Resolve the alert
        success = await alerting_service.resolve_alert(alert_id)
        
        if success:
            return {
                "status": "success",
                "message": f"Alert {alert_id} resolved successfully"
            }
        else:
            raise HTTPException(status_code=404, detail="Alert not found or already resolved")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to resolve alert {alert_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to resolve alert")

@monitoring_router.get("/alerts/thresholds")
async def get_alert_thresholds(
    current_user: User = Depends(get_current_user)
):
    """Get current alert thresholds"""
    try:
        # Only admin users can access thresholds
        if not getattr(current_user, 'is_admin', False):
            raise HTTPException(status_code=403, detail="Admin access required")
        
        # Import alerting service
        from ..services.alerting_service import alerting_service
        
        return {
            "status": "success",
            "thresholds": alerting_service.thresholds
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get alert thresholds: {e}")
        raise HTTPException(status_code=500, detail="Failed to get alert thresholds")

@monitoring_router.put("/alerts/thresholds")
async def update_alert_thresholds(
    thresholds: Dict[str, float],
    current_user: User = Depends(get_current_user)
):
    """Update alert thresholds"""
    try:
        # Only admin users can update thresholds
        if not getattr(current_user, 'is_admin', False):
            raise HTTPException(status_code=403, detail="Admin access required")
        
        # Import alerting service
        from ..services.alerting_service import alerting_service
        
        # Update thresholds
        alerting_service.update_thresholds(thresholds)
        
        return {
            "status": "success",
            "message": "Alert thresholds updated successfully",
            "updated_thresholds": thresholds
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update alert thresholds: {e}")
        raise HTTPException(status_code=500, detail="Failed to update alert thresholds")

@monitoring_router.post("/test-error")
async def test_error_tracking(
    current_user: User = Depends(get_current_user)
):
    """Test endpoint to generate an error for testing error tracking"""
    try:
        # Only admin users can test error tracking
        if not getattr(current_user, 'is_admin', False):
            raise HTTPException(status_code=403, detail="Admin access required")
        
        # Generate a test error
        raise Exception("This is a test error for monitoring system validation")
        
    except HTTPException:
        raise
    except Exception as e:
        # Track the error
        monitoring_service.error_tracker.track_error(e, {
            "endpoint": "/monitoring/test-error",
            "user_id": str(current_user.id),
            "test": True
        })
        
        return {
            "status": "success",
            "message": "Test error generated and tracked successfully"
        }

# Create router instance
router = monitoring_router