"""
Enhanced Database Performance Monitoring Service
Provides detailed query analysis, connection pool monitoring, and database health metrics.
"""

import logging
import time
import asyncio
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timezone, timedelta
from collections import defaultdict, deque
from contextlib import contextmanager
from sqlalchemy import text, event
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import Pool

from ..database import get_db, engine
from ..models.analytics import SystemMetric

logger = logging.getLogger(__name__)

class ConnectionPoolMonitor:
    """Monitor database connection pool health and performance"""
    
    def __init__(self):
        self.pool_stats = {
            'connections_created': 0,
            'connections_closed': 0,
            'connections_checked_out': 0,
            'connections_checked_in': 0,
            'pool_overflows': 0,
            'pool_invalidated': 0
        }
        self.connection_times = deque(maxlen=1000)  # Track connection acquisition times
        
    def setup_pool_monitoring(self, engine: Engine):
        """Set up connection pool event listeners"""
        pool = engine.pool
        
        @event.listens_for(pool, "connect")
        def on_connect(dbapi_conn, connection_record):
            self.pool_stats['connections_created'] += 1
            logger.debug("Database connection created")
        
        @event.listens_for(pool, "checkout")
        def on_checkout(dbapi_conn, connection_record, connection_proxy):
            start_time = time.time()
            connection_record.info['checkout_time'] = start_time
            self.pool_stats['connections_checked_out'] += 1
        
        @event.listens_for(pool, "checkin")
        def on_checkin(dbapi_conn, connection_record):
            if 'checkout_time' in connection_record.info:
                checkout_time = connection_record.info['checkout_time']
                duration = time.time() - checkout_time
                self.connection_times.append(duration)
                del connection_record.info['checkout_time']
            self.pool_stats['connections_checked_in'] += 1
        
        @event.listens_for(pool, "close")
        def on_close(dbapi_conn, connection_record):
            self.pool_stats['connections_closed'] += 1
        
        @event.listens_for(pool, "invalidate")
        def on_invalidate(dbapi_conn, connection_record, exception):
            self.pool_stats['pool_invalidated'] += 1
            logger.warning(f"Database connection invalidated: {exception}")
    
    def get_pool_status(self) -> Dict[str, Any]:
        """Get current connection pool status"""
        pool = engine.pool
        
        # Calculate connection time statistics
        conn_times = list(self.connection_times)
        avg_conn_time = sum(conn_times) / len(conn_times) if conn_times else 0
        max_conn_time = max(conn_times) if conn_times else 0
        
        # Get invalid connections count (some pool types don't have this method)
        try:
            invalid_connections = pool.invalid()
        except AttributeError:
            invalid_connections = 0
        
        return {
            'pool_size': pool.size(),
            'checked_in_connections': pool.checkedin(),
            'checked_out_connections': pool.checkedout(),
            'overflow_connections': pool.overflow(),
            'invalid_connections': invalid_connections,
            'total_connections': pool.size() + pool.overflow(),
            'pool_stats': self.pool_stats.copy(),
            'connection_times': {
                'avg_acquisition_time': avg_conn_time,
                'max_acquisition_time': max_conn_time,
                'recent_samples': len(conn_times)
            }
        }

