#!/bin/bash

# Comprehensive deployment testing script for Ponder platform
set -e

echo "🧪 Starting comprehensive deployment testing..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Functions
log_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

log_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

log_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

log_error() {
    echo -e "${RED}❌ $1${NC}"
}

# Test results tracking
TESTS_PASSED=0
TESTS_TOTAL=0

run_test() {
    local test_name="$1"
    local test_command="$2"
    
    log_info "Running test: $test_name"
    TESTS_TOTAL=$((TESTS_TOTAL + 1))
    
    if eval "$test_command"; then
        log_success "$test_name passed"
        TESTS_PASSED=$((TESTS_PASSED + 1))
        return 0
    else
        log_error "$test_name failed"
        return 1
    fi
}

# Check prerequisites
check_prerequisites() {
    log_info "Checking prerequisites..."
    
    # Check Docker
    if ! command -v docker &> /dev/null; then
        log_error "Docker is not installed"
        return 1
    fi
    
    # Check Docker Compose
    if ! command -v docker-compose &> /dev/null; then
        log_error "Docker Compose is not installed"
        return 1
    fi
    
    # Check if Docker is running
    if ! docker info > /dev/null 2>&1; then
        log_error "Docker daemon is not running"
        return 1
    fi
    
    # Check environment file
    if [ ! -f ".env" ]; then
        log_warning ".env file not found, copying from .env.development"
        cp .env.development .env
    fi
    
    log_success "Prerequisites check passed"
    return 0
}

# Test Docker configuration
test_docker_config() {
    log_info "Testing Docker configuration..."
    
    # Validate docker-compose syntax
    if ! docker-compose config > /dev/null 2>&1; then
        log_error "Docker Compose configuration is invalid"
        return 1
    fi
    
    # Run validation script
    if [ -f "scripts/validate-docker-config.sh" ]; then
        if ! ./scripts/validate-docker-config.sh > /dev/null 2>&1; then
            log_error "Docker configuration validation failed"
            return 1
        fi
    fi
    
    log_success "Docker configuration is valid"
    return 0
}

# Test database setup
test_database_setup() {
    log_info "Testing database setup..."
    
    # Start only database services
    docker-compose up -d db redis qdrant
    
    # Wait for services to be ready
    sleep 30
    
    # Test database connection
    if ! docker-compose exec -T db pg_isready -U ponder_dev -d ponder_dev > /dev/null 2>&1; then
        log_error "Database is not ready"
        return 1
    fi
    
    # Test Redis connection
    if ! docker-compose exec -T redis redis-cli -a "dev_redis_password" ping > /dev/null 2>&1; then
        log_error "Redis is not ready"
        return 1
    fi
    
    # Test Qdrant connection
    if ! curl -f -s http://localhost:6333/health > /dev/null 2>&1; then
        log_error "Qdrant is not ready"
        return 1
    fi
    
    log_success "Database services are ready"
    return 0
}

# Test backend build and startup
test_backend_deployment() {
    log_info "Testing backend deployment..."
    
    # Build and start backend
    docker-compose up -d backend
    
    # Wait for backend to be ready
    local max_attempts=30
    local attempt=1
    
    while [ $attempt -le $max_attempts ]; do
        if curl -f -s http://localhost:8000/api/v1/health > /dev/null 2>&1; then
            log_success "Backend is healthy"
            return 0
        fi
        
        log_info "Attempt $attempt/$max_attempts: Backend not ready yet..."
        sleep 10
        attempt=$((attempt + 1))
    done
    
    log_error "Backend failed to become healthy"
    log_info "Backend logs:"
    docker-compose logs --tail=20 backend
    return 1
}

# Test frontend build and startup
test_frontend_deployment() {
    log_info "Testing frontend deployment..."
    
    # Build and start frontend
    docker-compose up -d frontend
    
    # Wait for frontend to be ready
    local max_attempts=20
    local attempt=1
    
    while [ $attempt -le $max_attempts ]; do
        if curl -f -s http://localhost:3000/health > /dev/null 2>&1; then
            log_success "Frontend is healthy"
            return 0
        fi
        
        log_info "Attempt $attempt/$max_attempts: Frontend not ready yet..."
        sleep 10
        attempt=$((attempt + 1))
    done
    
    log_error "Frontend failed to become healthy"
    log_info "Frontend logs:"
    docker-compose logs --tail=20 frontend
    return 1
}

