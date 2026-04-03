"""
Memory metrics for monitoring memory operations.
"""

from prometheus_client import Counter, Histogram, Gauge
from typing import Dict, Any

class MemoryMetrics:
    """Metrics for monitoring memory operations."""

    def __init__(self):
        # Operation counters
        self.memory_operations_total = Counter(
            'memory_operations_total',
            'Total number of memory operations',
            ['operation', 'status']
        )

        # Latency histogram
        self.memory_operation_duration_seconds = Histogram(
            'memory_operation_duration_seconds',
            'Duration of memory operations in seconds',
            ['operation'],
            buckets=[0.1, 0.5, 1.0, 2.0, 5.0, 10.0]
        )

        # Memory size gauge
        self.memory_size_bytes = Gauge(
            'memory_size_bytes',
            'Current memory size in bytes',
            ['type']
        )

        # Hit/miss counters
        self.memory_hits_total = Counter(
            'memory_hits_total',
            'Total number of successful memory retrievals',
            ['type']
        )

        self.memory_misses_total = Counter(
            'memory_misses_total',
            'Total number of failed memory retrievals',
            ['type']
        )

        # Vector store operations
        self.vector_store_operations_total = Counter(
            'vector_store_operations_total',
            'Total number of vector store operations',
            ['operation', 'status']
        )

    def record_operation(self, operation: str, status: str):
        """Record a memory operation."""
        self.memory_operations_total.labels(operation=operation, status=status).inc()

    def record_latency(self, operation: str, duration: float):
        """Record operation latency."""
        self.memory_operation_duration_seconds.labels(operation=operation).observe(duration)

    def record_size(self, memory_type: str, size: int):
        """Record memory size."""
        self.memory_size_bytes.labels(type=memory_type).set(size)

    def record_hit(self, memory_type: str):
        """Record a memory hit."""
        self.memory_hits_total.labels(type=memory_type).inc()

    def record_miss(self, memory_type: str):
        """Record a memory miss."""
        self.memory_misses_total.labels(type=memory_type).inc()

    def record_vector_store_operation(self, operation: str, status: str):
        """Record a vector store operation."""
        self.vector_store_operations_total.labels(operation=operation, status=status).inc()

# Initialize metrics instance
memory_metrics = MemoryMetrics() 