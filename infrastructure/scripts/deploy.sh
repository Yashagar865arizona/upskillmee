#!/bin/bash
# Production deployment script for Ponder

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
COMPOSE_FILE="docker-compose.yml"
ENV_FILE=".env"
BACKUP_DIR="./backups"

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

# Check if running as root
check_root() {
    if [[ $EUID -eq 0 ]]; then
        log_error "This script should not be run as root for security reasons"
        exit 1
    fi
}

# Check prerequisites
check_prerequisites() {
    log_info "Checking prerequisites..."
    
    # Check if Docker is installed
    if ! command -v docker &> /dev/null; then
        log_error "Docker is not installed. Please install Docker first."
        exit 1
    fi
    
    # Check if Docker Compose is installed
    if ! command -v docker-compose &> /dev/null; then
        log_error "Docker Compose is not installed. Please install Docker Compose first."
        exit 1
    fi
    
    # Check if environment file exists
    if [[ ! -f "$ENV_FILE" ]]; then
        log_error "Environment file $ENV_FILE not found. Please create it from .env.production template."
        exit 1
    fi
    
    log_success "Prerequisites check passed"
}

# Create backup
create_backup() {
    log_info "Creating backup..."
    
    mkdir -p "$BACKUP_DIR"
    BACKUP_NAME="backup_$(date +%Y%m%d_%H%M%S)"
    
    # Backup database
    if docker-compose ps db | grep -q "Up"; then
        log_info "Backing up database..."
        docker-compose exec -T db pg_dump -U ${POSTGRES_USER} ${POSTGRES_DB} > "$BACKUP_DIR/${BACKUP_NAME}_database.sql"
        log_success "Database backup created: $BACKUP_DIR/${BACKUP_NAME}_database.sql"
    fi
    
    # Backup volumes
    log_info "Backing up volumes..."
    docker run --rm -v ponder_postgres_data:/data -v $(pwd)/$BACKUP_DIR:/backup alpine tar czf /backup/${BACKUP_NAME}_postgres_data.tar.gz -C /data .
    docker run --rm -v ponder_redis_data:/data -v $(pwd)/$BACKUP_DIR:/backup alpine tar czf /backup/${BACKUP_NAME}_redis_data.tar.gz -C /data .
    
    log_success "Backup completed: $BACKUP_NAME"
}

# Deploy application
deploy() {
    log_info "Starting deployment..."
    
    # Pull latest images
    log_info "Pulling latest images..."
    docker-compose pull
    
    # Build images
    log_info "Building images..."
    docker-compose build --no-cache
    
    # Stop services gracefully
    log_info "Stopping services..."
    docker-compose down --timeout 30
    
    # Start services
    log_info "Starting services..."
    docker-compose up -d
    
    # Wait for services to be healthy
    log_info "Waiting for services to be healthy..."
    sleep 30
    
    # Check service health
    check_health
    
    log_success "Deployment completed successfully!"
}

# Check service health
check_health() {
    log_info "Checking service health..."
    
    # Check backend health
    if curl -f http://localhost:8000/api/v1/health > /dev/null 2>&1; then
        log_success "Backend service is healthy"
    else
        log_error "Backend service is not healthy"
        return 1
    fi
    
    # Check frontend health
    if curl -f http://localhost:3000/health > /dev/null 2>&1; then
        log_success "Frontend service is healthy"
    else
        log_error "Frontend service is not healthy"
        return 1
    fi
    
    # Check database
    if docker-compose exec -T db pg_isready -U ${POSTGRES_USER} > /dev/null 2>&1; then
        log_success "Database is healthy"
    else
        log_error "Database is not healthy"
        return 1
    fi
    
    log_success "All services are healthy"
}

# Rollback function
rollback() {
    log_warning "Rolling back to previous version..."
    
    # Stop current services
    docker-compose down --timeout 30
    
    # Restore from backup (implement based on your backup strategy)
    log_info "Restore functionality should be implemented based on your backup strategy"
    
    log_warning "Rollback completed. Please verify services manually."
}

# Cleanup old images and volumes
cleanup() {
    log_info "Cleaning up old Docker images and volumes..."
    
    # Remove unused images
    docker image prune -f
    
    # Remove unused volumes (be careful with this in production)
    # docker volume prune -f
    
    log_success "Cleanup completed"
}

# Main deployment flow
main() {
    echo -e "${GREEN}🚀 Ponder Production Deployment${NC}"
    echo "=================================="
    
    # Load environment variables
    source "$ENV_FILE"
    
    check_root
    check_prerequisites
    
    # Ask for confirmation
    read -p "Are you sure you want to deploy to production? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        log_info "Deployment cancelled"
        exit 0
    fi
    
    # Create backup before deployment
    create_backup
    
    # Deploy
    if deploy; then
        log_success "🎉 Deployment successful!"
        
        # Optional cleanup
        read -p "Do you want to clean up old Docker images? (y/N): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            cleanup
        fi
    else
        log_error "Deployment failed!"
        read -p "Do you want to rollback? (y/N): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            rollback
        fi
        exit 1
    fi
}

# Handle script arguments
case "${1:-deploy}" in
    "deploy")
        main
        ;;
    "health")
        check_health
        ;;
    "backup")
        create_backup
        ;;
    "rollback")
        rollback
        ;;
    "cleanup")
        cleanup
        ;;
    *)
        echo "Usage: $0 {deploy|health|backup|rollback|cleanup}"
        exit 1
        ;;
esac