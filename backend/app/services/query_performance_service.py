"""
Query Performance Monitoring Service

This service monitors database query performance and identifies slow operations
to help optimize database queries and prevent N+1 query problems.
"""

import time
import logging
from typing import Dict, List, Any, Optional, Callable
from contextlib import contextmanager
from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from collections import defaultdict, deque
import threading
from sqlalchemy import event
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session
import statistics

logger = logging.getLogger(__name__)

@dataclass
class QueryMetrics:
    """Metrics for a database query."""
    query: str
    duration: float
    timestamp: datetime
    table_names: List[str] = field(default_factory=list)
    operation_type: str = "SELECT"
    row_count: Optional[int] = None
    parameters: Optional[Dict] = None

@dataclass
class QueryStats:
    """Aggregated statistics for a query pattern."""
    query_pattern: str
    count: int = 0
    total_duration: float = 0.0
    min_duration: float = float('inf')
    max_duration: float = 0.0
    avg_duration: float = 0.0
    recent_durations: deque = field(default_factory=lambda: deque(maxlen=100))
    slow_query_count: int = 0
    table_names: set = field(default_factory=set)

class QueryPerformanceService:
    """Service for monitoring and analyzing database query performance."""
    
    def __init__(self, slow_query_threshold: float = 0.1):
        """
        Initialize query performance monitoring.
        
        Args:
            slow_query_threshold: Threshold in seconds for considering a query slow
        """
        self.slow_query_threshold = slow_query_threshold
        self.query_metrics: List[QueryMetrics] = []
        self.query_stats: Dict[str, QueryStats] = defaultdict(QueryStats)
        self.n_plus_one_detector = NPlusOneDetector()
        self._lock = threading.Lock()
        self._monitoring_enabled = True
        
        # Keep only recent metrics to prevent memory bloat
        self.max_metrics_history = 10000
        
    def enable_monitoring(self):
        """Enable query performance monitoring."""
        self._monitoring_enabled = True
        logger.info("Query performance monitoring enabled")
        
    def disable_monitoring(self):
        """Disable query performance monitoring."""
        self._monitoring_enabled = False
        logger.info("Query performance monitoring disabled")
        
    def setup_sqlalchemy_monitoring(self, engine: Engine):
        """Set up SQLAlchemy event listeners for automatic query monitoring."""
        
        @event.listens_for(engine, "before_cursor_execute")
        def receive_before_cursor_execute(conn, cursor, statement, parameters, context, executemany):
            if self._monitoring_enabled:
                context._query_start_time = time.time()
                context._query_statement = statement
                context._query_parameters = parameters
                
        @event.listens_for(engine, "after_cursor_execute")
        def receive_after_cursor_execute(conn, cursor, statement, parameters, context, executemany):
            if self._monitoring_enabled and hasattr(context, '_query_start_time'):
                duration = time.time() - context._query_start_time
                
                # Extract table names from query
                table_names = self._extract_table_names(statement)
                
                # Determine operation type
                operation_type = self._get_operation_type(statement)
                
                # Record the query
                self.record_query(
                    query=statement,
                    duration=duration,
                    table_names=table_names,
                    operation_type=operation_type,
                    parameters=parameters,
                    row_count=cursor.rowcount if hasattr(cursor, 'rowcount') else None
                )
    
    def record_query(
        self,
        query: str,
        duration: float,
        table_names: List[str] = None,
        operation_type: str = "SELECT",
        parameters: Dict = None,
        row_count: int = None
    ):
        """Record a database query for performance analysis."""
        if not self._monitoring_enabled:
            return
            
        with self._lock:
            # Create query metrics
            metrics = QueryMetrics(
                query=query,
                duration=duration,
                timestamp=datetime.now(timezone.utc),
                table_names=table_names or [],
                operation_type=operation_type,
                row_count=row_count,
                parameters=parameters
            )
            
            # Add to metrics history
            self.query_metrics.append(metrics)
            
            # Trim history if too large
            if len(self.query_metrics) > self.max_metrics_history:
                self.query_metrics = self.query_metrics[-self.max_metrics_history//2:]
            
            # Update aggregated stats
            query_pattern = self._normalize_query(query)
            if query_pattern not in self.query_stats:
                self.query_stats[query_pattern] = QueryStats(query_pattern=query_pattern)
            
            stats = self.query_stats[query_pattern]
                
            stats.count += 1
            stats.total_duration += duration
            stats.min_duration = min(stats.min_duration, duration)
            stats.max_duration = max(stats.max_duration, duration)
            stats.avg_duration = stats.total_duration / stats.count
            stats.recent_durations.append(duration)
            stats.table_names.update(table_names or [])
            
            if duration > self.slow_query_threshold:
                stats.slow_query_count += 1
                logger.warning(f"Slow query detected ({duration:.3f}s): {query[:200]}...")
            
            # Check for N+1 queries
            self.n_plus_one_detector.check_query(metrics)
    
    @contextmanager
    def monitor_query(self, query_name: str):
        """Context manager for monitoring a specific query or operation."""
        start_time = time.time()
        try:
            yield
        finally:
            duration = time.time() - start_time
            self.record_query(
                query=f"MANUAL_MONITOR: {query_name}",
                duration=duration,
                operation_type="MANUAL"
            )
    
    def get_slow_queries(self, limit: int = 10) -> List[QueryStats]:
        """Get the slowest queries by average duration."""
        with self._lock:
            sorted_stats = sorted(
                self.query_stats.values(),
                key=lambda s: s.avg_duration,
                reverse=True
            )
            return sorted_stats[:limit]
    
    def get_frequent_queries(self, limit: int = 10) -> List[QueryStats]:
        """Get the most frequently executed queries."""
        with self._lock:
            sorted_stats = sorted(
                self.query_stats.values(),
                key=lambda s: s.count,
                reverse=True
            )
            return sorted_stats[:limit]
    
    def get_n_plus_one_issues(self) -> List[Dict[str, Any]]:
        """Get detected N+1 query issues."""
        return self.n_plus_one_detector.get_issues()
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """Get a comprehensive performance summary with enhanced metrics."""
        with self._lock:
            if not self.query_metrics:
                return {"message": "No query metrics available"}
            
            now = datetime.now(timezone.utc)
            recent_queries_1h = [m for m in self.query_metrics 
                               if m.timestamp > now - timedelta(hours=1)]
            recent_queries_24h = [m for m in self.query_metrics 
                                if m.timestamp > now - timedelta(hours=24)]
            
            total_queries = len(self.query_metrics)
            slow_queries = [m for m in self.query_metrics if m.duration > self.slow_query_threshold]
            very_slow_queries = [m for m in self.query_metrics if m.duration > self.slow_query_threshold * 5]
            
            durations = [m.duration for m in self.query_metrics]
            recent_durations_1h = [m.duration for m in recent_queries_1h]
            
            # Calculate query patterns by operation type
            operation_stats = {}
            for metric in self.query_metrics:
                op_type = metric.operation_type
                if op_type not in operation_stats:
                    operation_stats[op_type] = {'count': 0, 'total_duration': 0, 'slow_count': 0}
                operation_stats[op_type]['count'] += 1
                operation_stats[op_type]['total_duration'] += metric.duration
                if metric.duration > self.slow_query_threshold:
                    operation_stats[op_type]['slow_count'] += 1
            
            # Calculate average duration by operation type
            for op_type, stats in operation_stats.items():
                stats['avg_duration'] = stats['total_duration'] / stats['count'] if stats['count'] > 0 else 0
                stats['slow_percentage'] = (stats['slow_count'] / stats['count'] * 100) if stats['count'] > 0 else 0
            
            return {
                "total_queries": total_queries,
                "recent_queries_1h": len(recent_queries_1h),
                "recent_queries_24h": len(recent_queries_24h),
                "slow_queries": len(slow_queries),
                "very_slow_queries": len(very_slow_queries),
                "slow_query_percentage": (len(slow_queries) / total_queries * 100) if total_queries > 0 else 0,
                "very_slow_query_percentage": (len(very_slow_queries) / total_queries * 100) if total_queries > 0 else 0,
                "avg_query_duration": statistics.mean(durations) if durations else 0,
                "median_query_duration": statistics.median(durations) if durations else 0,
                "p95_query_duration": self._percentile(durations, 95) if durations else 0,
                "p99_query_duration": self._percentile(durations, 99) if durations else 0,
                "recent_avg_duration_1h": statistics.mean(recent_durations_1h) if recent_durations_1h else 0,
                "unique_query_patterns": len(self.query_stats),
                "n_plus_one_issues": len(self.get_n_plus_one_issues()),
                "most_frequent_tables": self._get_most_frequent_tables(),
                "operation_stats": operation_stats,
                "monitoring_enabled": self._monitoring_enabled,
                "slow_query_threshold": self.slow_query_threshold,
                "performance_trend": self._calculate_performance_trend()
            }
    
    def get_table_performance(self, table_name: str) -> Dict[str, Any]:
        """Get performance metrics for a specific table."""
        with self._lock:
            table_queries = [m for m in self.query_metrics if table_name in m.table_names]
            
            if not table_queries:
                return {"message": f"No queries found for table {table_name}"}
            
            durations = [q.duration for q in table_queries]
            operations = defaultdict(int)
            for q in table_queries:
                operations[q.operation_type] += 1
            
            return {
                "table_name": table_name,
                "total_queries": len(table_queries),
                "avg_duration": statistics.mean(durations),
                "median_duration": statistics.median(durations),
                "max_duration": max(durations),
                "operations": dict(operations),
                "slow_queries": len([q for q in table_queries if q.duration > self.slow_query_threshold])
            }
    
    def reset_metrics(self):
        """Reset all collected metrics."""
        with self._lock:
            self.query_metrics.clear()
            self.query_stats.clear()
            self.n_plus_one_detector.reset()
            logger.info("Query performance metrics reset")
    
    def _normalize_query(self, query: str) -> str:
        """Normalize a query to create a pattern for grouping similar queries."""
        import re
        
        # Remove extra whitespace
        normalized = re.sub(r'\s+', ' ', query.strip())
        
        # Replace parameter placeholders
        normalized = re.sub(r'\$\d+', '?', normalized)  # PostgreSQL style
        normalized = re.sub(r'%\([^)]+\)s', '?', normalized)  # Python style
        normalized = re.sub(r"'[^']*'", '?', normalized)  # String literals
        normalized = re.sub(r'\b\d+\b', '?', normalized)  # Numbers
        
        # Limit length
        if len(normalized) > 200:
            normalized = normalized[:200] + "..."
        
        return normalized
    
    def _extract_table_names(self, query: str) -> List[str]:
        """Extract table names from a SQL query."""
        import re
        
        # Simple regex to find table names after FROM, JOIN, UPDATE, INSERT INTO, DELETE FROM
        patterns = [
            r'\bFROM\s+([a-zA-Z_][a-zA-Z0-9_]*)',
            r'\bJOIN\s+([a-zA-Z_][a-zA-Z0-9_]*)',
            r'\bUPDATE\s+([a-zA-Z_][a-zA-Z0-9_]*)',
            r'\bINSERT\s+INTO\s+([a-zA-Z_][a-zA-Z0-9_]*)',
            r'\bDELETE\s+FROM\s+([a-zA-Z_][a-zA-Z0-9_]*)'
        ]
        
        table_names = set()
        query_upper = query.upper()
        
        for pattern in patterns:
            matches = re.findall(pattern, query_upper)
            table_names.update(matches)
        
        return list(table_names)
    
    def _get_operation_type(self, query: str) -> str:
        """Determine the operation type from a SQL query."""
        query_upper = query.strip().upper()
        
        if query_upper.startswith('SELECT'):
            return 'SELECT'
        elif query_upper.startswith('INSERT'):
            return 'INSERT'
        elif query_upper.startswith('UPDATE'):
            return 'UPDATE'
        elif query_upper.startswith('DELETE'):
            return 'DELETE'
        elif query_upper.startswith('CREATE'):
            return 'CREATE'
        elif query_upper.startswith('DROP'):
            return 'DROP'
        elif query_upper.startswith('ALTER'):
            return 'ALTER'
        else:
            return 'OTHER'
    
    def _get_most_frequent_tables(self, limit: int = 5) -> List[Dict[str, Any]]:
        """Get the most frequently queried tables."""
        table_counts = defaultdict(int)
        
        for metrics in self.query_metrics:
            for table in metrics.table_names:
                table_counts[table] += 1
        
        sorted_tables = sorted(table_counts.items(), key=lambda x: x[1], reverse=True)
        
        return [{"table": table, "query_count": count} for table, count in sorted_tables[:limit]]
    
    def _percentile(self, data: List[float], percentile: int) -> float:
        """Calculate percentile of a list of numbers."""
        if not data:
            return 0.0
        
        sorted_data = sorted(data)
        index = (percentile / 100) * (len(sorted_data) - 1)
        
        if index.is_integer():
            return sorted_data[int(index)]
        else:
            lower = sorted_data[int(index)]
            upper = sorted_data[int(index) + 1]
            return lower + (upper - lower) * (index - int(index))
    
    def _calculate_performance_trend(self) -> Dict[str, Any]:
        """Calculate performance trend over time."""
        if len(self.query_metrics) < 10:
            return {"trend": "insufficient_data", "message": "Not enough data for trend analysis"}
        
        now = datetime.now(timezone.utc)
        
        # Split metrics into time buckets
        recent_1h = [m for m in self.query_metrics if m.timestamp > now - timedelta(hours=1)]
        recent_6h = [m for m in self.query_metrics if m.timestamp > now - timedelta(hours=6)]
        recent_24h = [m for m in self.query_metrics if m.timestamp > now - timedelta(hours=24)]
        
        if not recent_1h or not recent_6h:
            return {"trend": "insufficient_recent_data"}
        
        # Calculate average durations for each period
        avg_1h = statistics.mean([m.duration for m in recent_1h])
        avg_6h = statistics.mean([m.duration for m in recent_6h])
        avg_24h = statistics.mean([m.duration for m in recent_24h]) if recent_24h else avg_6h
        
        # Calculate trend
        if avg_1h > avg_6h * 1.2:
            trend = "degrading"
        elif avg_1h < avg_6h * 0.8:
            trend = "improving"
        else:
            trend = "stable"
        
        return {
            "trend": trend,
            "avg_duration_1h": avg_1h,
            "avg_duration_6h": avg_6h,
            "avg_duration_24h": avg_24h,
            "query_count_1h": len(recent_1h),
            "query_count_6h": len(recent_6h),
            "query_count_24h": len(recent_24h)
        }

class NPlusOneDetector:
    """Detector for N+1 query problems."""
    
    def __init__(self, detection_window: int = 60, threshold: int = 10):
        """
        Initialize N+1 query detector.
        
        Args:
            detection_window: Time window in seconds to look for patterns
            threshold: Minimum number of similar queries to consider N+1
        """
        self.detection_window = detection_window
        self.threshold = threshold
        self.recent_queries: deque = deque(maxlen=1000)
        self.issues: List[Dict[str, Any]] = []
        
    def check_query(self, metrics: QueryMetrics):
        """Check if a query might be part of an N+1 pattern."""
        self.recent_queries.append(metrics)
        
        # Only check SELECT queries
        if metrics.operation_type != 'SELECT':
            return
        
        # Look for patterns in recent queries
        cutoff_time = datetime.now(timezone.utc) - timedelta(seconds=self.detection_window)
        recent = [q for q in self.recent_queries if q.timestamp > cutoff_time]
        
        # Group by normalized query pattern
        query_groups = defaultdict(list)
        for query in recent:
            pattern = self._normalize_for_n_plus_one(query.query)
            query_groups[pattern].append(query)
        
        # Check for N+1 patterns
        for pattern, queries in query_groups.items():
            if len(queries) >= self.threshold:
                # Check if queries are happening in quick succession
                timestamps = [q.timestamp for q in queries]
                time_span = (max(timestamps) - min(timestamps)).total_seconds()
                
                if time_span < self.detection_window:
                    self._record_n_plus_one_issue(pattern, queries)
    
    def _normalize_for_n_plus_one(self, query: str) -> str:
        """Normalize query specifically for N+1 detection."""
        import re
        
        # Focus on the structure, not the specific values
        normalized = re.sub(r'\s+', ' ', query.strip().upper())
        
        # Replace specific IDs and values with placeholders
        normalized = re.sub(r'\bWHERE\s+\w+\s*=\s*[^)\s]+', 'WHERE col = ?', normalized)
        normalized = re.sub(r'\bIN\s*\([^)]+\)', 'IN (?)', normalized)
        
        return normalized
    
    def _record_n_plus_one_issue(self, pattern: str, queries: List[QueryMetrics]):
        """Record a detected N+1 issue."""
        # Check if we already recorded this issue recently
        recent_issues = [i for i in self.issues 
                        if i['timestamp'] > datetime.now(timezone.utc) - timedelta(minutes=5)]
        
        if any(i['pattern'] == pattern for i in recent_issues):
            return  # Already recorded recently
        
        issue = {
            "pattern": pattern,
            "query_count": len(queries),
            "timestamp": datetime.now(timezone.utc),
            "duration_total": sum(q.duration for q in queries),
            "duration_avg": sum(q.duration for q in queries) / len(queries),
            "table_names": list(set().union(*[q.table_names for q in queries])),
            "sample_query": queries[0].query[:500]
        }
        
        self.issues.append(issue)
        
        # Keep only recent issues
        self.issues = [i for i in self.issues 
                      if i['timestamp'] > datetime.now(timezone.utc) - timedelta(hours=24)]
        
        logger.warning(f"N+1 query detected: {len(queries)} similar queries in pattern: {pattern[:100]}")
    
    def get_issues(self) -> List[Dict[str, Any]]:
        """Get all detected N+1 issues."""
        return self.issues.copy()
    
    def reset(self):
        """Reset the detector state."""
        self.recent_queries.clear()
        self.issues.clear()

# Global instance for easy access
query_performance_monitor = QueryPerformanceService()