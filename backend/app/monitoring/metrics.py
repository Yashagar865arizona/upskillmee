"""
Monitoring metrics for tracking application performance and usage.

This module provides Prometheus metrics for various components of the application:
- EmbeddingMetrics: Tracks embedding creation, cache hits, and queue size
- ChatMetrics: Tracks message counts, response times, and token usage
- CacheMetrics: Tracks cache hits, misses, and operation latency
- AIMetrics: Tracks AI API calls, errors, and latency

Each metrics class is instantiated at the module level for easy import and use
throughout the application.
"""

from prometheus_client import Counter, Histogram, Gauge
# No additional imports needed

class EmbeddingMetrics:
    """Metrics for tracking embedding operations."""

    def __init__(self):
        self.cache_hits = Counter(
            'embedding_cache_hits_total',
            'Number of embedding cache hits'
        )
        self.embedding_errors = Counter(
            'embedding_errors_total',
            'Number of embedding creation errors',
            ['error_type']
        )
        self.embedding_creation_duration = Histogram(
            'embedding_creation_duration_seconds',
            'Time spent creating embeddings',
            buckets=[0.1, 0.5, 1.0, 2.0, 5.0]
        )
        self.embedding_cache_size = Gauge(
            'embedding_cache_size_bytes',
            'Current size of embedding cache in bytes'
        )
        self.embedding_queue_size = Gauge(
            'embedding_queue_size',
            'Current number of pending embedding requests'
        )
        self.embedding_index_size = Gauge(
            'embedding_index_size',
            'Current number of embeddings in the index'
        )

    def record_cache_hit(self):
        """Record a cache hit for embeddings."""
        self.cache_hits.inc()

    def record_error(self, error_type: str):
        """Record an error during embedding creation."""
        self.embedding_errors.labels(error_type=error_type).inc()

    def record_embedding_creation(self, duration: float):
        """Record the time taken to create an embedding."""
        self.embedding_creation_duration.observe(duration)

    def update_cache_size(self, size_bytes: int):
        """Update the current size of the embedding cache."""
        self.embedding_cache_size.set(size_bytes)

    def update_queue_size(self, size: int):
        """Update the current size of the embedding request queue."""
        self.embedding_queue_size.set(size)

    def update_index_size(self, size: int):
        """Update the current size of the embedding index."""
        self.embedding_index_size.set(size)

class ChatMetrics:
    """Metrics for tracking chat operations."""

    def __init__(self):
        self.message_count = Counter(
            'chat_messages_total',
            'Total number of chat messages',
            ['role', 'type']
        )
        self.response_time = Histogram(
            'chat_response_time_seconds',
            'Time to generate chat responses',
            buckets=[0.5, 1.0, 2.0, 5.0, 10.0]
        )
        self.token_usage = Counter(
            'chat_token_usage_total',
            'Total number of tokens used',
            ['model']
        )
        self.error_count = Counter(
            'chat_errors_total',
            'Number of chat errors',
            ['error_type']
        )
        self.active_conversations = Gauge(
            'chat_active_conversations',
            'Number of active chat conversations'
        )

    def record_message(self, role: str, msg_type: str):
        """Record a new chat message."""
        self.message_count.labels(role=role, type=msg_type).inc()

    def record_response_time(self, duration: float):
        """Record the time taken to generate a chat response."""
        self.response_time.observe(duration)

    def record_token_usage(self, model: str, tokens: int):
        """Record token usage for a specific model."""
        self.token_usage.labels(model=model).inc(tokens)

    def record_error(self, error_type: str):
        """Record a chat error."""
        self.error_count.labels(error_type=error_type).inc()

    def update_active_conversations(self, count: int):
        """Update the count of active conversations."""
        self.active_conversations.set(count)