# Test database migrations
test_database_migrations() {
    log_info "Testing database migrations..."
    
    # Run migrations
    if ! docker-compose exec -T backend python scripts/test_migrations.py > /dev/null 2>&1; then
        log_error "Database migration tests failed"
        return 1
    fi
    
    log_success "Database migrations are working"
    return 0
}

# Test database health
test_database_health() {
    log_info "Testing database health..."
    
    # Run database health check
    if ! docker-compose exec -T backend python scripts/check_db_health.py > /dev/null 2>&1; then
        log_error "Database health check failed"
        return 1
    fi
    
    log_success "Database health check passed"
    return 0
}

# Test Qdrant integration
test_qdrant_integration() {
    log_info "Testing Qdrant integration..."
    
    # Run Qdrant integration test
    if ! docker-compose exec -T backend python scripts/test_qdrant_integration.py > /dev/null 2>&1; then
        log_error "Qdrant integration test failed"
        return 1
    fi
    
    log_success "Qdrant integration test passed"
    return 0
}

# Test API endpoints
test_api_endpoints() {
    log_info "Testing API endpoints..."
    
    # Test health endpoint
    if ! curl -f -s http://localhost:8000/api/v1/health > /dev/null 2>&1; then
        log_error "Backend health endpoint failed"
        return 1
    fi
    
    # Test API docs
    if ! curl -f -s http://localhost:8000/docs > /dev/null 2>&1; then
        log_error "API documentation endpoint failed"
        return 1
    fi
    
    # Test frontend health
    if ! curl -f -s http://localhost:3000/health > /dev/null 2>&1; then
        log_error "Frontend health endpoint failed"
        return 1
    fi
    
    log_success "API endpoints are working"
    return 0
}

# Cleanup function
cleanup() {
    log_info "Cleaning up test environment..."
    docker-compose down --remove-orphans
    log_success "Cleanup completed"
}

# Main test execution
main() {
    echo -e "${GREEN}🧪 Ponder Deployment Testing Suite${NC}"
    echo "===================================="
    
    # Set trap for cleanup on exit
    trap cleanup EXIT
    
    # Run tests
    run_test "Prerequisites Check" "check_prerequisites"
    run_test "Docker Configuration" "test_docker_config"
    run_test "Database Setup" "test_database_setup"
    run_test "Backend Deployment" "test_backend_deployment"
    run_test "Database Migrations" "test_database_migrations"
    run_test "Database Health" "test_database_health"
    run_test "Qdrant Integration" "test_qdrant_integration"
    run_test "Frontend Deployment" "test_frontend_deployment"
    run_test "API Endpoints" "test_api_endpoints"
    
    # Summary
    echo ""
    log_info "📊 Test Summary:"
    echo "==================="
    log_info "Tests passed: $TESTS_PASSED/$TESTS_TOTAL"
    
    if [ $TESTS_PASSED -eq $TESTS_TOTAL ]; then
        log_success "🎉 All deployment tests passed!"
        echo ""
        log_info "🌐 Application is ready at:"
        log_info "   Frontend: http://localhost:3000"
        log_info "   Backend API: http://localhost:8000"
        log_info "   API Docs: http://localhost:8000/docs"
        log_info "   Qdrant: http://localhost:6333/dashboard"
        return 0
    else
        log_error "❌ $((TESTS_TOTAL - TESTS_PASSED)) tests failed!"
        echo ""
        log_info "📋 Troubleshooting:"
        log_info "   View logs: docker-compose logs [service]"
        log_info "   Check status: docker-compose ps"
        log_info "   Restart: docker-compose restart [service]"
        return 1
    fi
}

# Handle script arguments
case "${1:-test}" in
    "test")
        main
        ;;
    "cleanup")
        cleanup
        ;;
    *)
        echo "Usage: $0 {test|cleanup}"
        exit 1
        ;;
esac