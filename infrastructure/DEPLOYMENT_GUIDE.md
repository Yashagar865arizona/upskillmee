# Ponder Platform Deployment Guide

This guide covers the complete deployment process for the Ponder platform, including Docker configuration, database setup, and production deployment.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Quick Start](#quick-start)
3. [Configuration](#configuration)
4. [Database Setup](#database-setup)
5. [Docker Deployment](#docker-deployment)
6. [Testing](#testing)
7. [Production Deployment](#production-deployment)
8. [Troubleshooting](#troubleshooting)

## Prerequisites

### System Requirements

- Docker 20.10+ and Docker Compose 2.0+
- 4GB+ RAM available for containers
- 10GB+ disk space
- Network access for downloading images

### Development Requirements

- Node.js 18+ (for local frontend development)
- Python 3.11+ (for local backend development)
- PostgreSQL client tools (optional, for database management)

## Quick Start

### Development Environment

1. **Clone and navigate to infrastructure directory:**
   ```bash
   cd infrastructure
   ```

2. **Copy environment configuration:**
   ```bash
   cp .env.development .env
   ```

3. **Start development environment:**
   ```bash
   ./scripts/dev-deploy.sh
   ```

4. **Access the application:**
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:8000
   - API Documentation: http://localhost:8000/docs

### Production Environment

1. **Copy production configuration:**
   ```bash
   cp .env.production .env
   ```

2. **Update environment variables:**
   ```bash
   nano .env  # Update with your production values
   ```

3. **Deploy to production:**
   ```bash
   ./scripts/deploy.sh
   ```

## Configuration

### Environment Variables

#### Required Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `POSTGRES_USER` | Database username | `ponder_user` |
| `POSTGRES_PASSWORD` | Database password | `secure_password_123` |
| `POSTGRES_DB` | Database name | `ponder_prod` |
| `REDIS_PASSWORD` | Redis password | `redis_password_123` |
| `JWT_SECRET` | JWT signing secret | `your-jwt-secret-key` |
| `ADMIN_API_KEY` | Admin API key | `your-admin-api-key` |

#### AI Service Configuration

| Variable | Description | Required |
|----------|-------------|----------|
| `OPENAI_API_KEY` | OpenAI API key | Yes |
| `DEEPSEEK_API_KEY` | DeepSeek API key | Optional |
| `ACTIVE_MODEL` | Active AI model | Yes |

#### Vector Database Configuration

| Variable | Description | Default |
|----------|-------------|---------|
| `VECTOR_STORE_TYPE` | Vector store type | `qdrant` |
| `QDRANT_HOST` | Qdrant hostname | `qdrant` |
| `QDRANT_PORT` | Qdrant port | `6333` |
| `PINECONE_API_KEY` | Pinecone API key | Optional |

### Service Ports

| Service | Development Port | Production Port |
|---------|------------------|-----------------|
| Frontend | 3000 | 3000 |
| Backend | 8000 | 8000 |
| PostgreSQL | 5432 | 5432 |
| Redis | 6379 | 6379 |
| Qdrant | 6333 | 6333 |
| Nginx | 80, 443 | 80, 443 |

## Database Setup

### PostgreSQL Configuration

The platform uses PostgreSQL 15 with the following optimizations:

- Connection pooling (10 connections, 20 max overflow)
- Query performance monitoring with `pg_stat_statements`
- Optimized memory settings for production workloads

### Required Extensions

- `pg_stat_statements` - Query performance monitoring
- `uuid-ossp` - UUID generation
- `vector` - Vector similarity search (optional)

### Migration Management

Migrations are managed using Alembic:

```bash
# Run migrations
docker-compose exec backend alembic upgrade head

# Check migration status
docker-compose exec backend alembic current

# View migration history
docker-compose exec backend alembic history
```

### Database Health Checks

Run comprehensive database health checks:

```bash
docker-compose exec backend python scripts/check_db_health.py
```

## Docker Deployment

### Multi-Stage Builds

Both frontend and backend use multi-stage Docker builds:

- **Development stage**: Includes dev dependencies and hot reload
- **Production stage**: Optimized for size and performance

### Health Checks

All services include health checks:

- **Backend**: `GET /api/v1/health`
- **Frontend**: `GET /health`
- **PostgreSQL**: `pg_isready`
- **Redis**: `redis-cli ping`
- **Qdrant**: `GET /health`

### Resource Limits

Production resource limits:

| Service | Memory Limit | CPU Limit |
|---------|--------------|-----------|
| Backend | 1GB | 0.5 CPU |
| Frontend | 512MB | 0.25 CPU |
| PostgreSQL | 1GB | 0.5 CPU |
| Redis | 512MB | 0.25 CPU |
| Qdrant | 1GB | 0.5 CPU |

## Testing

### Validation Scripts

1. **Docker Configuration Validation:**
   ```bash
   ./scripts/validate-docker-config.sh
   ```

2. **Database Health Check:**
   ```bash
   docker-compose exec backend python scripts/check_db_health.py
   ```

3. **Migration Testing:**
   ```bash
   docker-compose exec backend python scripts/test_migrations.py
   ```

4. **Qdrant Integration Testing:**
   ```bash
   docker-compose exec backend python scripts/test_qdrant_integration.py
   ```

5. **Comprehensive Deployment Testing:**
   ```bash
   ./scripts/test-deployment.sh
   ```

### Manual Testing

1. **API Endpoints:**
   ```bash
   curl http://localhost:8000/api/v1/health
   curl http://localhost:8000/docs
   ```

2. **Frontend:**
   ```bash
   curl http://localhost:3000/health
   ```

3. **Database Connection:**
   ```bash
   docker-compose exec db psql -U ponder_dev -d ponder_dev -c "SELECT 1;"
   ```

## Production Deployment

### Pre-Deployment Checklist

- [ ] Environment variables configured
- [ ] SSL certificates in place (if using HTTPS)
- [ ] Database backups configured
- [ ] Monitoring and logging set up
- [ ] Resource limits appropriate for load
- [ ] Security configurations reviewed

### Deployment Process

1. **Backup existing data:**
   ```bash
   ./scripts/deploy.sh backup
   ```

2. **Deploy new version:**
   ```bash
   ./scripts/deploy.sh deploy
   ```

3. **Verify deployment:**
   ```bash
   ./scripts/deploy.sh health
   ```

4. **Rollback if needed:**
   ```bash
   ./scripts/deploy.sh rollback
   ```

### Monitoring

#### Health Endpoints

- Backend: `http://localhost:8000/api/v1/health`
- Frontend: `http://localhost:3000/health`
- Qdrant: `http://localhost:6333/health`

#### Logs

```bash
# View all logs
docker-compose logs -f

# View specific service logs
docker-compose logs -f backend
docker-compose logs -f frontend
docker-compose logs -f db
```

#### Metrics

Access Prometheus metrics (if monitoring profile enabled):
- Prometheus: `http://localhost:9090`
- Grafana: `http://localhost:3001`

## Troubleshooting

### Common Issues

#### Database Connection Issues

**Symptoms:** Backend fails to start, database connection errors

**Solutions:**
1. Check database is running: `docker-compose ps db`
2. Verify credentials in `.env` file
3. Check database logs: `docker-compose logs db`
4. Test connection: `docker-compose exec db pg_isready -U $POSTGRES_USER`

#### Migration Failures

**Symptoms:** Backend starts but database schema is incorrect

**Solutions:**
1. Check migration status: `docker-compose exec backend alembic current`
2. Run migrations manually: `docker-compose exec backend alembic upgrade head`
3. Check migration logs: `docker-compose logs backend`

#### Qdrant Connection Issues

**Symptoms:** Vector search not working, embedding errors

**Solutions:**
1. Check Qdrant is running: `curl http://localhost:6333/health`
2. Verify Qdrant configuration in `.env`
3. Test integration: `docker-compose exec backend python scripts/test_qdrant_integration.py`

#### Frontend Build Issues

**Symptoms:** Frontend container fails to start or build

**Solutions:**
1. Check Node.js version in Dockerfile
2. Clear Docker build cache: `docker-compose build --no-cache frontend`
3. Check frontend logs: `docker-compose logs frontend`

#### Resource Issues

**Symptoms:** Containers being killed, out of memory errors

**Solutions:**
1. Increase Docker memory limits
2. Adjust resource limits in `docker-compose.yml`
3. Monitor resource usage: `docker stats`

### Debug Commands

```bash
# Check container status
docker-compose ps

# View resource usage
docker stats

# Access container shell
docker-compose exec backend bash
docker-compose exec frontend sh

# Check network connectivity
docker-compose exec backend ping db
docker-compose exec backend ping redis
docker-compose exec backend ping qdrant

# Restart specific service
docker-compose restart backend

# Rebuild and restart
docker-compose up --build -d backend
```

### Log Analysis

```bash
# Search for errors in logs
docker-compose logs backend | grep -i error
docker-compose logs frontend | grep -i error

# Follow logs in real-time
docker-compose logs -f --tail=100 backend

# Export logs for analysis
docker-compose logs backend > backend.log
```

## Support

For additional support:

1. Check the logs using the commands above
2. Run the comprehensive test suite: `./scripts/test-deployment.sh`
3. Review the troubleshooting section
4. Check Docker and system resources

## Security Considerations

### Production Security

- Change all default passwords and secrets
- Use strong, randomly generated passwords
- Enable SSL/TLS for all external connections
- Regularly update Docker images
- Monitor for security vulnerabilities
- Implement proper backup and disaster recovery

### Network Security

- Use Docker networks to isolate services
- Limit exposed ports to only what's necessary
- Implement proper firewall rules
- Use reverse proxy (Nginx) for SSL termination