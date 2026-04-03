# Running Ponder Services

This guide explains how to run all the required services for Ponder to work properly.

## Prerequisites

1. **Docker Desktop**
   - Install from [Docker's website](https://www.docker.com/products/docker-desktop)
   - Make sure it's running before starting services

2. **Python Environment**
   ```bash
   # Create virtual environment
   python -m venv .venv
   
   # Activate virtual environment
   source .venv/bin/activate
   
   # Install dependencies
   pip install -r requirements.txt
   ```

## Required Services

### 1. Database Services (Docker)

#### PostgreSQL
```bash
# Start PostgreSQL
docker run -d \
  --name postgres \
  -p 5432:5432 \
  -e POSTGRES_PASSWORD=your_password \
  -e POSTGRES_DB=ponder \
  postgres

# Verify it's running
docker ps | grep postgres
```

#### Redis Cache
```bash
# Start Redis
docker run -d \
  --name redis \
  -p 6379:6379 \
  redis

# Verify it's running
docker ps | grep redis
```

#### Qdrant Vector Database
```bash
# Start Qdrant
docker run -d \
  --name qdrant \
  -p 6333:6333 \
  qdrant/qdrant

# Verify it's running
docker ps | grep qdrant
```

### 2. Application Server

```bash
# Make sure you're in the backend directory
cd backend

# Activate virtual environment (if not already activated)
source .venv/bin/activate

# Run FastAPI server
uvicorn app.main:app --reload
```

## Environment Variables

Make sure these environment variables are set in your `.env` file:

```bash
# Database
DATABASE_URL=postgresql://postgres:your_password@localhost:5432/ponder

# Redis
REDIS_URL=redis://localhost:6379

# OpenAI
OPENAI_API_KEY=your_openai_key

# Environment
ENVIRONMENT=development
```

## Verification

### Check if services are running:

```bash
# Check Docker containers
docker ps

# Should show:
# - postgres
# - redis
# - qdrant
```

### Test endpoints:
1. FastAPI Docs: http://localhost:8000/docs
2. Health Check: http://localhost:8000/health

## Troubleshooting

### Docker Issues
```bash
# Stop all containers
docker stop $(docker ps -a -q)

# Remove all containers
docker rm $(docker ps -a -q)

# Start fresh with the commands above
```

### Database Issues
```bash
# Run migrations
alembic upgrade head

# Reset database (WARNING: Deletes all data)
alembic downgrade base
alembic upgrade head
```

### Cache Issues
```bash
# Clear Redis cache
docker exec redis redis-cli FLUSHALL
```

## Starting Everything Fresh

Here's the complete sequence to start everything from scratch:

```bash
# 1. Start Docker Desktop

# 2. Start Docker services
docker run -d --name postgres -p 5432:5432 -e POSTGRES_PASSWORD=your_password -e POSTGRES_DB=ponder postgres
docker run -d --name redis -p 6379:6379 redis
docker run -d --name qdrant -p 6333:6333 qdrant/qdrant

# 3. Setup Python environment
cd backend
source .venv/bin/activate
pip install -r requirements.txt

# 4. Run migrations
alembic upgrade head

# 5. Start FastAPI server
uvicorn app.main:app --reload
```

## Stopping Everything

```bash
# 1. Stop FastAPI (Ctrl+C in the terminal running uvicorn)

# 2. Stop Docker containers
docker stop postgres redis qdrant

# Optional: Remove containers
docker rm postgres redis qdrant
```