class QueryAnalyzer:
    """Analyze database queries for performance issues"""
    
    def __init__(self):
        self.slow_queries = deque(maxlen=100)
        self.query_patterns = defaultdict(list)
        self.table_access_patterns = defaultdict(int)
        self.lock_waits = []
        
    def analyze_query(self, query: str, duration: float, params: Optional[Dict] = None) -> Dict[str, Any]:
        """Analyze a single query for performance characteristics"""
        analysis = {
            'query': query,
            'duration': duration,
            'timestamp': datetime.now(timezone.utc),
            'issues': [],
            'recommendations': []
        }
        
        # Normalize query for pattern matching
        normalized_query = self._normalize_query(query)
        analysis['normalized_query'] = normalized_query
        
        # Check for common performance issues
        if duration > 1.0:  # Slow query threshold
            analysis['issues'].append('slow_execution')
            self.slow_queries.append(analysis)
        
        if 'SELECT *' in query.upper():
            analysis['issues'].append('select_star')
            analysis['recommendations'].append('Use specific column names instead of SELECT *')
        
        if 'ORDER BY' in query.upper() and 'LIMIT' not in query.upper():
            analysis['issues'].append('unbounded_sort')
            analysis['recommendations'].append('Consider adding LIMIT to ORDER BY queries')
        
        if query.upper().count('JOIN') > 3:
            analysis['issues'].append('complex_joins')
            analysis['recommendations'].append('Consider breaking down complex joins')
        
        if 'WHERE' not in query.upper() and any(op in query.upper() for op in ['UPDATE', 'DELETE']):
            analysis['issues'].append('unsafe_modification')
            analysis['recommendations'].append('Add WHERE clause to UPDATE/DELETE statements')
        
        # Track table access patterns
        tables = self._extract_table_names(query)
        for table in tables:
            self.table_access_patterns[table] += 1
        
        # Store query pattern
        self.query_patterns[normalized_query].append(analysis)
        
        return analysis
    
    def _normalize_query(self, query: str) -> str:
        """Normalize query for pattern matching"""
        import re
        
        # Remove extra whitespace
        normalized = re.sub(r'\s+', ' ', query.strip())
        
        # Replace literal values with placeholders
        normalized = re.sub(r"'[^']*'", "'?'", normalized)  # String literals
        normalized = re.sub(r'\b\d+\b', '?', normalized)    # Numeric literals
        
        return normalized.upper()
    
    def _extract_table_names(self, query: str) -> List[str]:
        """Extract table names from SQL query"""
        import re
        
        # Simple regex to find table names (this could be more sophisticated)
        patterns = [
            r'FROM\s+(\w+)',
            r'JOIN\s+(\w+)',
            r'UPDATE\s+(\w+)',
            r'INSERT\s+INTO\s+(\w+)',
            r'DELETE\s+FROM\s+(\w+)'
        ]
        
        tables = set()
        for pattern in patterns:
            matches = re.findall(pattern, query.upper())
            tables.update(matches)
        
        return list(tables)
    
    def get_query_recommendations(self) -> List[Dict[str, Any]]:
        """Get recommendations based on query analysis"""
        recommendations = []
        
        # Analyze slow queries
        if len(self.slow_queries) > 0:
            slow_query_patterns = defaultdict(int)
            for query_info in self.slow_queries:
                slow_query_patterns[query_info['normalized_query']] += 1
            
            for pattern, count in slow_query_patterns.items():
                if count > 1:
                    recommendations.append({
                        'type': 'slow_query_pattern',
                        'priority': 'high',
                        'title': f'Repeated slow query pattern ({count} occurrences)',
                        'description': f'Query pattern: {pattern[:100]}...',
                        'recommendation': 'Consider adding indexes or optimizing this query pattern'
                    })
        
        # Analyze table access patterns
        most_accessed_tables = sorted(
            self.table_access_patterns.items(), 
            key=lambda x: x[1], 
            reverse=True
        )[:5]
        
        for table, access_count in most_accessed_tables:
            if access_count > 100:  # High access threshold
                recommendations.append({
                    'type': 'high_table_access',
                    'priority': 'medium',
                    'title': f'High access frequency for table: {table}',
                    'description': f'Table accessed {access_count} times recently',
                    'recommendation': f'Consider optimizing indexes for table {table}'
                })
        
        return recommendations

