#!/bin/bash
# Configuration validation script for Ponder Docker setup

set -e

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

# Check if Docker is available
check_docker() {
    log_info "Checking Docker installation..."
    
    if ! command -v docker &> /dev/null; then
        log_error "Docker is not installed or not in PATH"
        return 1
    fi
    
    if ! docker info &> /dev/null; then
        log_warning "Docker daemon is not running (this is OK for configuration validation)"
        return 0
    fi
    
    log_success "Docker is available and running"
}

# Check if Docker Compose is available
check_docker_compose() {
    log_info "Checking Docker Compose installation..."
    
    if ! command -v docker-compose &> /dev/null; then
        log_error "Docker Compose is not installed or not in PATH"
        return 1
    fi
    
    log_success "Docker Compose is available"
}

# Validate Docker Compose configuration
validate_compose_config() {
    log_info "Validating Docker Compose configuration..."
    
    # Create temporary environment file for validation
    if [[ ! -f ".env" ]]; then
        log_info "Creating temporary .env file for validation..."
        cp .env.sample .env
        TEMP_ENV_CREATED=true
    fi
    
    # Validate configuration
    if docker-compose config --quiet; then
        log_success "Docker Compose configuration is valid"
    else
        log_error "Docker Compose configuration has errors"
        return 1
    fi
    
    # Clean up temporary file
    if [[ "$TEMP_ENV_CREATED" == "true" ]]; then
        rm .env
        log_info "Removed temporary .env file"
    fi
}

# Check required files
check_required_files() {
    log_info "Checking required files..."
    
    local required_files=(
        "docker-compose.yml"
        "docker-compose.override.yml"
        ".env.production"
        ".env.development"
        ".env.sample"
        "nginx/conf.d/default.conf"
        "postgres/init/01-init.sql"
        "monitoring/prometheus.yml"
        "../backend/Dockerfile"
        "../frontend/Dockerfile"
    )
    
    local missing_files=()
    
    for file in "${required_files[@]}"; do
        if [[ ! -f "$file" ]]; then
            missing_files+=("$file")
        fi
    done
    
    if [[ ${#missing_files[@]} -eq 0 ]]; then
        log_success "All required files are present"
    else
        log_error "Missing required files:"
        for file in "${missing_files[@]}"; do
            echo "  - $file"
        done
        return 1
    fi
}

# Check Dockerfile syntax
check_dockerfiles() {
    log_info "Checking Dockerfile syntax..."
    
    # If Docker is not available, do basic syntax checks
    if ! docker info &> /dev/null; then
        log_warning "Docker daemon not available, performing basic syntax checks..."
        
        # Check if Dockerfiles exist and have basic structure
        if [[ -f "../backend/Dockerfile" ]] && grep -q "FROM" "../backend/Dockerfile"; then
            log_success "Backend Dockerfile exists and has basic structure"
        else
            log_error "Backend Dockerfile missing or invalid"
            return 1
        fi
        
        if [[ -f "../frontend/Dockerfile" ]] && grep -q "FROM" "../frontend/Dockerfile"; then
            log_success "Frontend Dockerfile exists and has basic structure"
        else
            log_error "Frontend Dockerfile missing or invalid"
            return 1
        fi
        
        return 0
    fi
    
    # Full Docker build test if Docker is available
    # Check backend Dockerfile
    if docker build --no-cache -f ../backend/Dockerfile -t ponder-backend-test ../backend --target development > /dev/null 2>&1; then
        log_success "Backend Dockerfile syntax is valid"
        docker rmi ponder-backend-test > /dev/null 2>&1 || true
    else
        log_error "Backend Dockerfile has syntax errors"
        return 1
    fi
    
    # Check frontend Dockerfile
    if docker build --no-cache -f ../frontend/Dockerfile -t ponder-frontend-test ../frontend --target development > /dev/null 2>&1; then
        log_success "Frontend Dockerfile syntax is valid"
        docker rmi ponder-frontend-test > /dev/null 2>&1 || true
    else
        log_error "Frontend Dockerfile has syntax errors"
        return 1
    fi
}

# Check network configuration
check_network_config() {
    log_info "Checking network configuration..."
    
    # Extract network configuration from docker-compose.yml
    if grep -q "ponder-network" docker-compose.yml; then
        log_success "Custom network configuration found"
    else
        log_warning "No custom network configuration found"
    fi
}

# Check volume configuration
check_volume_config() {
    log_info "Checking volume configuration..."
    
    local expected_volumes=(
        "postgres_data"
        "redis_data"
        "qdrant_data"
        "backend_logs"
        "nginx_logs"
    )
    
    for volume in "${expected_volumes[@]}"; do
        if grep -q "$volume:" docker-compose.yml; then
            log_success "Volume $volume is configured"
        else
            log_warning "Volume $volume is not configured"
        fi
    done
}

# Check health check configuration
check_health_checks() {
    log_info "Checking health check configuration..."
    
    local services_with_health_checks=(
        "backend"
        "frontend"
        "db"
        "redis"
        "nginx"
    )
    
    for service in "${services_with_health_checks[@]}"; do
        # Check both Docker Compose healthcheck and Dockerfile HEALTHCHECK
        if grep -A 20 "^  $service:" docker-compose.yml | grep -q "healthcheck:" || \
           grep -q "HEALTHCHECK" "../${service}/Dockerfile" 2>/dev/null || \
           ([ "$service" = "backend" ] && grep -q "HEALTHCHECK" "../backend/Dockerfile") || \
           ([ "$service" = "frontend" ] && grep -q "HEALTHCHECK" "../frontend/Dockerfile"); then
            log_success "Health check configured for $service"
        else
            log_warning "No health check configured for $service"
        fi
    done
}

# Check security configuration
check_security_config() {
    log_info "Checking security configuration..."
    
    # Check for non-root user configuration
    if grep -q "USER " ../backend/Dockerfile && grep -q "USER " ../frontend/Dockerfile; then
        log_success "Non-root users configured in Dockerfiles"
    else
        log_warning "Non-root users may not be properly configured"
    fi
    
    # Check for resource limits
    if grep -q "resources:" docker-compose.yml; then
        log_success "Resource limits configured"
    else
        log_warning "No resource limits configured"
    fi
    
    # Check for restart policies
    if grep -q "restart:" docker-compose.yml; then
        log_success "Restart policies configured"
    else
        log_warning "No restart policies configured"
    fi
}

# Main validation function
main() {
    echo -e "${GREEN}🔍 Ponder Docker Configuration Validation${NC}"
    echo "=========================================="
    
    local validation_passed=true
    
    # Run all checks
    check_docker || validation_passed=false
    check_docker_compose || validation_passed=false
    check_required_files || validation_passed=false
    validate_compose_config || validation_passed=false
    check_dockerfiles || validation_passed=false
    check_network_config
    check_volume_config
    check_health_checks
    check_security_config
    
    echo
    if [[ "$validation_passed" == "true" ]]; then
        log_success "🎉 All critical validations passed!"
        echo -e "${GREEN}Your Docker configuration is ready for deployment.${NC}"
    else
        log_error "❌ Some critical validations failed!"
        echo -e "${RED}Please fix the errors before deploying.${NC}"
        exit 1
    fi
    
    echo
    echo -e "${BLUE}Next steps:${NC}"
    echo "1. Copy .env.development to .env for local development"
    echo "2. Copy .env.production to .env for production deployment"
    echo "3. Update environment variables with your actual values"
    echo "4. Generate secure secrets with: ./scripts/generate-secrets.sh"
    echo "5. Deploy with: ./scripts/deploy.sh"
}

# Run validation
main "$@"