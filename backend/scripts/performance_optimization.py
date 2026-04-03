#!/usr/bin/env python3
"""
Performance optimization script for Ponder backend.
Analyzes database queries, API response times, and system resources.
"""

import asyncio
import time
import psutil
import logging
from typing import Dict, List, Any
from sqlalchemy import text, inspect
from sqlalchemy.orm import Session
import json
import sys
import os

# Add the backend directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database.database import engine, get_db
from app.models import User, Message, Conversation, LearningPlan, UserProject
from app.services.query_performance_service import query_performance_monitor

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s'
)
logger = logging.getLogger(__name__)

class PerformanceOptimizer:
    """Analyzes and optimizes system performance."""
    
    def __init__(self):
        self.db_session = next(get_db())
        self.performance_data = {}
    
    def analyze_database_performance(self) -> Dict[str, Any]:
        """Analyze database query performance and suggest optimizations."""
        logger.info("Analyzing database performance...")
        
        analysis = {
            "connection_pool": self.analyze_connection_pool(),
            "slow_queries": self.identify_slow_queries(),
            "missing_indexes": self.check_missing_indexes(),
            "table_stats": self.get_table_statistics(),
            "query_patterns": self.analyze_query_patterns()
        }
        
        return analysis
    
    def analyze_connection_pool(self) -> Dict[str, Any]:
        """Analyze database connection pool usage."""
        pool = engine.pool
        
        try:
            pool_size = pool.size()
            checked_in = pool.checkedin()
            checked_out = pool.checkedout()
            overflow = pool.overflow()
            
            return {
                "pool_size": pool_size,
                "checked_in": checked_in,
                "checked_out": checked_out,
                "overflow": overflow,
                "status": "healthy" if checked_out < pool_size * 0.8 else "warning"
            }
        except Exception as e:
            logger.warning(f"Could not analyze connection pool: {e}")
            return {
                "pool_size": "unknown",
                "checked_in": "unknown", 
                "checked_out": "unknown",
                "overflow": "unknown",
                "status": "unknown"
            }
    
    def identify_slow_queries(self) -> List[Dict[str, Any]]:
        """Identify slow database queries."""
        slow_queries = []
        
        try:
            # Get slow queries from PostgreSQL
            result = self.db_session.execute(text("""
                SELECT 
                    query,
                    calls,
                    total_time,
                    mean_time,
                    rows
                FROM pg_stat_statements 
                WHERE mean_time > 100
                ORDER BY mean_time DESC 
                LIMIT 10
            """))
            
            for row in result:
                slow_queries.append({
                    "query": row.query[:200] + "..." if len(row.query) > 200 else row.query,
                    "calls": row.calls,
                    "total_time": row.total_time,
                    "mean_time": row.mean_time,
                    "rows": row.rows
                })
                
        except Exception as e:
            logger.warning(f"Could not fetch slow queries: {e}")
            # Fallback to query performance monitor data
            slow_queries = query_performance_monitor.get_slow_queries()
        
        return slow_queries
    
    def check_missing_indexes(self) -> List[Dict[str, Any]]:
        """Check for missing database indexes."""
        missing_indexes = []
        
        try:
            # Check for missing indexes on foreign keys
            result = self.db_session.execute(text("""
                SELECT 
                    schemaname,
                    tablename,
                    attname,
                    n_distinct,
                    correlation
                FROM pg_stats 
                WHERE schemaname = 'public'
                AND n_distinct > 100
                AND correlation < 0.1
            """))
            
            for row in result:
                missing_indexes.append({
                    "table": row.tablename,
                    "column": row.attname,
                    "distinct_values": row.n_distinct,
                    "correlation": row.correlation,
                    "recommendation": f"CREATE INDEX idx_{row.tablename}_{row.attname} ON {row.tablename}({row.attname});"
                })
                
        except Exception as e:
            logger.warning(f"Could not check missing indexes: {e}")
        
        return missing_indexes
    
    def get_table_statistics(self) -> Dict[str, Any]:
        """Get table size and row count statistics."""
        stats = {}
        
        try:
            # Get table sizes
            result = self.db_session.execute(text("""
                SELECT 
                    schemaname,
                    tablename,
                    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size,
                    pg_total_relation_size(schemaname||'.'||tablename) as size_bytes
                FROM pg_tables 
                WHERE schemaname = 'public'
                ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC
            """))
            
            for row in result:
                stats[row.tablename] = {
                    "size": row.size,
                    "size_bytes": row.size_bytes
                }
            
            # Get row counts for main tables
            tables = ['users', 'messages', 'conversations', 'learning_plans', 'user_projects']
            for table in tables:
                try:
                    count_result = self.db_session.execute(text(f"SELECT COUNT(*) FROM {table}"))
                    count = count_result.scalar()
                    if table in stats:
                        stats[table]["row_count"] = count
                    else:
                        stats[table] = {"row_count": count}
                except Exception as e:
                    logger.warning(f"Could not get row count for {table}: {e}")
                    
        except Exception as e:
            logger.warning(f"Could not get table statistics: {e}")
        
        return stats
    
    def analyze_query_patterns(self) -> Dict[str, Any]:
        """Analyze common query patterns and performance."""
        patterns = {
            "most_frequent_queries": [],
            "n_plus_one_queries": [],
            "full_table_scans": []
        }
        
        # Get query performance data from monitor
        query_data = query_performance_monitor.get_performance_summary()
        
        if query_data:
            patterns["most_frequent_queries"] = query_data.get("frequent_queries", [])
            patterns["average_response_time"] = query_data.get("average_response_time", 0)
            patterns["total_queries"] = query_data.get("total_queries", 0)
        
        return patterns
    
    def analyze_api_performance(self) -> Dict[str, Any]:
        """Analyze API endpoint performance."""
        logger.info("Analyzing API performance...")
        
        # Import monitoring service to get metrics
        try:
            from app.services.monitoring_service import monitoring_service
            
            metrics = monitoring_service.get_performance_metrics()
            
            return {
                "response_times": metrics.get("response_times", {}),
                "error_rates": metrics.get("error_rates", {}),
                "throughput": metrics.get("throughput", {}),
                "slow_endpoints": [
                    endpoint for endpoint, time in metrics.get("response_times", {}).items()
                    if time > 2.0  # Endpoints slower than 2 seconds
                ]
            }
            
        except Exception as e:
            logger.warning(f"Could not get API performance metrics: {e}")
            return {"error": "API metrics not available"}
    
    def analyze_system_resources(self) -> Dict[str, Any]:
        """Analyze system resource usage."""
        logger.info("Analyzing system resources...")
        
        return {
            "cpu": {
                "usage_percent": psutil.cpu_percent(interval=1),
                "count": psutil.cpu_count(),
                "load_average": os.getloadavg() if hasattr(os, 'getloadavg') else None
            },
            "memory": {
                "total": psutil.virtual_memory().total,
                "available": psutil.virtual_memory().available,
                "percent": psutil.virtual_memory().percent,
                "used": psutil.virtual_memory().used
            },
            "disk": {
                "total": psutil.disk_usage('/').total,
                "used": psutil.disk_usage('/').used,
                "free": psutil.disk_usage('/').free,
                "percent": psutil.disk_usage('/').percent
            },
            "network": dict(psutil.net_io_counters()._asdict()) if psutil.net_io_counters() else {}
        }
    
    def test_websocket_performance(self) -> Dict[str, Any]:
        """Test WebSocket connection performance."""
        logger.info("Testing WebSocket performance...")
        
        # This would require a more complex setup with actual WebSocket testing
        # For now, return placeholder data
        return {
            "concurrent_connections": 0,
            "message_throughput": 0,
            "average_latency": 0,
            "connection_errors": 0,
            "status": "not_tested",
            "note": "WebSocket performance testing requires separate test setup"
        }
    
    def generate_optimization_recommendations(self, analysis: Dict[str, Any]) -> List[str]:
        """Generate optimization recommendations based on analysis."""
        recommendations = []
        
        # Database recommendations
        db_analysis = analysis.get("database", {})
        
        # Connection pool recommendations
        pool_info = db_analysis.get("connection_pool", {})
        if pool_info.get("status") == "warning":
            recommendations.append(
                "Consider increasing database connection pool size or optimizing query performance"
            )
        
        # Slow query recommendations
        slow_queries = db_analysis.get("slow_queries", [])
        if slow_queries:
            recommendations.append(
                f"Found {len(slow_queries)} slow queries. Consider optimizing or adding indexes."
            )
        
        # Missing index recommendations
        missing_indexes = db_analysis.get("missing_indexes", [])
        if missing_indexes:
            recommendations.append(
                f"Found {len(missing_indexes)} potential missing indexes. Review and add as needed."
            )
        
        # API performance recommendations
        api_analysis = analysis.get("api", {})
        slow_endpoints = api_analysis.get("slow_endpoints", [])
        if slow_endpoints:
            recommendations.append(
                f"Found {len(slow_endpoints)} slow API endpoints. Consider caching or optimization."
            )
        
        # System resource recommendations
        system_analysis = analysis.get("system", {})
        
        cpu_usage = system_analysis.get("cpu", {}).get("usage_percent", 0)
        if cpu_usage > 80:
            recommendations.append("High CPU usage detected. Consider scaling or optimization.")
        
        memory_usage = system_analysis.get("memory", {}).get("percent", 0)
        if memory_usage > 80:
            recommendations.append("High memory usage detected. Consider increasing memory or optimization.")
        
        disk_usage = system_analysis.get("disk", {}).get("percent", 0)
        if disk_usage > 80:
            recommendations.append("High disk usage detected. Consider cleanup or additional storage.")
        
        return recommendations
    
    def run_full_analysis(self) -> Dict[str, Any]:
        """Run complete performance analysis."""
        logger.info("Starting comprehensive performance analysis...")
        
        analysis = {
            "timestamp": time.time(),
            "database": self.analyze_database_performance(),
            "api": self.analyze_api_performance(),
            "system": self.analyze_system_resources(),
            "websocket": self.test_websocket_performance()
        }
        
        analysis["recommendations"] = self.generate_optimization_recommendations(analysis)
        
        return analysis
    
    def save_analysis_report(self, analysis: Dict[str, Any], filename: str = None):
        """Save analysis report to file."""
        if not filename:
            timestamp = int(time.time())
            filename = f"performance_analysis_{timestamp}.json"
        
        filepath = os.path.join(os.path.dirname(__file__), "..", "reports", filename)
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        
        with open(filepath, 'w') as f:
            json.dump(analysis, f, indent=2, default=str)
        
        logger.info(f"Performance analysis report saved to: {filepath}")
        return filepath


