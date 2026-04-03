"""
Resource optimization service for monitoring and optimizing application resource usage.
"""

import asyncio
import logging
import psutil
import gc
import threading
import time
from typing import Dict, List, Optional, Callable
from dataclasses import dataclass
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor
import weakref

logger = logging.getLogger(__name__)

@dataclass
class ResourceMetrics:
    """Resource usage metrics"""
    timestamp: datetime
    memory_rss: int  # Resident Set Size in bytes
    memory_vms: int  # Virtual Memory Size in bytes
    cpu_percent: float
    open_files: int
    threads: int
    connections: int = 0
    cache_size: int = 0

class ResourceOptimizationService:
    """Service for monitoring and optimizing application resource usage"""
    
    def __init__(self):
        self.metrics_history: List[ResourceMetrics] = []
        self.max_history_size = 1000
        self.monitoring_active = False
        self.optimization_callbacks: List[Callable] = []
        self.memory_threshold = 500 * 1024 * 1024  # 500MB
        self.cpu_threshold = 80.0  # 80%
        self.cleanup_interval = 300  # 5 minutes
        self._cleanup_task: Optional[asyncio.Task] = None
        self._monitoring_task: Optional[asyncio.Task] = None
        
    async def start_monitoring(self, interval: int = 60):
        """Start resource monitoring"""
        if self.monitoring_active:
            return
            
        self.monitoring_active = True
        self._monitoring_task = asyncio.create_task(self._monitoring_loop(interval))
        self._cleanup_task = asyncio.create_task(self._cleanup_loop())
        logger.info(f"Resource monitoring started with {interval}s interval")
    
    async def stop_monitoring(self):
        """Stop resource monitoring"""
        self.monitoring_active = False
        
        if self._monitoring_task:
            self._monitoring_task.cancel()
            try:
                await self._monitoring_task
            except asyncio.CancelledError:
                pass
                
        if self._cleanup_task:
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass
                
        logger.info("Resource monitoring stopped")
    
    async def _monitoring_loop(self, interval: int):
        """Main monitoring loop"""
        while self.monitoring_active:
            try:
                metrics = self._collect_metrics()
                self._store_metrics(metrics)
                await self._check_thresholds(metrics)
                await asyncio.sleep(interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in resource monitoring: {e}")
                await asyncio.sleep(interval)
    
    async def _cleanup_loop(self):
        """Periodic cleanup loop"""
        while self.monitoring_active:
            try:
                await asyncio.sleep(self.cleanup_interval)
                await self.optimize_resources()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in cleanup loop: {e}")
    
    def _collect_metrics(self) -> ResourceMetrics:
        """Collect current resource metrics"""
        try:
            process = psutil.Process()
            memory_info = process.memory_info()
            
            # Get database connection count if available
            connections = 0
            try:
                from ..database.database import engine
                connections = engine.pool.size() + engine.pool.overflow()
            except:
                pass
            
            return ResourceMetrics(
                timestamp=datetime.now(),
                memory_rss=memory_info.rss,
                memory_vms=memory_info.vms,
                cpu_percent=process.cpu_percent(),
                open_files=len(process.open_files()),
                threads=process.num_threads(),
                connections=connections
            )
        except Exception as e:
            logger.error(f"Error collecting metrics: {e}")
            return ResourceMetrics(
                timestamp=datetime.now(),
                memory_rss=0,
                memory_vms=0,
                cpu_percent=0.0,
                open_files=0,
                threads=0
            )
    
    def _store_metrics(self, metrics: ResourceMetrics):
        """Store metrics in history"""
        self.metrics_history.append(metrics)
        
        # Trim history if too large
        if len(self.metrics_history) > self.max_history_size:
            self.metrics_history = self.metrics_history[-self.max_history_size:]
    
    async def _check_thresholds(self, metrics: ResourceMetrics):
        """Check if resource usage exceeds thresholds"""
        alerts = []
        
        if metrics.memory_rss > self.memory_threshold:
            alerts.append(f"High memory usage: {metrics.memory_rss / 1024 / 1024:.1f}MB")
            
        if metrics.cpu_percent > self.cpu_threshold:
            alerts.append(f"High CPU usage: {metrics.cpu_percent:.1f}%")
            
        if alerts:
            logger.warning(f"Resource threshold exceeded: {', '.join(alerts)}")
            await self.optimize_resources()
    
    async def optimize_resources(self):
        """Optimize resource usage"""
        logger.info("Starting resource optimization...")
        
        # Force garbage collection
        collected = gc.collect()
        if collected > 0:
            logger.info(f"Garbage collection freed {collected} objects")
        
        # Run optimization callbacks
        for callback in self.optimization_callbacks:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback()
                else:
                    callback()
            except Exception as e:
                logger.error(f"Error in optimization callback: {e}")
        
        # Clear old metrics
        cutoff_time = datetime.now() - timedelta(hours=1)
        self.metrics_history = [
            m for m in self.metrics_history 
            if m.timestamp > cutoff_time
        ]
        
        logger.info("Resource optimization completed")
    
    def add_optimization_callback(self, callback: Callable):
        """Add a callback to run during optimization"""
        self.optimization_callbacks.append(callback)
    
    def get_current_metrics(self) -> ResourceMetrics:
        """Get current resource metrics"""
        return self._collect_metrics()
    
    def get_metrics_summary(self, minutes: int = 60) -> Dict:
        """Get summary of metrics for the last N minutes"""
        cutoff_time = datetime.now() - timedelta(minutes=minutes)
        recent_metrics = [
            m for m in self.metrics_history 
            if m.timestamp > cutoff_time
        ]
        
        if not recent_metrics:
            return {}
        
        return {
            "period_minutes": minutes,
            "sample_count": len(recent_metrics),
            "memory_rss": {
                "current": recent_metrics[-1].memory_rss,
                "avg": sum(m.memory_rss for m in recent_metrics) / len(recent_metrics),
                "max": max(m.memory_rss for m in recent_metrics),
                "min": min(m.memory_rss for m in recent_metrics)
            },
            "cpu_percent": {
                "current": recent_metrics[-1].cpu_percent,
                "avg": sum(m.cpu_percent for m in recent_metrics) / len(recent_metrics),
                "max": max(m.cpu_percent for m in recent_metrics),
                "min": min(m.cpu_percent for m in recent_metrics)
            },
            "connections": {
                "current": recent_metrics[-1].connections,
                "avg": sum(m.connections for m in recent_metrics) / len(recent_metrics),
                "max": max(m.connections for m in recent_metrics)
            },
            "threads": {
                "current": recent_metrics[-1].threads,
                "avg": sum(m.threads for m in recent_metrics) / len(recent_metrics),
                "max": max(m.threads for m in recent_metrics)
            }
        }
    
    def set_memory_threshold(self, threshold_mb: int):
        """Set memory usage threshold in MB"""
        self.memory_threshold = threshold_mb * 1024 * 1024
        logger.info(f"Memory threshold set to {threshold_mb}MB")
    
    def set_cpu_threshold(self, threshold_percent: float):
        """Set CPU usage threshold as percentage"""
        self.cpu_threshold = threshold_percent
        logger.info(f"CPU threshold set to {threshold_percent}%")

class ConnectionPoolOptimizer:
    """Optimizer for database connection pools"""
    
    def __init__(self):
        self.pool_stats = {}
        
    async def optimize_connection_pool(self):
        """Optimize database connection pool"""
        try:
            from ..database.database import engine
            
            # Get pool statistics
            pool = engine.pool
            stats = {
                "size": pool.size(),
                "checked_in": pool.checkedin(),
                "checked_out": pool.checkedout(),
                "overflow": pool.overflow(),
                "invalid": pool.invalid()
            }
            
            self.pool_stats = stats
            
            # Log pool status
            logger.info(f"Connection pool stats: {stats}")
            
            # If we have too many invalid connections, recreate the pool
            if stats["invalid"] > 2:
                logger.warning(f"High number of invalid connections ({stats['invalid']}), optimizing pool")
                pool.dispose()
                
        except Exception as e:
            logger.error(f"Error optimizing connection pool: {e}")
    
    def get_pool_stats(self) -> Dict:
        """Get current pool statistics"""
        return self.pool_stats.copy()

class MemoryOptimizer:
    """Memory usage optimizer"""
    
    def __init__(self):
        self.cache_registries = []
        
    def register_cache(self, cache_clear_func: Callable):
        """Register a cache clearing function"""
        self.cache_registries.append(cache_clear_func)
    
    async def optimize_memory(self):
        """Optimize memory usage"""
        logger.info("Starting memory optimization...")
        
        # Clear registered caches
        for cache_clear in self.cache_registries:
            try:
                if asyncio.iscoroutinefunction(cache_clear):
                    await cache_clear()
                else:
                    cache_clear()
            except Exception as e:
                logger.error(f"Error clearing cache: {e}")
        
        # Force garbage collection multiple times
        for i in range(3):
            collected = gc.collect()
            if collected > 0:
                logger.debug(f"GC round {i+1}: freed {collected} objects")
        
        # Clear weak references
        try:
            import weakref
            weakref.getweakrefs(object)
        except:
            pass
        
        logger.info("Memory optimization completed")

# Global instances
resource_optimizer = ResourceOptimizationService()
connection_optimizer = ConnectionPoolOptimizer()
memory_optimizer = MemoryOptimizer()

# Register optimizers with resource service
resource_optimizer.add_optimization_callback(connection_optimizer.optimize_connection_pool)
resource_optimizer.add_optimization_callback(memory_optimizer.optimize_memory)