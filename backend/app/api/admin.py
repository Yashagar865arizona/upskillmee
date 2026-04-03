"""
Admin endpoints for data management.
"""

from fastapi import APIRouter, Depends, HTTPException, Security, Body
from fastapi.security import APIKeyHeader
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Dict, Optional
from datetime import datetime, timezone
import os

from ..database.session import get_db
from ..services.data_management_service import DataManagementService
from ..services.message_service import MessageService
from ..config import settings
from ..services.admin_service import AdminService
from ..services.user_service import UserService
from ..services.ai_integration_service import AIIntegrationService
from pydantic import BaseModel

admin_router = APIRouter(prefix="/admin", tags=["admin"])

# Initialize services with proper dependencies
data_service = DataManagementService()
admin_service = AdminService()
ai_service = AIIntegrationService()

# Security
API_KEY_HEADER = APIKeyHeader(name="X-Admin-Key")

from fastapi.security import APIKeyHeader

API_KEY_HEADER = APIKeyHeader(name="X-Admin-Key")

async def verify_admin_key(api_key: str = Security(API_KEY_HEADER)):
    print("Admin Key Received:::::::::::::::::::::::::::::::::::", api_key)
    print("Admin Key Expected:::::::::::::::::::::::::::::::::::", settings.ADMIN_API_KEY)
    if api_key != settings.ADMIN_API_KEY:
        raise HTTPException(status_code=403, detail="Access denied")
    return api_key


# Get user service with proper dependencies
async def get_user_service(db: AsyncSession = Depends(get_db)) -> UserService:
    """Get user service with proper dependencies."""
    message_service = MessageService(db)
    return UserService(message_service)

