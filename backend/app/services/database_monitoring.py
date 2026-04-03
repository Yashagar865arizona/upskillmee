"""
Database Monitoring Integration Service

This service integrates query performance monitoring with the database engine
and provides easy-to-use methods for monitoring database operations.
"""

import logging
from typing import Dict, List, Any, Optional
from contextlib import contextmanager
from sqlalchemy.orm import Session
from sqlalchemy.engine import Engine

from .query_performance_service import query_performance_monitor, QueryPerformanceService
from ..database.engine import engine as default_engine
from ..config import settings

logger = logging.getLogger(__name__)

class DatabaseMonitoringService:
    """Service for integrating database monitoring across the application."""
    
    def __init__(self):
        self.performance_monitor = query_performance_monitor
        self._initialized = False
        
    def initialize(self, engine: Optional[Engine] = None):
        """Initialize database monitoring with the SQLAlchemy engine."""
        if self._initialized:
            return
            
        try:
            # Use provided engine or get the default one
            if engine is None:
                engine = default_engine
            
            # Set up automatic query monitoring
            self.performance_monitor.setup_sqlalchemy_monitoring(engine)
            
            # Configure monitoring based on environment
            if settings.ENVIRONMENT == "production":
                # More conservative monitoring in production
                self.performance_monitor.slow_query_threshold = 0.2  # 200ms
                self.performance_monitor.max_metrics_history = 5000
            elif settings.ENVIRONMENT == "development":
                # More detailed monitoring in development
                self.performance_monitor.slow_query_threshold = 0.05  # 50ms
                self.performance_monitor.max_metrics_history = 10000
            else:
                # Default settings for other environments
                self.performance_monitor.slow_query_threshold = 0.1  # 100ms
                self.performance_monitor.max_metrics_history = 7500
            
            self._initialized = True
            logger.info(f"Database monitoring initialized for {settings.ENVIRONMENT} environment")
            logger.info(f"Slow query threshold: {self.performance_monitor.slow_query_threshold}s")
            
        except Exception as e:
            logger.error(f"Failed to initialize database monitoring: {e}")
            self._initialized = False
    
    def is_initialized(self) -> bool:
        """Check if monitoring is initialized."""
        return self._initialized
    
    @contextmanager
    def monitor_operation(self, operation_name: str):
        """Context manager for monitoring a specific database operation."""
        with self.performance_monitor.monitor_query(operation_name):
            yield
    
    def get_performance_report(self) -> Dict[str, Any]:
        """Get a comprehensive performance report."""
        if not self._initialized:
            return {"error": "Monitoring not initialized"}
        
        summary = self.performance_monitor.get_performance_summary()
        slow_queries = self.performance_monitor.get_slow_queries(limit=5)
        frequent_queries = self.performance_monitor.get_frequent_queries(limit=5)
        n_plus_one_issues = self.performance_monitor.get_n_plus_one_issues()
        
        return {
            "summary": summary,
            "slow_queries": [
                {
                    "pattern": q.query_pattern,
                    "count": q.count,
                    "avg_duration": q.avg_duration,
                    "max_duration": q.max_duration,
                    "slow_query_count": q.slow_query_count,
                    "tables": list(q.table_names)
                }
                for q in slow_queries
            ],
            "frequent_queries": [
                {
                    "pattern": q.query_pattern,
                    "count": q.count,
                    "avg_duration": q.avg_duration,
                    "tables": list(q.table_names)
                }
                for q in frequent_queries
            ],
            "n_plus_one_issues": n_plus_one_issues
        }
    
    def get_table_report(self, table_name: str) -> Dict[str, Any]:
        """Get performance report for a specific table."""
        if not self._initialized:
            return {"error": "Monitoring not initialized"}
        
        return self.performance_monitor.get_table_performance(table_name)
    
    def get_optimization_recommendations(self) -> List[Dict[str, Any]]:
        """Get recommendations for database optimization."""
        if not self._initialized:
            return [{"error": "Monitoring not initialized"}]
        
        recommendations = []
        
        # Get current performance data
        summary = self.performance_monitor.get_performance_summary()
        slow_queries = self.performance_monitor.get_slow_queries(limit=10)
        n_plus_one_issues = self.performance_monitor.get_n_plus_one_issues()
        
        # Analyze slow queries
        if summary.get("slow_query_percentage", 0) > 10:
            recommendations.append({
                "type": "slow_queries",
                "priority": "high",
                "title": "High percentage of slow queries detected",
                "description": f"{summary['slow_query_percentage']:.1f}% of queries are slower than {self.performance_monitor.slow_query_threshold}s",
                "recommendation": "Review and optimize the slowest queries, consider adding indexes",
                "affected_queries": len(slow_queries)
            })
        
        # Analyze N+1 issues
        if len(n_plus_one_issues) > 0:
            recommendations.append({
                "type": "n_plus_one",
                "priority": "high",
                "title": "N+1 query problems detected",
                "description": f"Found {len(n_plus_one_issues)} potential N+1 query patterns",
                "recommendation": "Use eager loading (joinedload/selectinload) or batch queries to fix N+1 problems",
                "affected_patterns": len(n_plus_one_issues)
            })
        
        # Analyze query patterns
        operation_stats = summary.get("operation_stats", {})
        for op_type, stats in operation_stats.items():
            if stats.get("slow_percentage", 0) > 20:
                recommendations.append({
                    "type": "operation_performance",
                    "priority": "medium",
                    "title": f"Slow {op_type} operations",
                    "description": f"{stats['slow_percentage']:.1f}% of {op_type} operations are slow",
                    "recommendation": f"Optimize {op_type} queries, consider indexing frequently queried columns",
                    "operation_type": op_type
                })
        
        # Analyze table access patterns
        frequent_tables = summary.get("most_frequent_tables", [])
        for table_info in frequent_tables[:3]:  # Top 3 most accessed tables
            table_name = table_info["table"]
            table_stats = self.performance_monitor.get_table_performance(table_name)
            
            if table_stats.get("avg_duration", 0) > self.performance_monitor.slow_query_threshold:
                recommendations.append({
                    "type": "table_performance",
                    "priority": "medium",
                    "title": f"Table '{table_name}' has slow queries",
                    "description": f"Average query time: {table_stats['avg_duration']:.3f}s",
                    "recommendation": f"Add indexes to frequently queried columns in '{table_name}' table",
                    "table_name": table_name,
                    "query_count": table_info["query_count"]
                })
        
        # Performance trend analysis
        trend = summary.get("performance_trend", {})
        if trend.get("trend") == "degrading":
            recommendations.append({
                "type": "performance_trend",
                "priority": "medium",
                "title": "Database performance is degrading",
                "description": f"Query performance has worsened recently",
                "recommendation": "Monitor query patterns and consider database maintenance",
                "trend_data": trend
            })
        
        # Sort recommendations by priority
        priority_order = {"high": 0, "medium": 1, "low": 2}
        recommendations.sort(key=lambda x: priority_order.get(x["priority"], 3))
        
        return recommendations
    
    def enable_monitoring(self):
        """Enable query performance monitoring."""
        self.performance_monitor.enable_monitoring()
        logger.info("Database monitoring enabled")
    
    def disable_monitoring(self):
        """Disable query performance monitoring."""
        self.performance_monitor.disable_monitoring()
        logger.info("Database monitoring disabled")
    
    def reset_metrics(self):
        """Reset all monitoring metrics."""
        self.performance_monitor.reset_metrics()
        logger.info("Database monitoring metrics reset")
    
    def export_metrics(self) -> Dict[str, Any]:
        """Export all metrics for external analysis."""
        if not self._initialized:
            return {"error": "Monitoring not initialized"}
        
        return {
            "performance_summary": self.performance_monitor.get_performance_summary(),
            "slow_queries": [
                {
                    "pattern": q.query_pattern,
                    "count": q.count,
                    "total_duration": q.total_duration,
                    "avg_duration": q.avg_duration,
                    "min_duration": q.min_duration,
                    "max_duration": q.max_duration,
                    "slow_query_count": q.slow_query_count,
                    "tables": list(q.table_names)
                }
                for q in self.performance_monitor.query_stats.values()
            ],
            "n_plus_one_issues": self.performance_monitor.get_n_plus_one_issues(),
            "export_timestamp": logger.info("Metrics exported")
        }

# Global instance
db_monitoring = DatabaseMonitoringService()

def initialize_database_monitoring(engine: Optional[Engine] = None):
    """Initialize database monitoring - call this during app startup."""
    db_monitoring.initialize(engine)

def get_database_monitoring() -> DatabaseMonitoringService:
    """Get the database monitoring service instance."""
    return db_monitoring