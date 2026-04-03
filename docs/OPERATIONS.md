# Ponder Operations Guide

This document outlines all the essential commands and operations needed to manage the Ponder application.

## Table of Contents
- [Environment Setup](#environment-setup)
- [Database Operations](#database-operations)
- [Development Commands](#development-commands)
- [Production Deployment](#production-deployment)
- [Production Setup](#production-setup)
- [Maintenance Tasks](#maintenance-tasks)

## Environment Setup

### Initial Setup
```bash
# Create and activate virtual environment
python -m venv venv
source venv/bin/activate  # On Unix/macOS
.\venv\Scripts\activate   # On Windows

# Install dependencies
pip install -r requirements.txt

# Install development dependencies
pip install -r requirements-dev.txt
```

### Environment Configuration
```bash
# Copy environment templates
cp .env.example .env
cp .env.development.example .env.development
cp .env.production.example .env.production

# Set environment
export ENVIRONMENT=development  # For development
export ENVIRONMENT=production   # For production
```

## Database Operations

### Database Setup
```bash
# Install PostgreSQL (macOS)
brew install postgresql@15
brew services start postgresql@15

# Create database
createdb ponder_dev     # Development database
createdb ponder_prod    # Production database
```

### Database Migrations
```bash
# Initialize Alembic (first time only)
alembic init migrations

# Create new migration
alembic revision --autogenerate -m "description_of_changes"

# Run migrations
alembic upgrade head                # Apply all pending migrations
alembic upgrade +1                  # Apply next migration
alembic downgrade -1                # Rollback last migration
alembic downgrade base              # Rollback all migrations

# View migration status
alembic current                     # Show current revision
alembic history                     # Show migration history
```

### Database Maintenance
```bash
# Backup database
python manage.py backup_db

# Restore database from backup
python manage.py restore_db --backup-file backup_filename.sql

# Reset database (Development only)
python manage.py reset_db --confirm

# Export database analytics
python manage.py export_analytics
```

## Development Commands

### Running the Application
```bash
# Start development server
uvicorn app.main:app --reload --port 8000

# Start with specific host
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Start with debug logging
uvicorn app.main:app --reload --log-level debug
```

### Testing
```bash
# Run all tests
pytest

# Run specific test file
pytest tests/test_file.py

# Run with coverage
pytest --cov=app tests/

# Generate coverage report
pytest --cov=app --cov-report=html tests/
```

### Code Quality
```bash
# Run linter
flake8 app/

# Run type checker
mypy app/

# Format code
black app/
isort app/
```

## Production Deployment

### Deployment Checklist
```bash
# 1. Set production environment
export ENVIRONMENT=production

# 2. Install production dependencies
pip install -r requirements.txt

# 3. Run database migrations
alembic upgrade head

# 4. Start application with Gunicorn
gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker -b 0.0.0.0:8000
```

### Docker Commands
```bash
# Build Docker image
docker build -t ponder:latest .

# Run Docker container
docker run -d -p 8000:8000 --env-file .env.production ponder:latest

# View logs
docker logs -f container_name

# Stop container
docker stop container_name
```

## Production Setup

### 1. Database Migrations
```bash
# In production server
cd /path/to/backend
alembic revision --autogenerate -m "Add user and profile tables"
alembic upgrade head
```

### 2. Production Environment Setup
```bash
# Create required directories with proper permissions
sudo mkdir -p /var/backups/ponder
sudo mkdir -p /var/data/ponder/analytics
sudo chown -R your_app_user:your_app_group /var/backups/ponder
sudo chown -R your_app_user:your_app_group /var/data/ponder

# Update production environment variables in .env.production:
DATABASE_URL=postgresql://actual_user:actual_password@actual_host:5432/ponder_prod
ADMIN_API_KEY=your_secure_admin_key
JWT_SECRET=your_secure_jwt_secret
OPENAI_API_KEY=your_production_openai_key
```

### 3. Error Logging Setup
```bash
# Install production logging dependencies
pip install python-json-logger

# Create log directory
sudo mkdir -p /var/log/ponder
sudo chown -R your_app_user:your_app_group /var/log/ponder

# Add to .env.production
LOG_LEVEL=INFO
LOG_FILE=/var/log/ponder/app.log
```

### 4. Start Production Server
```bash
# Install production server
pip install gunicorn

# Start server with proper workers
gunicorn app.main:app --workers 4 --worker-class uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000 --env-file .env.production
```

### 5. Testing in Production
```bash
# Test user creation
curl -X POST https://your-production-domain/api/v1/users \
-H "Content-Type: application/json" \
-d '{
    "name": "Test User",
    "email": "test@example.com"
}'

# Verify in database
psql postgresql://user:pass@host:5432/ponder_prod
> SELECT * FROM users;
> SELECT * FROM user_profiles;
```

### 6. Monitoring
```bash
# Monitor application logs
tail -f /var/log/ponder/app.log

# Monitor system logs
journalctl -u your-service-name -f
```

### 7. Health Checks
After deployment, verify these endpoints:
- `/api/v1/health` - Basic health check
- `/api/v1/metrics` - Application metrics
- `/api/v1/users` - User creation endpoint

### 8. Backup Verification
Ensure automatic backups are working:
1. Check `/var/backups/ponder` for database backups
2. Verify backup rotation (MAX_BACKUP_COUNT=30)
3. Test backup restoration in a staging environment

### 9. Security Checklist
- [ ] All production secrets are properly set
- [ ] Database passwords are secure
- [ ] JWT_SECRET is a strong random value
- [ ] ADMIN_API_KEY is properly secured
- [ ] File permissions are correctly set
- [ ] Database is not exposed to public internet
- [ ] CORS settings are properly configured

## Maintenance Tasks

### Log Management
```bash
# View application logs
tail -f logs/app.log

# View error logs
tail -f logs/error.log

# Rotate logs
logrotate /etc/logrotate.d/ponder
```

### Monitoring
```bash
# Check application status
curl http://localhost:8000/api/v1/health

# View system metrics
python manage.py show_metrics

# Monitor resource usage
top -pid $(pgrep -f "uvicorn app.main:app")
```

### Cache Management
```bash
# Clear application cache
python manage.py clear_cache

# View cache stats
python manage.py cache_stats
```

### User Management
```bash
# Create admin user
python manage.py create_admin --email admin@example.com

# List users
python manage.py list_users

# Reset user password
python manage.py reset_password --email user@example.com
```

## Environment Variables Reference

### Required Variables
- `DATABASE_URL`: PostgreSQL connection string
- `OPENAI_API_KEY`: OpenAI API key for AI features
- `JWT_SECRET`: Secret key for JWT token generation
- `ENVIRONMENT`: Application environment (development/production)

### Optional Variables
- `LOG_LEVEL`: Logging level (default: INFO)
- `PORT`: Application port (default: 8000)
- `HOST`: Application host (default: 0.0.0.0)
- `CORS_ORIGINS`: Allowed CORS origins
- `REDIS_URL`: Redis connection string for caching

## Common Issues and Solutions

### Database Connection Issues
```bash
# Check database status
pg_isready

# Reset PostgreSQL service
brew services restart postgresql@15

# View PostgreSQL logs
tail -f /usr/local/var/log/postgres.log
```

### Application Issues
```bash
# Clear all application caches
python manage.py clear_all_caches

# Verify environment
python manage.py check_env

# Run diagnostics
python manage.py diagnostics
```

## Security Operations

### SSL/TLS Management
```bash
# Generate SSL certificate (development)
openssl req -x509 -nodes -days 365 -newkey rsa:2048 -keyout cert.key -out cert.pem

# View SSL certificate info
openssl x509 -in cert.pem -text -noout
```

### Backup Operations
```bash
# Full system backup
python manage.py backup_all

# Backup specific components
python manage.py backup --component database
python manage.py backup --component uploads
python manage.py backup --component config
```

Remember to always check the logs (`logs/app.log` and `logs/error.log`) when troubleshooting issues. For production deployments, ensure all security measures are in place and environment variables are properly set.
