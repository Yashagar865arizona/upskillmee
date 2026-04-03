#!/bin/bash
# Script to validate CI/CD pipeline configuration

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

echo -e "${GREEN}🔍 CI/CD Pipeline Validation${NC}"
echo "==============================="
echo ""

# Check if we're in the right directory
if [[ ! -f ".github/workflows/test.yml" ]]; then
    log_error "Not in project root directory or GitHub workflows not found"
    exit 1
fi

log_info "Validating GitHub Actions workflows..."

# Validate workflow files
validate_workflow() {
    local workflow_file=$1
    local workflow_name=$2
    
    if [[ -f "$workflow_file" ]]; then
        log_success "$workflow_name workflow file exists"
        
        # Basic YAML syntax check (if yq is available)
        if command -v yq &> /dev/null; then
            if yq eval '.' "$workflow_file" > /dev/null 2>&1; then
                log_success "$workflow_name workflow has valid YAML syntax"
            else
                log_error "$workflow_name workflow has invalid YAML syntax"
                return 1
            fi
        else
            log_warning "yq not available - skipping YAML syntax validation"
        fi
        
        # Check for required jobs
        if grep -q "backend-tests:" "$workflow_file"; then
            log_success "$workflow_name has backend-tests job"
        else
            log_warning "$workflow_name missing backend-tests job"
        fi
        
        if grep -q "frontend-tests:" "$workflow_file"; then
            log_success "$workflow_name has frontend-tests job"
        else
            log_warning "$workflow_name missing frontend-tests job"
        fi
        
    else
        log_error "$workflow_name workflow file not found"
        return 1
    fi
}

# Validate test workflow
validate_workflow ".github/workflows/test.yml" "Test"

# Validate deployment workflow
validate_workflow ".github/workflows/deploy.yml" "Deploy"

echo ""
log_info "Validating deployment scripts..."

# Check deployment scripts
if [[ -f "infrastructure/scripts/deploy.sh" ]]; then
    log_success "Deployment script exists"
    
    if [[ -x "infrastructure/scripts/deploy.sh" ]]; then
        log_success "Deployment script is executable"
    else
        log_warning "Deployment script is not executable"
        chmod +x infrastructure/scripts/deploy.sh
        log_success "Made deployment script executable"
    fi
else
    log_error "Deployment script not found"
fi

# Check secrets setup script
if [[ -f "infrastructure/scripts/setup-secrets.sh" ]]; then
    log_success "Secrets setup script exists"
    
    if [[ -x "infrastructure/scripts/setup-secrets.sh" ]]; then
        log_success "Secrets setup script is executable"
    else
        log_warning "Secrets setup script is not executable"
        chmod +x infrastructure/scripts/setup-secrets.sh
        log_success "Made secrets setup script executable"
    fi
else
    log_error "Secrets setup script not found"
fi

echo ""
log_info "Validating Docker configuration..."

# Check Dockerfiles
if [[ -f "backend/Dockerfile" ]]; then
    log_success "Backend Dockerfile exists"
else
    log_error "Backend Dockerfile not found"
fi

if [[ -f "frontend/Dockerfile" ]]; then
    log_success "Frontend Dockerfile exists"
else
    log_error "Frontend Dockerfile not found"
fi

# Check docker-compose files
if [[ -f "infrastructure/docker-compose.yml" ]]; then
    log_success "Docker Compose file exists"
    
    # Validate docker-compose syntax
    if command -v docker-compose &> /dev/null; then
        if docker-compose -f infrastructure/docker-compose.yml config > /dev/null 2>&1; then
            log_success "Docker Compose file has valid syntax"
        else
            log_error "Docker Compose file has invalid syntax"
        fi
    else
        log_warning "docker-compose not available - skipping syntax validation"
    fi
else
    log_error "Docker Compose file not found"
fi

echo ""
log_info "Validating test configuration..."

# Check backend test configuration
if [[ -f "backend/pytest.ini" ]]; then
    log_success "Backend test configuration exists"
else
    log_warning "Backend test configuration (pytest.ini) not found"
fi

# Check frontend test configuration
if [[ -f "frontend/package.json" ]]; then
    if grep -q '"test"' frontend/package.json; then
        log_success "Frontend test script configured"
    else
        log_warning "Frontend test script not found in package.json"
    fi
else
    log_error "Frontend package.json not found"
fi

# Check test directories
if [[ -d "backend/tests" ]]; then
    log_success "Backend tests directory exists"
    
    test_count=$(find backend/tests -name "test_*.py" | wc -l)
    log_info "Found $test_count backend test files"
else
    log_error "Backend tests directory not found"
fi

if [[ -d "frontend/src" ]]; then
    test_count=$(find frontend/src -name "*.test.js" -o -name "*.test.jsx" -o -name "*.test.ts" -o -name "*.test.tsx" | wc -l)
    if [[ $test_count -gt 0 ]]; then
        log_success "Frontend tests found ($test_count files)"
    else
        log_warning "No frontend test files found"
    fi
else
    log_error "Frontend src directory not found"
fi

echo ""
log_info "Validating security configuration..."

# Check for security tools configuration
security_tools=("bandit" "safety" "semgrep")
for tool in "${security_tools[@]}"; do
    if grep -q "$tool" .github/workflows/test.yml; then
        log_success "$tool security scanning configured"
    else
        log_warning "$tool security scanning not configured"
    fi
done

# Check for secret detection
if grep -q "trufflehog" .github/workflows/test.yml; then
    log_success "Secret detection configured"
else
    log_warning "Secret detection not configured"
fi

echo ""
log_info "Validating documentation..."

# Check for CI/CD documentation
if [[ -f "docs/CI_CD_GUIDE.md" ]]; then
    log_success "CI/CD documentation exists"
else
    log_warning "CI/CD documentation not found"
fi

# Check for deployment guide
if [[ -f "infrastructure/DEPLOYMENT_GUIDE.md" ]]; then
    log_success "Deployment guide exists"
else
    log_warning "Deployment guide not found"
fi

echo ""
log_info "Validation Summary"
echo "=================="

# Count issues
error_count=$(grep -c "❌" <<< "$(log_error "test" 2>&1)" || echo "0")
warning_count=$(grep -c "⚠️" <<< "$(log_warning "test" 2>&1)" || echo "0")

if [[ $error_count -eq 0 ]]; then
    log_success "No critical issues found!"
    
    if [[ $warning_count -eq 0 ]]; then
        log_success "CI/CD pipeline is fully configured and ready!"
    else
        log_warning "CI/CD pipeline is functional but has $warning_count warnings"
    fi
    
    echo ""
    log_info "Next steps:"
    echo "1. Set up GitHub repository secrets using: ./infrastructure/scripts/setup-secrets.sh"
    echo "2. Configure GitHub environments (staging, production)"
    echo "3. Set up staging and production servers"
    echo "4. Test the pipeline with a staging deployment"
    echo "5. Review the CI/CD guide: docs/CI_CD_GUIDE.md"
    
else
    log_error "Found $error_count critical issues that need to be fixed"
    exit 1
fi

echo ""
log_success "CI/CD validation completed!"