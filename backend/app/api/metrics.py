"""
Metrics and monitoring endpoints.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..database import get_db
from typing import Dict, Any
import psutil
import os
from datetime import datetime, timedelta
from sqlalchemy import func, text
from ..models.user import UserSnapshot, UserProject
import logging

logger = logging.getLogger(__name__)

metrics_router = APIRouter(
    prefix="/metrics",
    tags=["metrics"]
)

@metrics_router.get("/")
async def get_basic_metrics(db: Session = Depends(get_db)):
    """Get basic system metrics and stats."""
    try:
        # System metrics
        cpu_percent = psutil.cpu_percent()
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        # Application metrics
        active_users = db.query(func.count(func.distinct(UserSnapshot.user_id)))\
            .filter(UserSnapshot.created_at > datetime.now() - timedelta(hours=24))\
            .scalar()
            
        total_projects = db.query(func.count(UserProject.id)).scalar()
        
        return {
            "system": {
                "cpu_usage": f"{cpu_percent}%",
                "memory_usage": f"{memory.percent}%",
                "disk_usage": f"{disk.percent}%"
            },
            "application": {
                "active_users_24h": active_users,
                "total_projects": total_projects
            },
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error getting basic metrics: {str(e)}")
        raise HTTPException(status_code=500, detail="Error fetching metrics")

@metrics_router.get("/detailed")
async def get_detailed_metrics(db: Session = Depends(get_db)):
    """Get detailed system and application metrics."""
    try:
        # System metrics
        cpu_times = psutil.cpu_times()
        memory_detailed = psutil.virtual_memory()
        disk_io = psutil.disk_io_counters()
        network = psutil.net_io_counters()
        
        # Database metrics
        db_stats = db.execute(text("""
            SELECT 
                (SELECT COUNT(*) FROM users) as total_users,
                (SELECT COUNT(*) FROM user_projects WHERE status = 'completed') as completed_projects,
                (SELECT COUNT(*) FROM user_projects WHERE status = 'in_progress') as active_projects,
                (SELECT AVG(CAST(project_metrics->>'completion_rate' AS FLOAT)) 
                 FROM user_projects) as avg_completion_rate
        """)).first()
        
        return {
            "system": {
                "cpu": {
                    "user": cpu_times.user,
                    "system": cpu_times.system,
                    "idle": cpu_times.idle
                },
                "memory": {
                    "total": memory_detailed.total if memory_detailed else 0,
                    "available": memory_detailed.available if memory_detailed else 0,
                    "used": memory_detailed.used if memory_detailed else 0,
                    "free": memory_detailed.free if memory_detailed else 0
                },
                "disk_io": {
                    "read_bytes": disk_io.read_bytes if disk_io else 0,
                    "write_bytes": disk_io.write_bytes if disk_io else 0
                },
                "network": {
                    "bytes_sent": network.bytes_sent if network else 0,
                    "bytes_recv": network.bytes_recv if network else 0
                }
            },
            "database": {
                "total_users": db_stats[0] if db_stats else 0,
                "completed_projects": db_stats[1] if db_stats else 0,
                "active_projects": db_stats[2] if db_stats else 0,
                "avg_completion_rate": float(db_stats[3]) if db_stats and db_stats[3] is not None else 0.0
            },
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error getting detailed metrics: {str(e)}")
        raise HTTPException(status_code=500, detail="Error fetching detailed metrics")

@metrics_router.get("/errors")
async def get_error_metrics():
    """Get error statistics from logs."""
    try:
        error_counts = {
            "critical": 0,
            "error": 0,
            "warning": 0
        }
        
        if os.path.exists("logs/app.log"):
            with open("logs/app.log", "r") as f:
                for line in f:
                    if "CRITICAL" in line:
                        error_counts["critical"] += 1
                    elif "ERROR" in line:
                        error_counts["error"] += 1
                    elif "WARNING" in line:
                        error_counts["warning"] += 1
        
        return {
            "error_counts": error_counts,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error getting error metrics: {str(e)}")
        raise HTTPException(status_code=500, detail="Error fetching error metrics")

@metrics_router.get("/performance")
async def get_performance_metrics(db: Session = Depends(get_db)):
    """Get API and database performance metrics."""
    try:
        # Get average query times
        query_stats = db.execute(text("""
            SELECT 
                AVG(EXTRACT(EPOCH FROM (updated_at - created_at))) as avg_query_time
            FROM user_snapshots
            WHERE created_at > NOW() - INTERVAL '1 hour'
        """)).first()
        
        return {
            "database": {
                "avg_query_time": float(query_stats[0]) if query_stats and query_stats[0] is not None else 0.0,
                "connections": db.execute(text("SELECT COUNT(*) FROM pg_stat_activity")).scalar()
            },
            "system": {
                "load_avg": os.getloadavg(),
                "cpu_count": psutil.cpu_count()
            },
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error getting performance metrics: {str(e)}")
        raise HTTPException(status_code=500, detail="Error fetching performance metrics")

@metrics_router.get("/cache")
async def get_cache_metrics():
    """Get cache statistics."""
    try:
        # This would need to be implemented based on your caching solution
        # For now, returning placeholder metrics
        return {
            "cache": {
                "size": 0,
                "hits": 0,
                "misses": 0,
                "hit_rate": 0
            },
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error getting cache metrics: {str(e)}")
        raise HTTPException(status_code=500, detail="Error fetching cache metrics")