class CacheMetrics:
    """Metrics for tracking cache operations."""

    def __init__(self):
        self.cache_hits = Counter(
            'cache_hits_total',
            'Number of cache hits',
            ['cache_type']
        )
        self.cache_misses = Counter(
            'cache_misses_total',
            'Number of cache misses',
            ['cache_type']
        )
        self.cache_size = Gauge(
            'cache_size_bytes',
            'Current cache size in bytes',
            ['cache_type']
        )
        self.cache_operations = Counter(
            'cache_operations_total',
            'Number of cache operations',
            ['operation', 'status']
        )
        self.cache_latency = Histogram(
            'cache_operation_duration_seconds',
            'Cache operation duration',
            ['operation'],
            buckets=[0.001, 0.005, 0.01, 0.05, 0.1]
        )

    def record_hit(self, cache_type: str):
        """Record a cache hit."""
        self.cache_hits.labels(cache_type=cache_type).inc()

    def record_miss(self, cache_type: str):
        """Record a cache miss."""
        self.cache_misses.labels(cache_type=cache_type).inc()

    def update_size(self, cache_type: str, size_bytes: int):
        """Update the size of a specific cache."""
        self.cache_size.labels(cache_type=cache_type).set(size_bytes)

    def record_operation(self, operation: str, status: str):
        """Record a cache operation with its status."""
        self.cache_operations.labels(operation=operation, status=status).inc()

    def record_latency(self, operation: str, duration: float):
        """Record the latency of a cache operation."""
        self.cache_latency.labels(operation=operation).observe(duration)

class AIMetrics:
    """Metrics for tracking AI API operations."""

    def __init__(self):
        # Basic API metrics
        self.api_calls = Counter(
            'ai_api_calls_total',
            'Total number of AI API calls'
        )
        self.api_errors = Counter(
            'ai_api_errors_total',
            'Number of AI API errors'
        )
        self.api_latency = Histogram(
            'ai_api_latency_seconds',
            'AI API latency in seconds',
            buckets=[0.1, 0.5, 1.0, 2.0, 5.0, 10.0]
        )

        # Model-specific metrics
        self.model_requests = Counter(
            'ai_model_requests_total',
            'Total number of requests by model',
            ['model']
        )
        self.model_errors = Counter(
            'ai_model_errors_total',
            'Number of errors by model',
            ['model']
        )
        self.model_response_time = Histogram(
            'ai_model_response_time_seconds',
            'Response time by model in seconds',
            ['model'],
            buckets=[0.1, 0.5, 1.0, 2.0, 5.0, 10.0, 30.0, 60.0]
        )

        # Fallback metrics
        self.fallback_count = Counter(
            'ai_fallback_total',
            'Total number of fallbacks to alternative models'
        )
        self.fallback_success = Counter(
            'ai_fallback_success_total',
            'Number of successful fallbacks'
        )
        self.fallback_failure = Counter(
            'ai_fallback_failure_total',
            'Number of failed fallbacks'
        )
        self.fallback_time = Histogram(
            'ai_fallback_time_seconds',
            'Time taken for fallback operations',
            buckets=[0.1, 0.5, 1.0, 2.0, 5.0, 10.0, 30.0]
        )

    def api_success(self):
        """Record a successful AI API call."""
        self.api_calls.inc()

    def api_failure(self):
        """Record a failed AI API call."""
        self.api_errors.inc()

    def record_latency(self, duration: float):
        """Record the latency of an AI API call."""
        self.api_latency.observe(duration)

    def increment_request_count(self, model: str):
        """Increment the request count for a specific model."""
        self.api_calls.inc()
        self.model_requests.labels(model=model).inc()

    def increment_error_count(self, model: str):
        """Increment the error count for a specific model."""
        self.api_errors.inc()
        self.model_errors.labels(model=model).inc()

    def record_response_time(self, model: str, duration: float):
        """Record the response time for a specific model."""
        self.api_latency.observe(duration)
        self.model_response_time.labels(model=model).observe(duration)

    def increment_fallback_count(self):
        """Increment the count of fallbacks to alternative models."""
        self.fallback_count.inc()

    def increment_fallback_success(self):
        """Increment the count of successful fallbacks."""
        self.fallback_success.inc()

    def increment_fallback_failure_count(self):
        """Increment the count of failed fallbacks."""
        self.fallback_failure.inc()

    def record_fallback_time(self, duration: float):
        """Record the time taken for a fallback operation."""
        self.fallback_time.observe(duration)
        self.increment_fallback_success()

# Initialize metric instances
ai_metrics = AIMetrics()
embedding_metrics = EmbeddingMetrics()
chat_metrics = ChatMetrics()
cache_metrics = CacheMetrics()