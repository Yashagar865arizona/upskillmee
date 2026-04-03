#!/bin/bash

# Docker Configuration Validation Script
# This script validates Docker configuration without requiring Docker to be running

set -e

echo "🔍 Validating Docker configuration..."

# Check if docker-compose.yml is valid
echo "✅ Checking docker-compose.yml syntax..."
if command -v docker-compose >/dev/null 2>&1; then
    docker-compose -f docker-compose.yml config >/dev/null
    echo "✅ docker-compose.yml syntax is valid"
else
    echo "⚠️  docker-compose not found, skipping syntax validation"
fi

# Check if Dockerfiles exist and have basic structure
echo "✅ Checking Dockerfile structure..."

# Backend Dockerfile
if [ -f "../backend/Dockerfile" ]; then
    echo "✅ Backend Dockerfile exists"
    if grep -q "FROM.*as base" "../backend/Dockerfile"; then
        echo "✅ Backend Dockerfile has multi-stage build"
    else
        echo "❌ Backend Dockerfile missing multi-stage build"
        exit 1
    fi
    if grep -q "HEALTHCHECK" "../backend/Dockerfile"; then
        echo "✅ Backend Dockerfile has health check"
    else
        echo "❌ Backend Dockerfile missing health check"
        exit 1
    fi
else
    echo "❌ Backend Dockerfile not found"
    exit 1
fi

# Frontend Dockerfile
if [ -f "../frontend/Dockerfile" ]; then
    echo "✅ Frontend Dockerfile exists"
    if grep -q "FROM.*as base" "../frontend/Dockerfile"; then
        echo "✅ Frontend Dockerfile has multi-stage build"
    else
        echo "❌ Frontend Dockerfile missing multi-stage build"
        exit 1
    fi
    if grep -q "HEALTHCHECK" "../frontend/Dockerfile"; then
        echo "✅ Frontend Dockerfile has health check"
    else
        echo "❌ Frontend Dockerfile missing health check"
        exit 1
    fi
else
    echo "❌ Frontend Dockerfile not found"
    exit 1
fi

# Check environment files
echo "✅ Checking environment configuration..."

if [ -f ".env" ]; then
    echo "✅ .env file exists"
    
    # Check for required variables
    required_vars=("POSTGRES_USER" "POSTGRES_PASSWORD" "POSTGRES_DB" "REDIS_PASSWORD" "JWT_SECRET")
    for var in "${required_vars[@]}"; do
        if grep -q "^${var}=" .env; then
            echo "✅ $var is configured"
        else
            echo "❌ $var is missing from .env"
            exit 1
        fi
    done
else
    echo "❌ .env file not found"
    exit 1
fi

# Check for required directories
echo "✅ Checking required directories..."

required_dirs=("postgres/init" "nginx/conf.d")
for dir in "${required_dirs[@]}"; do
    if [ -d "$dir" ]; then
        echo "✅ $dir directory exists"
    else
        echo "⚠️  $dir directory missing, creating..."
        mkdir -p "$dir"
    fi
done

# Check health endpoints
echo "✅ Checking health endpoints..."

if [ -f "../backend/app/api/health.py" ]; then
    echo "✅ Backend health endpoint exists"
else
    echo "❌ Backend health endpoint missing"
    exit 1
fi

if [ -f "../frontend/public/health" ]; then
    echo "✅ Frontend health endpoint exists"
else
    echo "❌ Frontend health endpoint missing"
    exit 1
fi

echo "🎉 Docker configuration validation completed successfully!"
echo ""
echo "Next steps:"
echo "1. Start Docker daemon"
echo "2. Run: docker-compose up --build"
echo "3. Test health endpoints:"
echo "   - Backend: curl http://localhost:8000/api/v1/health"
echo "   - Frontend: curl http://localhost:3000/health"