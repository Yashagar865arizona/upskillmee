# Enhanced Monitoring System Documentation

## Overview

The Ponder backend includes a comprehensive monitoring system that provides real-time health checks, performance monitoring, error tracking, and alerting capabilities. This system is designed for production use and includes advanced features for database monitoring and automated alerting.

## Components

### 1. Core Monitoring Service (`monitoring_service.py`)

The main monitoring service coordinates all monitoring components:

- **PerformanceMonitor**: Tracks API response times and request statistics
- **HealthChecker**: Performs health checks on critical system components
- **ErrorTracker**: Tracks and analyzes application errors
- **Integration with AlertingService**: Automatic alert generation based on thresholds

### 2. Alerting Service (`alerting_service.py`)

Provides comprehensive alerting capabilities:

- **Alert Types**: Health checks, performance, error rates, resource usage, database, AI services
- **Severity Levels**: Low, Medium, High, Critical
- **Notification Methods**: Email, webhooks, logging
- **Alert Management**: Creation, resolution, history tracking
- **Configurable Thresholds**: CPU, memory, disk, error rates, response times

### 3. Enhanced Database Monitoring (`enhanced_db_monitoring.py`)

Advanced database performance monitoring:

- **Connection Pool Monitoring**: Track connection usage and performance
- **Query Analysis**: Identify slow queries and performance issues
- **Database Health Checks**: Comprehensive database status monitoring
- **Performance Recommendations**: Automated suggestions for optimization

### 4. Monitoring Middleware (`monitoring_middleware.py`)

Automatic monitoring integration:

- **Request Tracking**: Automatically monitor all API requests
- **Performance Metrics**: Response time and status code tracking
- **Error Capture**: Automatic error tracking for failed requests
- **Health Headers**: Add health status to response headers

## API Endpoints

### Public Endpoints

#### Health Checks
```
GET /api/v1/monitoring/health
GET /api/v1/monitoring/health/database
GET /api/v1/monitoring/health/system
```

### Admin-Only Endpoints

#### System Status
```
GET /api/v1/monitoring/status
GET /api/v1/monitoring/performance
GET /api/v1/monitoring/performance/{endpoint}
GET /api/v1/monitoring/errors
```

#### Database Monitoring
```
GET /api/v1/monitoring/database/detailed
GET /api/v1/monitoring/database/query-analysis
```

#### Alerting System
```
GET /api/v1/monitoring/alerts
GET /api/v1/monitoring/alerts/history
POST /api/v1/monitoring/alerts/{alert_id}/resolve
GET /api/v1/monitoring/alerts/thresholds
PUT /api/v1/monitoring/alerts/thresholds
```

#### Historical Data
```
GET /api/v1/monitoring/metrics/historical/{metric_name}
```

## Configuration

### Alert Thresholds

Default thresholds can be configured via API or environment variables:

```python
{
    "cpu_percent": 80.0,
    "memory_percent": 85.0,
    "disk_percent": 90.0,
    "error_rate_per_hour": 10.0,
    "database_response_time": 1.0,
    "api_response_time": 2.0,
    "failed_health_checks": 3
}
```

### Email Notifications

Configure email alerts by setting environment variables:

```bash
ALERT_EMAIL_ENABLED=true
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-password
SMTP_USE_TLS=true
ADMIN_EMAILS=admin1@company.com,admin2@company.com
```

### Webhook Notifications

Configure webhook alerts:

```bash
ALERT_WEBHOOK_ENABLED=true
ALERT_WEBHOOK_URL=https://your-webhook-endpoint.com/alerts
```

## Monitoring Features

### 1. Health Checks

- **Database Connectivity**: Connection tests and query performance
- **System Resources**: CPU, memory, disk usage monitoring
- **AI Services**: OpenAI and DeepSeek API connectivity
- **Overall Status**: Aggregated health status

### 2. Performance Monitoring

- **API Response Times**: Track response times for all endpoints
- **Request Counts**: Monitor request volume and patterns
- **Error Rates**: Track error percentages by endpoint
- **Historical Trends**: Store and analyze performance over time

### 3. Error Tracking

- **Error Classification**: Categorize errors by type and severity
- **Error Rates**: Calculate error rates per hour/day
- **Error Context**: Capture request context and stack traces
- **Error Trends**: Identify patterns in error occurrence

### 4. Database Monitoring

- **Connection Pool Health**: Monitor connection usage and performance
- **Query Performance**: Identify slow and problematic queries
- **Database Statistics**: Track table access patterns and statistics
- **Lock Monitoring**: Detect database locks and blocking queries
- **Query Recommendations**: Automated optimization suggestions

### 5. Alerting System