@admin_router.delete("/delete-user/{user_id}")
async def admin_delete_user(
    user_id: str,
    db: AsyncSession = Depends(get_db),
    _: str = Security(verify_admin_key)
):
    try:
        user_service = await get_user_service(db)
        return user_service.delete_user_data(user_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@admin_router.get("/stats")
async def get_stats(
    db: AsyncSession = Depends(get_db),
    _: str = Security(verify_admin_key)
):
    """Get system statistics."""
    try:
        return await data_service.get_system_stats(db)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@admin_router.post("/backup")
async def create_backup(
    db: AsyncSession = Depends(get_db),
    _: str = Security(verify_admin_key)
):
    """Create a database backup."""
    try:
        backup_path = await data_service.backup_database()
        return {"message": "Backup created successfully", "path": backup_path}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@admin_router.get("/backups")
async def list_backups(_: str = Security(verify_admin_key)):
    """List all available backups."""
    try:
        backups = await data_service.get_backup_list()
        return {"backups": backups}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@admin_router.post("/cleanup")
async def cleanup_old_data(
    days: int = 30,
    db: AsyncSession = Depends(get_db),
    _: str = Security(verify_admin_key)
):
    """Clean up old data."""
    if not settings.is_production:
        raise HTTPException(
            status_code=400,
            detail="Cleanup only available in production"
        )
    
    try:
        stats = await data_service.cleanup_old_data(db, days)
        return {
            "message": "Data cleanup completed successfully",
            "stats": stats
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@admin_router.post("/export-analytics")
async def export_analytics(
    db: AsyncSession = Depends(get_db),
    _: str = Security(verify_admin_key)
):
    """Export analytics data."""
    try:
        metrics = await data_service.export_analytics(db)
        return {
            "message": "Analytics exported successfully",
            "metrics": metrics
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Model management
class AIModelInfo(BaseModel):
    id: str
    provider: str
    description: str
    active: bool

class ModelChangeRequest(BaseModel):
    model_id: str

@admin_router.get("/models", response_model=List[AIModelInfo])
async def list_available_models(_: str = Security(verify_admin_key)):
    """List all available AI models."""
    try:
        models = []
        active_model = settings.ACTIVE_MODEL
        
        # Add OpenAI models
        models.append(AIModelInfo(
            id=settings.GPT_MODEL,
            provider="openai",
            description=f"OpenAI {settings.GPT_MODEL}",
            active=(active_model == settings.GPT_MODEL)
        ))
        
        # Add alternative models
        for model_id, model_config in settings.ALTERNATIVE_MODELS.items():
            models.append(AIModelInfo(
                id=model_id,
                provider=model_config.get("provider", "unknown"),
                description=model_config.get("description", model_id),
                active=(active_model == model_id)
            ))
            
        return models
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@admin_router.post("/models/switch")
async def switch_ai_model(request: ModelChangeRequest, _: str = Security(verify_admin_key)):
    """Switch the active AI model."""
    try:
        model_id = request.model_id
        
        # Validate model exists
        if model_id != settings.GPT_MODEL and model_id not in settings.ALTERNATIVE_MODELS:
            raise HTTPException(status_code=404, detail=f"Model {model_id} not found")
            
        # Check if API key is available
        if model_id != settings.GPT_MODEL:
            model_config = settings.ALTERNATIVE_MODELS[model_id]
            env_var = model_config.get("api_key_env")
            if env_var and env_var not in os.environ:
                raise HTTPException(
                    status_code=400, 
                    detail=f"Missing API key for {model_id}. Set the {env_var} environment variable."
                )
        
        # Update environment variable to change active model
        os.environ["ACTIVE_MODEL"] = model_id
        
        # Update settings
        settings.ACTIVE_MODEL = model_id
        
        return {
            "message": f"Successfully switched to {model_id}",
            "active_model": model_id
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Database Performance Monitoring Endpoints
@admin_router.get("/database/performance")
async def get_database_performance(_: str = Security(verify_admin_key)):
    """Get comprehensive database performance report."""
    try:
        from ..services.database_monitoring import get_database_monitoring
        monitoring = get_database_monitoring()
        
        if not monitoring.is_initialized():
            raise HTTPException(
                status_code=503,
                detail="Database monitoring not initialized"
            )
        
        return monitoring.get_performance_report()
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@admin_router.get("/database/performance/table/{table_name}")
async def get_table_performance(
    table_name: str,
    _: str = Security(verify_admin_key)
):
    """Get performance report for a specific table."""
    try:
        from ..services.database_monitoring import get_database_monitoring
        monitoring = get_database_monitoring()
        
        if not monitoring.is_initialized():
            raise HTTPException(
                status_code=503,
                detail="Database monitoring not initialized"
            )
        
        report = monitoring.get_table_report(table_name)
        if "message" in report and "not found" in report["message"].lower():
            raise HTTPException(status_code=404, detail=f"No performance data found for table '{table_name}'")
        
        return report
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@admin_router.get("/database/recommendations")
async def get_optimization_recommendations(_: str = Security(verify_admin_key)):
    """Get database optimization recommendations."""
    try:
        from ..services.database_monitoring import get_database_monitoring
        monitoring = get_database_monitoring()
        
        if not monitoring.is_initialized():
            raise HTTPException(
                status_code=503,
                detail="Database monitoring not initialized"
            )
        
        recommendations = monitoring.get_optimization_recommendations()
        return {
            "recommendations": recommendations,
            "count": len(recommendations),
            "generated_at": datetime.now(timezone.utc).isoformat()
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@admin_router.post("/database/monitoring/reset")
async def reset_monitoring_metrics(_: str = Security(verify_admin_key)):
    """Reset database monitoring metrics."""
    try:
        from ..services.database_monitoring import get_database_monitoring
        monitoring = get_database_monitoring()
        
        if not monitoring.is_initialized():
            raise HTTPException(
                status_code=503,
                detail="Database monitoring not initialized"
            )
        
        monitoring.reset_metrics()
        return {"message": "Database monitoring metrics reset successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@admin_router.post("/database/monitoring/enable")
async def enable_monitoring(_: str = Security(verify_admin_key)):
    """Enable database monitoring."""
    try:
        from ..services.database_monitoring import get_database_monitoring
        monitoring = get_database_monitoring()
        
        monitoring.enable_monitoring()
        return {"message": "Database monitoring enabled"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@admin_router.post("/database/monitoring/disable")
async def disable_monitoring(_: str = Security(verify_admin_key)):
    """Disable database monitoring."""
    try:
        from ..services.database_monitoring import get_database_monitoring
        monitoring = get_database_monitoring()
        
        monitoring.disable_monitoring()
        return {"message": "Database monitoring disabled"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@admin_router.get("/database/export")
async def export_database_metrics(_: str = Security(verify_admin_key)):
    """Export all database metrics for analysis."""
    try:
        from ..services.database_monitoring import get_database_monitoring
        monitoring = get_database_monitoring()
        
        if not monitoring.is_initialized():
            raise HTTPException(
                status_code=503,
                detail="Database monitoring not initialized"
            )
        
        return monitoring.export_metrics()
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# AI Integration Monitoring Endpoints
@admin_router.get("/ai/metrics")
async def get_ai_metrics(_: str = Security(verify_admin_key)):
    """Get comprehensive AI integration metrics."""
    try:
        basic_metrics = ai_service.get_usage_metrics()
        detailed_cost_metrics = ai_service.get_detailed_cost_metrics()
        error_metrics = ai_service.get_error_metrics()
        
        return {
            "basic_metrics": basic_metrics,
            "cost_metrics": detailed_cost_metrics,
            "error_metrics": error_metrics,
            "generated_at": datetime.now(timezone.utc).isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@admin_router.get("/ai/cost")
async def get_ai_cost_breakdown(_: str = Security(verify_admin_key)):
    """Get detailed AI cost breakdown and alerts."""
    try:
        cost_metrics = ai_service.get_detailed_cost_metrics()
        return cost_metrics
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@admin_router.get("/ai/errors")
async def get_ai_error_analysis(_: str = Security(verify_admin_key)):
    """Get AI error analysis and circuit breaker status."""
    try:
        error_metrics = ai_service.get_error_metrics()
        return error_metrics
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@admin_router.post("/ai/metrics/reset")
async def reset_ai_metrics(_: str = Security(verify_admin_key)):
    """Reset AI integration metrics."""
    try:
        ai_service.reset_usage_metrics()
        # Reset detailed cost metrics
        ai_service.detailed_cost_metrics = ai_service.__class__.__dict__['__annotations__']['detailed_cost_metrics'].__origin__()
        # Reset error counts
        ai_service.error_counts = {error_type: 0 for error_type in ai_service.error_counts.keys()}
        
        return {"message": "AI metrics reset successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

class CostThresholdUpdate(BaseModel):
    daily_threshold: Optional[float] = None
    monthly_threshold: Optional[float] = None

@admin_router.post("/ai/cost/thresholds")
async def update_cost_thresholds(
    thresholds: CostThresholdUpdate,
    _: str = Security(verify_admin_key)
):
    """Update AI cost alert thresholds."""
    try:
        if thresholds.daily_threshold is not None:
            ai_service.daily_cost_threshold = thresholds.daily_threshold
        
        if thresholds.monthly_threshold is not None:
            ai_service.monthly_cost_threshold = thresholds.monthly_threshold
        
        return {
            "message": "Cost thresholds updated successfully",
            "current_thresholds": {
                "daily": ai_service.daily_cost_threshold,
                "monthly": ai_service.monthly_cost_threshold
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

class CircuitBreakerConfig(BaseModel):
    provider: str
    failure_threshold: Optional[int] = None
    recovery_timeout: Optional[int] = None

@admin_router.post("/ai/circuit-breaker/config")
async def update_circuit_breaker_config(
    config: CircuitBreakerConfig,
    _: str = Security(verify_admin_key)
):
    """Update circuit breaker configuration."""
    try:
        from ..services.ai_integration_service import AIProvider
        
        # Validate provider
        try:
            provider = AIProvider(config.provider)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid provider: {config.provider}")
        
        breaker = ai_service.circuit_breakers[provider]
        
        if config.failure_threshold is not None:
            breaker.failure_threshold = config.failure_threshold
        
        if config.recovery_timeout is not None:
            breaker.recovery_timeout = config.recovery_timeout
        
        return {
            "message": f"Circuit breaker configuration updated for {config.provider}",
            "config": {
                "failure_threshold": breaker.failure_threshold,
                "recovery_timeout": breaker.recovery_timeout,
                "current_state": breaker.state
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@admin_router.post("/ai/circuit-breaker/reset")
async def reset_circuit_breakers(_: str = Security(verify_admin_key)):
    """Reset all circuit breakers to closed state."""
    try:
        from ..services.ai_integration_service import CircuitBreakerState
        
        for provider in ai_service.circuit_breakers:
            ai_service.circuit_breakers[provider] = CircuitBreakerState()
        
        return {"message": "All circuit breakers reset to closed state"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@admin_router.get("/ai/performance")
async def get_ai_performance_report(_: str = Security(verify_admin_key)):
    """Get comprehensive AI performance report."""
    try:
        basic_metrics = ai_service.get_usage_metrics()
        cost_metrics = ai_service.get_detailed_cost_metrics()
        error_metrics = ai_service.get_error_metrics()
        
        # Calculate performance indicators
        total_requests = basic_metrics.get("total_requests", 0)
        success_rate = basic_metrics.get("success_rate", 0.0)
        avg_response_time = basic_metrics.get("average_response_time", 0.0)
        total_cost = cost_metrics.get("total_cost", 0.0)
        
        performance_score = 0.0
        if total_requests > 0:
            # Calculate performance score (0-100)
            success_weight = success_rate * 40  # 40% weight for success rate
            speed_weight = max(0, (5.0 - avg_response_time) / 5.0) * 30  # 30% weight for speed (5s baseline)
            cost_efficiency = max(0, (0.01 - (total_cost / max(total_requests, 1))) / 0.01) * 30  # 30% weight for cost efficiency
            performance_score = success_weight + speed_weight + cost_efficiency
        
        return {
            "performance_score": round(performance_score, 2),
            "metrics_summary": {
                "total_requests": total_requests,
                "success_rate": round(success_rate * 100, 2),
                "average_response_time": round(avg_response_time, 2),
                "total_cost": total_cost,
                "cost_per_request": round(total_cost / max(total_requests, 1), 4)
            },
            "detailed_metrics": {
                "basic": basic_metrics,
                "cost": cost_metrics,
                "errors": error_metrics
            },
            "generated_at": datetime.now(timezone.utc).isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
