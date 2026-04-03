#!/bin/bash

# Development deployment script for Ponder platform
set -e

echo "🚀 Starting Ponder development deployment..."

# Function to check if a service is healthy
check_service_health() {
    local service=$1
    local url=$2
    local max_attempts=30
    local attempt=1
    
    echo "🔍 Checking $service health..."
    
    while [ $attempt -le $max_attempts ]; do
        if curl -f -s "$url" > /dev/null 2>&1; then
            echo "✅ $service is healthy"
            return 0
        fi
        
        echo "⏳ Attempt $attempt/$max_attempts: $service not ready yet..."
        sleep 10
        attempt=$((attempt + 1))
    done
    
    echo "❌ $service failed to become healthy after $max_attempts attempts"
    return 1
}

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker and try again."
    exit 1
fi

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo "❌ .env file not found. Copying from .env.development..."
    cp .env.development .env
    echo "✅ Created .env file from development template"
fi

# Validate Docker configuration
echo "🔍 Validating Docker configuration..."
./scripts/validate-docker-config.sh

# Stop any existing containers
echo "🛑 Stopping existing containers..."
docker-compose down --remove-orphans

# Build and start services
echo "📦 Building and starting services..."
docker-compose up --build -d

# Wait for database to be ready
echo "⏳ Waiting for database to initialize..."
sleep 20

# Check individual service health
echo "🔍 Checking service health..."

# Check database
echo "🔍 Checking Database..."
if docker-compose exec -T db pg_isready -U ponder_dev -d ponder_dev > /dev/null 2>&1; then
    echo "✅ Database is healthy"
else
    echo "❌ Database health check failed"
fi

# Check Redis
echo "🔍 Checking Redis..."
if docker-compose exec -T redis redis-cli -a "dev_redis_password" ping > /dev/null 2>&1; then
    echo "✅ Redis is healthy"
else
    echo "❌ Redis health check failed"
fi

# Check Qdrant
if ! check_service_health "Qdrant" "http://localhost:6333/health"; then
    echo "❌ Qdrant health check failed"
fi

# Check Backend
if ! check_service_health "Backend" "http://localhost:8000/api/v1/health"; then
    echo "❌ Backend health check failed"
    echo "📋 Backend logs:"
    docker-compose logs --tail=50 backend
    exit 1
fi

# Check Frontend
if ! check_service_health "Frontend" "http://localhost:3000/health"; then
    echo "❌ Frontend health check failed"
    echo "📋 Frontend logs:"
    docker-compose logs --tail=50 frontend
    exit 1
fi

# Show final status
echo "📊 Final service status:"
docker-compose ps

echo ""
echo "✅ Development deployment completed successfully!"
echo "🌐 Access the application at:"
echo "   Frontend: http://localhost:3000"
echo "   Backend API: http://localhost:8000"
echo "   API Docs: http://localhost:8000/docs"
echo "   Qdrant Dashboard: http://localhost:6333/dashboard"
echo "   Adminer (DB): http://localhost:8080 (if dev-tools profile enabled)"
echo "   Redis Commander: http://localhost:8081 (if dev-tools profile enabled)"
echo ""
echo "📋 Useful commands:"
echo "   View logs: docker-compose logs -f [service]"
echo "   Stop services: docker-compose down"
echo "   Restart service: docker-compose restart [service]"
echo "   Enable dev tools: docker-compose --profile dev-tools up -d"