- **Threshold-Based Alerts**: Automatic alerts when metrics exceed thresholds
- **Alert Management**: Create, resolve, and track alerts
- **Multiple Notification Channels**: Email, webhooks, and logging
- **Alert History**: Track alert patterns and resolution times
- **Configurable Thresholds**: Adjust alert sensitivity per environment

## Usage Examples

### Check System Health

```bash
curl http://localhost:8000/api/v1/monitoring/health
```

### Get Performance Metrics (Admin)

```bash
curl -H "Authorization: Bearer YOUR_ADMIN_TOKEN" \
     http://localhost:8000/api/v1/monitoring/performance
```

### View Active Alerts (Admin)

```bash
curl -H "Authorization: Bearer YOUR_ADMIN_TOKEN" \
     http://localhost:8000/api/v1/monitoring/alerts
```

### Update Alert Thresholds (Admin)

```bash
curl -X PUT \
     -H "Authorization: Bearer YOUR_ADMIN_TOKEN" \
     -H "Content-Type: application/json" \
     -d '{"cpu_percent": 85.0, "memory_percent": 90.0}' \
     http://localhost:8000/api/v1/monitoring/alerts/thresholds
```

### Resolve an Alert (Admin)

```bash
curl -X POST \
     -H "Authorization: Bearer YOUR_ADMIN_TOKEN" \
     http://localhost:8000/api/v1/monitoring/alerts/ALERT_ID/resolve
```

## Metrics Storage

The system automatically stores metrics to the database every 5 minutes:

- **System Metrics**: CPU, memory, disk usage
- **Performance Metrics**: Response times, error rates
- **Database Metrics**: Connection pool stats, query performance
- **Error Metrics**: Error counts and rates

## Production Deployment

### 1. Environment Configuration

Set appropriate environment variables for your production environment:

```bash
ENVIRONMENT=production
ALERT_EMAIL_ENABLED=true
ALERT_WEBHOOK_ENABLED=true
# ... other configuration
```

### 2. Monitoring Dashboard

The monitoring system provides comprehensive data that can be integrated with external monitoring tools:

- **Prometheus**: Metrics can be exported in Prometheus format
- **Grafana**: Create dashboards using the monitoring API
- **Custom Dashboards**: Build custom monitoring interfaces using the API

### 3. Alert Configuration

Configure appropriate thresholds for your production environment:

- **CPU**: 80-90% for warnings, 95%+ for critical
- **Memory**: 85-90% for warnings, 95%+ for critical
- **Disk**: 85-90% for warnings, 95%+ for critical
- **Error Rate**: 5-10 errors/hour for warnings, 20+ for critical

### 4. Notification Setup

Set up multiple notification channels:

- **Email**: For immediate admin notifications
- **Webhooks**: For integration with Slack, PagerDuty, etc.
- **Logging**: All alerts are logged for audit trails

## Troubleshooting

### Common Issues

1. **Database Connection Errors**
   - Check database connectivity
   - Verify connection pool configuration
   - Review database logs

2. **High Error Rates**
   - Check application logs
   - Review recent deployments
   - Analyze error patterns

3. **Performance Degradation**
   - Review slow query logs
   - Check system resource usage
   - Analyze API response times

### Debugging

Enable debug logging for detailed monitoring information:

```python
import logging
logging.getLogger('app.services.monitoring_service').setLevel(logging.DEBUG)
logging.getLogger('app.services.alerting_service').setLevel(logging.DEBUG)
```

## Testing

Run the comprehensive monitoring test suite:

```bash
cd backend
python test_enhanced_monitoring.py
```

This will test all monitoring components and verify system functionality.

## Integration with Frontend

The monitoring system can be integrated with a frontend dashboard:

1. **Health Status Widget**: Display overall system health
2. **Performance Charts**: Show API response times and error rates
3. **Alert Dashboard**: Display active alerts and alert history
4. **Database Metrics**: Show database performance and query analysis

## Security Considerations

- **Admin-Only Access**: Sensitive monitoring data requires admin authentication
- **Rate Limiting**: Monitoring endpoints are rate-limited to prevent abuse
- **Data Sanitization**: Sensitive data is filtered from error logs
- **Secure Notifications**: Email and webhook notifications use secure protocols

## Future Enhancements

Potential future improvements:

1. **Machine Learning**: Anomaly detection for unusual patterns
2. **Predictive Alerts**: Forecast potential issues before they occur
3. **Custom Metrics**: Allow applications to define custom monitoring metrics
4. **Advanced Dashboards**: Built-in web dashboard for monitoring data
5. **Integration APIs**: Better integration with external monitoring tools

## Support

For issues or questions about the monitoring system:

1. Check the logs for error details
2. Run the test suite to verify functionality
3. Review the API documentation for endpoint usage
4. Check configuration settings and environment variables