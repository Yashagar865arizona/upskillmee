# Ponder Metrics and Monitoring Guide

This document provides a comprehensive overview of Ponder's metrics, monitoring, and logging capabilities.

## Quick Start Guide

### Viewing Metrics in Development

1. **Start the Application**
   ```bash
   cd backend
   uvicorn app.main:app --reload --log-level debug
   ```

2. **Access Metrics Dashboard**
   - Open your browser to `http://localhost:8000/metrics`
   - This shows real-time system metrics and current status

3. **Check Application Logs**
   ```bash
   # View live logs
   tail -f backend/logs/app.log
   
   # View only errors
   grep "ERROR" backend/logs/app.log
   
   # View metrics for today
   grep "$(date '+%Y-%m-%d')" backend/logs/app.log
   ```

4. **Database Metrics**
   ```bash
   # Connect to database
   psql $DATABASE_URL
   
   # View active users
   SELECT COUNT(DISTINCT user_id) FROM user_snapshots 
   WHERE created_at > NOW() - INTERVAL '24 hours';
   ```

5. **User Metrics**
   ```python
   # Via Python Shell
   from app.services.mentor_metrics_service import MentorMetricsService
   
   metrics = MentorMetricsService()
   user_metrics = metrics.get_user_metrics("user_id")
   print(user_metrics)
   ```

6. **Health Check**
   ```bash
   # Check system health
   curl http://localhost:8000/health
   
   # Check detailed metrics
   curl http://localhost:8000/metrics/detailed
   ```

### Common Monitoring Tasks

1. **Monitor User Progress**
   - Check user snapshots: `http://localhost:8000/api/users/{user_id}/progress`
   - View learning metrics: `http://localhost:8000/api/users/{user_id}/metrics`
   - Track engagement: `http://localhost:8000/api/users/{user_id}/engagement`

2. **System Health**
   - Monitor error rates: `http://localhost:8000/metrics/errors`
   - Check API performance: `http://localhost:8000/metrics/performance`
   - View cache status: `http://localhost:8000/metrics/cache`

3. **Debug Common Issues**
   ```bash
   # Check for database connection issues
   grep "Database connection error" logs/app.log
   
   # Monitor rate limiting
   grep "Rate limit exceeded" logs/app.log
   
   # Track slow queries
   grep "Query execution time" logs/app.log
   ```

4. **Export Metrics**
   ```bash
   # Export today's metrics to CSV
   python scripts/export_metrics.py --date today --format csv
   
   # Export user metrics
   python scripts/export_metrics.py --user-id {user_id} --format json
   ```

## System Metrics

### Application Logging

Logs are stored in the `logs/app.log` file and are configured with different levels of verbosity:

- **DEBUG**: Detailed information for debugging
- **INFO**: General application flow and state changes
- **WARNING**: Potential issues that don't affect core functionality
- **ERROR**: Serious issues that affect functionality
- **CRITICAL**: System-critical issues requiring immediate attention

To change the log level, modify `LOG_LEVEL` in your environment settings.

### Database Monitoring

Database metrics and events are tracked through various listeners:

- Connection pool status
- Query execution times
- Transaction success/failure rates
- Connection lifecycle events (checkout/checkin)

### Performance Metrics

The following performance metrics are tracked:

- Request latency
- Database query performance
- Rate limiting statistics
- Cache hit/miss rates

## User Metrics

### Engagement Metrics

Tracked in `UserSnapshot.engagement_metrics`:
```json
{
    "messages_per_day": float,
    "response_time_avg": float,  // in seconds
    "session_duration_avg": float,  // in minutes
    "active_days_streak": int,
    "project_completion_rate": float
}
```

### Learning Metrics

Tracked in `UserSnapshot.learning_progress`:
```json
{
    "completed_projects": int,
    "active_projects": int,
    "skill_progress": {
        "skill_name": float  // progress percentage
    },
    "learning_pace": float,  // relative to baseline
    "milestone_completion_rate": float
}
```

### Skill Improvements

Tracked in `UserSnapshot.skill_improvements`:
```json
{
    "technical_skills": {
        "skill_name": {
            "level": int,
            "progress": float,
            "last_updated": timestamp
        }
    },
    "soft_skills": {
        "skill_name": {
            "level": int,
            "progress": float,
            "last_updated": timestamp
        }
    }
}
```

## Project Metrics

### Project Tracking

Each project (`UserProject`) tracks:
```json
{
    "completion_percentage": int,
    "project_metrics": {
        "completion_rate": float,
        "quality_score": float,  // Scale 1-10
        "innovation_score": float,  // Scale 1-10
        "technical_accuracy": float  // Scale 1-10
    },
    "activity_metrics": {
        "engagement_level": float,  // Scale 1-10
        "consistency": float,  // Scale 1-10
        "resource_utilization": float  // Scale 1-10
    }
}
```

### Learning Effectiveness

Tracked per project:
```json
{
    "concept_understanding": float,  // Scale 1-10
    "skill_improvement": float,  // Scale 1-10
    "feedback_responsiveness": float,  // Scale 1-10
    "challenge_handling": float  // Scale 1-10
}
```

## Mentor Effectiveness Metrics

Tracked through `MentorMetricsService`:
```json
{
    "user_satisfaction": float,  // based on explicit feedback
    "concept_retention": float,  // based on follow-up discussions
    "progression_rate": float,  // speed of advancing through difficulty levels
    "engagement_score": float  // composite score
}
```

## Error Tracking

Errors are tracked with unique identifiers and include:
- Error ID
- Request path
- Error details
- Stack trace (in logs only)
- Timestamp
- Related user/session info

## Monitoring Tools

### Log Analysis

Logs can be analyzed using standard tools:
```bash
# View all errors
grep "ERROR" logs/app.log

# View metrics for a specific user
grep "user_id" logs/app.log

# Monitor real-time logs
tail -f logs/app.log
```

### Database Queries

Common monitoring queries:
```sql
-- Active users in last 24 hours
SELECT COUNT(DISTINCT user_id) 
FROM user_snapshots 
WHERE created_at > NOW() - INTERVAL '24 hours';

-- Project completion rates
SELECT 
    difficulty,
    AVG(completion_percentage) as avg_completion
FROM user_projects 
GROUP BY difficulty;

-- User engagement trends
SELECT 
    user_id,
    engagement_metrics->>'messages_per_day' as daily_messages
FROM user_snapshots
ORDER BY created_at DESC;
```

## Rate Limiting

Current rate limits:
- API calls: 60 per minute per IP
- Database connections: 5 permanent, 10 overflow
- Cache size: 10,000 items
- Cache TTL: 1 hour

## Health Checks

The `/health` endpoint provides:
- Application status
- Database connection status
- Cache status
- External service status (OpenAI, etc.)
- System resource usage

## Best Practices

1. **Regular Monitoring**
   - Check logs daily for ERROR and CRITICAL entries
   - Monitor user engagement trends weekly
   - Review performance metrics monthly

2. **Performance Optimization**
   - Monitor slow queries (>100ms)
   - Track cache hit rates
   - Review rate limit incidents

3. **User Experience**
   - Track user satisfaction metrics
   - Monitor project completion rates
   - Review learning progression paths

4. **Error Management**
   - Investigate all CRITICAL errors immediately
   - Review ERROR logs daily
   - Track error patterns weekly
