# Ponder Infrastructure

This directory contains the Docker-based infrastructure configuration for the Ponder AI learning platform.

## 🏗️ Architecture Overview

The infrastructure consists of the following services:

- **Backend**: FastAPI application with 19+ services
- **Frontend**: React application with modern UI
- **Database**: PostgreSQL 15 with vector extensions
- **Cache**: Redis with persistence
- **Vector DB**: Qdrant for embeddings
- **Reverse Proxy**: Nginx with SSL termination
- **Monitoring**: Prometheus + Grafana (optional)

## 🚀 Quick Start

### Development Setup

1. **Clone and navigate to infrastructure directory**:
   ```bash
   cd infrastructure
   ```

2. **Copy environment file**:
   ```bash
   cp .env.development .env
   ```

3. **Start development environment**:
   ```bash
   docker-compose up -d
   ```

4. **Access the application**:
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:8000
   - API Docs: http://localhost:8000/docs
   - Database Admin: http://localhost:8080 (Adminer)
   - Redis Admin: http://localhost:8081 (Redis Commander)

### Production Deployment

1. **Generate secure secrets**:
   ```bash
   ./scripts/generate-secrets.sh
   ```

2. **Create production environment file**:
   ```bash
   cp .env.production .env
   # Edit .env with your production values
   ```

3. **Deploy to production**:
   ```bash
   ./scripts/deploy.sh
   ```

## 📁 Directory Structure

```
infrastructure/
├── docker-compose.yml          # Main compose file
├── docker-compose.override.yml # Development overrides
├── .env.production            # Production environment template
├── .env.development           # Development environment template
├── nginx/
│   └── conf.d/
│       └── default.conf       # Nginx configuration
├── postgres/
│   └── init/
│       └── 01-init.sql        # Database initialization
├── monitoring/
│   └── prometheus.yml         # Monitoring configuration
├── scripts/
│   ├── deploy.sh             # Deployment script
│   └── generate-secrets.sh   # Secrets generation
└── secrets/                  # Generated secrets (gitignored)
```

## 🔧 Configuration

### Environment Variables

#### Core Configuration
- `ENVIRONMENT`: deployment environment (development/production)
- `BUILD_TARGET`: Docker build target (development/production)
- `NODE_ENV`: Node.js environment

#### Service Ports
- `BACKEND_PORT`: Backend service port (default: 8000)
- `FRONTEND_PORT`: Frontend service port (default: 3000)
- `POSTGRES_PORT`: PostgreSQL port (default: 5432)
- `REDIS_PORT`: Redis port (default: 6379)

#### Security (Critical for Production)
- `JWT_SECRET`: JWT signing secret
- `ADMIN_API_KEY`: Admin API access key
- `POSTGRES_PASSWORD`: Database password
- `REDIS_PASSWORD`: Redis password

#### AI Services
- `OPENAI_API_KEY`: OpenAI API key
- `DEEPSEEK_API_KEY`: DeepSeek API key
- `ACTIVE_MODEL`: Active AI model (default: gpt-4o-mini)

### Docker Compose Profiles

#### Default Profile
Runs core services: backend, frontend, database, cache, vector DB, nginx

#### Monitoring Profile
```bash
docker-compose --profile monitoring up -d
```
Adds: Prometheus, Grafana

#### Dev Tools Profile
```bash
docker-compose --profile dev-tools up -d
```
Adds: Adminer (DB admin), Redis Commander

## 🔒 Security Features

### Production Security
- Non-root containers
- Resource limits and reservations
- Health checks with proper timeouts
- Restart policies
- Network isolation
- SSL/TLS termination
- Security headers
- Rate limiting
- Input validation

### Secrets Management
- Environment-based secrets
- Generated secure passwords
- Gitignored secrets directory
- Proper file permissions

## 📊 Monitoring & Health Checks

