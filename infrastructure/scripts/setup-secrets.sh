#!/bin/bash
# Script to help set up GitHub Actions secrets for CI/CD pipeline

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

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

echo -e "${GREEN}🔐 GitHub Actions Secrets Setup Guide${NC}"
echo "========================================"
echo ""

log_info "This script will guide you through setting up the required secrets for the CI/CD pipeline."
log_warning "You'll need to manually add these secrets to your GitHub repository settings."
echo ""

# Required secrets
declare -A SECRETS=(
    ["CONTAINER_REGISTRY"]="Container registry URL (e.g., ghcr.io, docker.io)"
    ["REGISTRY_USERNAME"]="Container registry username"
    ["REGISTRY_PASSWORD"]="Container registry password/token"
    ["STAGING_HOST"]="Staging server hostname or IP"
    ["STAGING_USER"]="SSH username for staging server"
    ["STAGING_SSH_KEY"]="Private SSH key for staging server access"
    ["STAGING_API_URL"]="Staging API URL (e.g., https://staging-api.yourapp.com)"
    ["PRODUCTION_HOST"]="Production server hostname or IP"
    ["PRODUCTION_USER"]="SSH username for production server"
    ["PRODUCTION_SSH_KEY"]="Private SSH key for production server access"
    ["PRODUCTION_API_URL"]="Production API URL (e.g., https://api.yourapp.com)"
    ["PRODUCTION_URL"]="Production frontend URL (e.g., https://yourapp.com)"
    ["SLACK_WEBHOOK_URL"]="Slack webhook URL for notifications (optional)"
)

# Optional secrets
declare -A OPTIONAL_SECRETS=(
    ["CODECOV_TOKEN"]="Codecov token for coverage reporting"
    ["SONAR_TOKEN"]="SonarCloud token for code quality analysis"
    ["SENTRY_DSN"]="Sentry DSN for error tracking"
    ["DATADOG_API_KEY"]="Datadog API key for monitoring"
)

log_info "Required Secrets:"
echo "=================="
for secret in "${!SECRETS[@]}"; do
    echo "• $secret: ${SECRETS[$secret]}"
done

echo ""
log_info "Optional Secrets:"
echo "=================="
for secret in "${!OPTIONAL_SECRETS[@]}"; do
    echo "• $secret: ${OPTIONAL_SECRETS[$secret]}"
done

echo ""
log_warning "To add these secrets to your GitHub repository:"
echo "1. Go to your repository on GitHub"
echo "2. Click on 'Settings' tab"
echo "3. Click on 'Secrets and variables' > 'Actions'"
echo "4. Click 'New repository secret' for each secret"
echo ""

# Generate SSH key pair for deployment
read -p "Do you want to generate SSH key pairs for deployment? (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    log_info "Generating SSH key pairs..."
    
    mkdir -p ./ssh-keys
    
    # Generate staging key
    ssh-keygen -t ed25519 -f ./ssh-keys/staging_deploy_key -N "" -C "staging-deploy-$(date +%Y%m%d)"
    log_success "Staging SSH key generated: ./ssh-keys/staging_deploy_key"
    
    # Generate production key
    ssh-keygen -t ed25519 -f ./ssh-keys/production_deploy_key -N "" -C "production-deploy-$(date +%Y%m%d)"
    log_success "Production SSH key generated: ./ssh-keys/production_deploy_key"
    
    echo ""
    log_warning "IMPORTANT: Add the public keys to your servers:"
    echo "Staging public key:"
    cat ./ssh-keys/staging_deploy_key.pub
    echo ""
    echo "Production public key:"
    cat ./ssh-keys/production_deploy_key.pub
    echo ""
    
    log_warning "Use the private keys as GitHub secrets:"
    echo "STAGING_SSH_KEY: $(cat ./ssh-keys/staging_deploy_key)"
    echo "PRODUCTION_SSH_KEY: $(cat ./ssh-keys/production_deploy_key)"
    echo ""
    
    log_error "SECURITY: Delete these key files after adding them to GitHub secrets!"
fi

# Generate example environment files
read -p "Do you want to generate example environment files? (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    log_info "Generating example environment files..."
    
    # Staging environment
    cat > .env.staging.example << EOF
# Staging Environment Configuration
ENVIRONMENT=staging
DEBUG=false

# Database
DATABASE_URL=postgresql://user:password@staging-db:5432/ponder_staging
POSTGRES_USER=ponder_user
POSTGRES_PASSWORD=staging_password_change_me
POSTGRES_DB=ponder_staging

# Redis
REDIS_URL=redis://staging-redis:6379

# JWT
JWT_SECRET=staging_jwt_secret_change_me
JWT_ALGORITHM=HS256

# API Keys
OPENAI_API_KEY=your_openai_api_key_here

# External Services
SENTRY_DSN=your_sentry_dsn_here
DATADOG_API_KEY=your_datadog_api_key_here

# Docker Images
BACKEND_IMAGE=your-registry/ponder-backend:staging
FRONTEND_IMAGE=your-registry/ponder-frontend:staging
EOF
    
    # Production environment
    cat > .env.production.example << EOF
# Production Environment Configuration
ENVIRONMENT=production
DEBUG=false

# Database
DATABASE_URL=postgresql://user:password@prod-db:5432/ponder_production
POSTGRES_USER=ponder_user
POSTGRES_PASSWORD=production_password_change_me
POSTGRES_DB=ponder_production

# Redis
REDIS_URL=redis://prod-redis:6379

# JWT
JWT_SECRET=production_jwt_secret_change_me
JWT_ALGORITHM=HS256

# API Keys
OPENAI_API_KEY=your_openai_api_key_here

# External Services
SENTRY_DSN=your_sentry_dsn_here
DATADOG_API_KEY=your_datadog_api_key_here

# Docker Images
BACKEND_IMAGE=your-registry/ponder-backend:latest
FRONTEND_IMAGE=your-registry/ponder-frontend:latest
EOF
    
    log_success "Environment files generated:"
    log_success "• .env.staging.example"
    log_success "• .env.production.example"
    echo ""
    log_warning "Copy these to your servers and update with actual values!"
fi

echo ""
log_info "Next Steps:"
echo "==========="
echo "1. Add all required secrets to GitHub repository settings"
echo "2. Set up your staging and production servers"
echo "3. Configure your container registry"
echo "4. Test the deployment pipeline with a staging deployment"
echo "5. Set up monitoring and alerting"
echo ""

log_success "Setup guide completed!"
log_warning "Remember to keep your secrets secure and rotate them regularly!"