def apply_database_optimizations():
    """Apply recommended database optimizations."""
    logger.info("Applying database optimizations...")
    
    db = next(get_db())
    
    # Common indexes that should exist
    indexes_to_create = [
        "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_messages_user_id ON messages(user_id);",
        "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_messages_conversation_id ON messages(conversation_id);",
        "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_messages_created_at ON messages(created_at);",
        "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_conversations_user_id ON conversations(user_id);",
        "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_conversations_updated_at ON conversations(updated_at);",
        "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_user_projects_user_id ON user_projects(user_id);",
        "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_user_projects_status ON user_projects(status);",
        "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_learning_plans_user_id ON learning_plans(user_id);",
        "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_users_email ON users(email);",
        "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_users_created_at ON users(created_at);"
    ]
    
    for index_sql in indexes_to_create:
        try:
            db.execute(text(index_sql))
            db.commit()
            logger.info(f"Created index: {index_sql.split('idx_')[1].split(' ')[0]}")
        except Exception as e:
            logger.warning(f"Could not create index: {e}")
            db.rollback()
    
    # Update table statistics
    try:
        db.execute(text("ANALYZE;"))
        db.commit()
        logger.info("Updated table statistics")
    except Exception as e:
        logger.warning(f"Could not update statistics: {e}")
    
    db.close()