### Health Endpoints
- Backend: `GET /api/v1/health`
- Frontend: `GET /health`
- Database: `pg_isready` command
- Redis: `redis-cli ping`

### Monitoring Stack
- **Prometheus**: Metrics collection
- **Grafana**: Visualization dashboards
- **Health Checks**: Docker native health monitoring

### Metrics Collected
- API response times
- Database performance
- Cache hit rates
- System resources
- Error rates

## 🔄 Deployment Strategies

### Zero-Downtime Deployment
1. Health checks ensure services are ready
2. Graceful shutdown with timeouts
3. Rolling updates with dependency management
4. Automatic rollback on failure

### Backup Strategy
- Automated database backups
- Volume snapshots
- Configuration backups
- Point-in-time recovery

## 🛠️ Development Tools

### Available Commands

```bash
# Start all services
docker-compose up -d

# Start with monitoring
docker-compose --profile monitoring up -d

# Start with dev tools
docker-compose --profile dev-tools up -d

# View logs
docker-compose logs -f [service_name]

# Execute commands in containers
docker-compose exec backend bash
docker-compose exec db psql -U ponder_user ponder_db

# Scale services
docker-compose up -d --scale backend=3

# Stop services
docker-compose down

# Clean up
docker-compose down -v --remove-orphans
```

### Database Management

```bash
# Connect to database
docker-compose exec db psql -U ponder_user ponder_db

# Run migrations
docker-compose exec backend alembic upgrade head

# Create migration
docker-compose exec backend alembic revision --autogenerate -m "description"

# Backup database
docker-compose exec db pg_dump -U ponder_user ponder_db > backup.sql

# Restore database
docker-compose exec -T db psql -U ponder_user ponder_db < backup.sql
```

## 🚨 Troubleshooting

### Common Issues

#### Services Not Starting
```bash
# Check logs
docker-compose logs [service_name]

# Check health status
docker-compose ps

# Restart specific service
docker-compose restart [service_name]
```

#### Database Connection Issues
```bash
# Check database status
docker-compose exec db pg_isready -U ponder_user

# Check database logs
docker-compose logs db

# Reset database
docker-compose down -v
docker-compose up -d db
```

#### Performance Issues
```bash
# Check resource usage
docker stats

# Check service health
./scripts/deploy.sh health

# Monitor logs
docker-compose logs -f --tail=100
```

### Debug Mode

Enable debug logging:
```bash
# Set in .env file
LOG_LEVEL=DEBUG

# Restart services
docker-compose restart backend
```

## 📈 Scaling

### Horizontal Scaling
```bash
# Scale backend services
docker-compose up -d --scale backend=3

# Scale with load balancer
# (Nginx automatically load balances)
```

### Vertical Scaling
Adjust resource limits in `docker-compose.yml`:
```yaml
deploy:
  resources:
    limits:
      memory: 2G
      cpus: '1.0'
```

## 🔐 Production Checklist

### Before Deployment
- [ ] Generate secure secrets
- [ ] Configure SSL certificates
- [ ] Set up monitoring alerts
- [ ] Configure backup strategy
- [ ] Review security settings
- [ ] Test health checks
- [ ] Verify environment variables

### After Deployment
- [ ] Verify all services are healthy
- [ ] Test critical user flows
- [ ] Monitor performance metrics
- [ ] Set up log aggregation
- [ ] Configure alerting
- [ ] Document runbooks

## 📞 Support

For infrastructure issues:
1. Check service logs: `docker-compose logs [service]`
2. Verify health checks: `./scripts/deploy.sh health`
3. Review monitoring dashboards
4. Check resource usage: `docker stats`

## 🔄 Updates

### Updating Services
```bash
# Pull latest images
docker-compose pull

# Rebuild and restart
docker-compose up -d --build

# Or use deployment script
./scripts/deploy.sh
```

### Database Migrations
```bash
# Run migrations
docker-compose exec backend alembic upgrade head

# Check migration status
docker-compose exec backend alembic current
```