class DatabaseHealthMonitor:
    """Monitor overall database health and performance"""
    
    def __init__(self):
        self.connection_monitor = ConnectionPoolMonitor()
        self.query_analyzer = QueryAnalyzer()
        self.health_history = deque(maxlen=100)
        
    def initialize(self, db_engine: Engine):
        """Initialize database monitoring"""
        self.connection_monitor.setup_pool_monitoring(db_engine)
        logger.info("Enhanced database monitoring initialized")
    
    async def check_database_health(self) -> Dict[str, Any]:
        """Comprehensive database health check"""
        health_info = {
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'overall_status': 'healthy',
            'checks': {}
        }
        
        try:
            # Basic connectivity check
            start_time = time.time()
            db = next(get_db())
            
            # Test basic query
            result = db.execute(text("SELECT 1 as test")).fetchone()
            basic_query_time = time.time() - start_time
            
            if not result or result[0] != 1:
                health_info['overall_status'] = 'unhealthy'
                health_info['checks']['basic_connectivity'] = {
                    'status': 'failed',
                    'error': 'Basic query returned unexpected result'
                }
            else:
                health_info['checks']['basic_connectivity'] = {
                    'status': 'healthy',
                    'response_time': basic_query_time
                }
            
            # Check database statistics
            db_stats = await self._get_database_statistics(db)
            health_info['checks']['database_stats'] = db_stats
            
            # Check connection pool health
            pool_status = self.connection_monitor.get_pool_status()
            health_info['checks']['connection_pool'] = pool_status
            
            # Check for long-running queries
            long_running = await self._check_long_running_queries(db)
            health_info['checks']['long_running_queries'] = long_running
            
            # Check database locks
            locks_info = await self._check_database_locks(db)
            health_info['checks']['database_locks'] = locks_info
            
            # Overall health assessment
            if any(check.get('status') == 'unhealthy' for check in health_info['checks'].values()):
                health_info['overall_status'] = 'unhealthy'
            elif any(check.get('status') == 'warning' for check in health_info['checks'].values()):
                health_info['overall_status'] = 'warning'
            
            db.close()
            
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            health_info['overall_status'] = 'unhealthy'
            health_info['error'] = str(e)
        
        # Store health history
        self.health_history.append(health_info)
        
        return health_info
    
    async def _get_database_statistics(self, db: Session) -> Dict[str, Any]:
        """Get database statistics"""
        try:
            # Get connection statistics
            conn_stats = db.execute(text("""
                SELECT 
                    count(*) as total_connections,
                    sum(case when state = 'active' then 1 else 0 end) as active_connections,
                    sum(case when state = 'idle' then 1 else 0 end) as idle_connections
                FROM pg_stat_activity 
                WHERE datname = current_database()
            """)).fetchone()
            
            # Get database size
            db_size = db.execute(text("""
                SELECT pg_size_pretty(pg_database_size(current_database())) as size
            """)).fetchone()
            
            # Get table statistics
            table_stats = db.execute(text("""
                SELECT 
                    schemaname,
                    relname as tablename,
                    n_tup_ins as inserts,
                    n_tup_upd as updates,
                    n_tup_del as deletes,
                    n_live_tup as live_tuples,
                    n_dead_tup as dead_tuples
                FROM pg_stat_user_tables 
                ORDER BY n_live_tup DESC 
                LIMIT 10
            """)).fetchall()
            
            return {
                'status': 'healthy',
                'connections': {
                    'total': conn_stats[0] if conn_stats else 0,
                    'active': conn_stats[1] if conn_stats else 0,
                    'idle': conn_stats[2] if conn_stats else 0
                },
                'database_size': db_size[0] if db_size else 'unknown',
                'top_tables': [
                    {
                        'schema': row[0],
                        'table': row[1],
                        'inserts': row[2],
                        'updates': row[3],
                        'deletes': row[4],
                        'live_tuples': row[5],
                        'dead_tuples': row[6]
                    }
                    for row in table_stats
                ]
            }
            
        except Exception as e:
            logger.error(f"Failed to get database statistics: {e}")
            return {
                'status': 'error',
                'error': str(e)
            }
    
    async def _check_long_running_queries(self, db: Session) -> Dict[str, Any]:
        """Check for long-running queries"""
        try:
            long_queries = db.execute(text("""
                SELECT 
                    pid,
                    now() - pg_stat_activity.query_start AS duration,
                    query,
                    state
                FROM pg_stat_activity 
                WHERE (now() - pg_stat_activity.query_start) > interval '30 seconds'
                AND state = 'active'
                AND query NOT LIKE '%pg_stat_activity%'
                ORDER BY duration DESC
                LIMIT 10
            """)).fetchall()
            
            long_query_list = []
            for query in long_queries:
                long_query_list.append({
                    'pid': query[0],
                    'duration': str(query[1]),
                    'query': query[2][:200] + '...' if len(query[2]) > 200 else query[2],
                    'state': query[3]
                })
            
            status = 'healthy'
            if len(long_query_list) > 5:
                status = 'warning'
            elif len(long_query_list) > 10:
                status = 'unhealthy'
            
            return {
                'status': status,
                'long_running_count': len(long_query_list),
                'queries': long_query_list
            }
            
        except Exception as e:
            logger.error(f"Failed to check long-running queries: {e}")
            return {
                'status': 'error',
                'error': str(e)
            }
    
    async def _check_database_locks(self, db: Session) -> Dict[str, Any]:
        """Check for database locks"""
        try:
            locks = db.execute(text("""
                SELECT 
                    l.locktype,
                    l.mode,
                    l.granted,
                    a.query,
                    a.pid
                FROM pg_locks l
                JOIN pg_stat_activity a ON l.pid = a.pid
                WHERE NOT l.granted
                ORDER BY l.pid
                LIMIT 10
            """)).fetchall()
            
            lock_list = []
            for lock in locks:
                lock_list.append({
                    'locktype': lock[0],
                    'mode': lock[1],
                    'granted': lock[2],
                    'query': lock[3][:200] + '...' if len(lock[3]) > 200 else lock[3],
                    'pid': lock[4]
                })
            
            status = 'healthy'
            if len(lock_list) > 0:
                status = 'warning'
            if len(lock_list) > 5:
                status = 'unhealthy'
            
            return {
                'status': status,
                'blocked_queries': len(lock_list),
                'locks': lock_list
            }
            
        except Exception as e:
            logger.error(f"Failed to check database locks: {e}")
            return {
                'status': 'error',
                'error': str(e)
            }
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """Get comprehensive database performance summary"""
        return {
            'connection_pool': self.connection_monitor.get_pool_status(),
            'query_analysis': {
                'slow_queries_count': len(self.query_analyzer.slow_queries),
                'table_access_patterns': dict(self.query_analyzer.table_access_patterns),
                'recommendations': self.query_analyzer.get_query_recommendations()
            },
            'health_trend': {
                'recent_checks': len(self.health_history),
                'healthy_percentage': sum(1 for h in self.health_history if h['overall_status'] == 'healthy') / len(self.health_history) * 100 if self.health_history else 0
            }
        }

# Global enhanced database monitoring instance
enhanced_db_monitor = DatabaseHealthMonitor()

def initialize_enhanced_db_monitoring():
    """Initialize enhanced database monitoring"""
    enhanced_db_monitor.initialize(engine)
    logger.info("Enhanced database monitoring initialized")

def get_enhanced_db_monitor() -> DatabaseHealthMonitor:
    """Get the enhanced database monitoring instance"""
    return enhanced_db_monitor