def main():
    """Main function to run performance analysis."""
    optimizer = PerformanceOptimizer()
    
    # Run analysis
    analysis = optimizer.run_full_analysis()
    
    # Save report
    report_path = optimizer.save_analysis_report(analysis)
    
    # Print summary
    print("\n" + "="*60)
    print("PERFORMANCE ANALYSIS SUMMARY")
    print("="*60)
    
    # Database summary
    db_analysis = analysis.get("database", {})
    pool_info = db_analysis.get("connection_pool", {})
    print(f"Database Connection Pool: {pool_info.get('status', 'unknown')}")
    print(f"  - Pool Size: {pool_info.get('pool_size', 0)}")
    print(f"  - Checked Out: {pool_info.get('checked_out', 0)}")
    
    slow_queries = db_analysis.get("slow_queries", [])
    print(f"Slow Queries: {len(slow_queries)} found")
    
    missing_indexes = db_analysis.get("missing_indexes", [])
    print(f"Missing Indexes: {len(missing_indexes)} potential")
    
    # System summary
    system_analysis = analysis.get("system", {})
    cpu_usage = system_analysis.get("cpu", {}).get("usage_percent", 0)
    memory_usage = system_analysis.get("memory", {}).get("percent", 0)
    disk_usage = system_analysis.get("disk", {}).get("percent", 0)
    
    print(f"System Resources:")
    print(f"  - CPU Usage: {cpu_usage:.1f}%")
    print(f"  - Memory Usage: {memory_usage:.1f}%")
    print(f"  - Disk Usage: {disk_usage:.1f}%")
    
    # Recommendations
    recommendations = analysis.get("recommendations", [])
    print(f"\nRecommendations ({len(recommendations)}):")
    for i, rec in enumerate(recommendations, 1):
        print(f"  {i}. {rec}")
    
    print(f"\nFull report saved to: {report_path}")
    
    # Ask if user wants to apply optimizations
    if input("\nApply database optimizations? (y/N): ").lower() == 'y':
        apply_database_optimizations()
        print("Database optimizations applied.")


if __name__ == "__main__":
    main()