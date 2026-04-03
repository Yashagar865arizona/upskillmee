"""
Monitoring package for tracking application performance and usage.

This package provides metrics and monitoring tools for the application:
- Prometheus metrics for various components
- Utility functions for tracking performance
- Integration with monitoring systems

Import the metrics directly from the metrics module:
    from app.monitoring.metrics import ai_metrics, embedding_metrics, cache_metrics, chat_metrics
"""

from .metrics import ai_metrics, embedding_metrics, cache_metrics, chat_metrics

__all__ = ['ai_metrics', 'embedding_metrics', 'cache_metrics', 'chat_metrics'] 