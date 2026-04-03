# CI/CD Pipeline Guide

## Overview

This document describes the Continuous Integration and Continuous Deployment (CI/CD) pipeline for the Ponder application. The pipeline is implemented using GitHub Actions and provides automated testing, security scanning, code quality checks, and deployment capabilities.

## Pipeline Architecture

### Test Pipeline (`.github/workflows/test.yml`)

The test pipeline runs on every push to `main` and `develop` branches, as well as on pull requests. It consists of the following jobs:

#### 1. Backend Tests
- **Environment**: Ubuntu Latest with Python 3.11
- **Services**: PostgreSQL 13, Redis 6
- **Steps**:
  - Install Python dependencies
  - Run database migrations
  - Execute backend tests with coverage
  - Upload coverage reports to Codecov

#### 2. Frontend Tests
- **Environment**: Ubuntu Latest with Node.js 18
- **Steps**:
  - Install npm dependencies
  - Run frontend tests with coverage
  - Upload coverage reports to Codecov

#### 3. Integration Tests
- **Dependencies**: Backend and Frontend tests must pass
- **Environment**: Full stack with PostgreSQL and Redis
- **Steps**:
  - Set up both backend and frontend
  - Run database migrations
  - Start backend server
  - Build frontend
  - Execute integration tests

#### 4. Security Scan
- **Tools Used**:
  - **Bandit**: Python security linter
  - **Safety**: Python dependency vulnerability scanner
  - **Semgrep**: Multi-language static analysis
  - **TruffleHog**: Secret detection
- **Outputs**: Security reports uploaded as artifacts

#### 5. Code Quality
- **Backend Tools**:
  - **Flake8**: Style checking
  - **Black**: Code formatting
  - **isort**: Import sorting
  - **MyPy**: Type checking
- **Frontend Tools**:
  - **ESLint**: JavaScript/TypeScript linting
  - **Prettier**: Code formatting

#### 6. Test Summary
- Aggregates results from all jobs
- Provides comprehensive status report
- Runs regardless of individual job failures

### Deployment Pipeline (`.github/workflows/deploy.yml`)

The deployment pipeline handles automated deployments to staging and production environments.

#### Staging Deployment
- **Trigger**: Automatic on push to `main` branch
- **Steps**:
  1. Build and push Docker images to container registry
  2. Deploy to staging server via SSH
  3. Run health checks
  4. Send Slack notifications

#### Production Deployment
- **Trigger**: Manual workflow dispatch only
- **Additional Safety Measures**:
  1. Requires manual approval via GitHub environments
  2. Creates backup before deployment
  3. Comprehensive health checks
  4. Automatic rollback on failure
  5. Creates GitHub release on success

## Setup Instructions

### 1. Repository Secrets

Run the setup script to get guidance on required secrets:

```bash
./infrastructure/scripts/setup-secrets.sh
```

#### Required Secrets:
- `CONTAINER_REGISTRY`: Container registry URL
- `REGISTRY_USERNAME`: Registry username
- `REGISTRY_PASSWORD`: Registry password/token
- `STAGING_HOST`: Staging server hostname
- `STAGING_USER`: SSH username for staging
- `STAGING_SSH_KEY`: Private SSH key for staging
- `STAGING_API_URL`: Staging API URL
- `PRODUCTION_HOST`: Production server hostname
- `PRODUCTION_USER`: SSH username for production
- `PRODUCTION_SSH_KEY`: Private SSH key for production
- `PRODUCTION_API_URL`: Production API URL
- `PRODUCTION_URL`: Production frontend URL
- `SLACK_WEBHOOK_URL`: Slack notifications (optional)

#### Optional Secrets:
- `CODECOV_TOKEN`: Coverage reporting
- `SONAR_TOKEN`: Code quality analysis
- `SENTRY_DSN`: Error tracking
- `DATADOG_API_KEY`: Monitoring

### 2. GitHub Environments

Set up GitHub environments for deployment protection:

1. Go to repository Settings → Environments
2. Create `staging` environment
3. Create `production` environment with protection rules:
   - Required reviewers
   - Deployment branches (main only)
   - Environment secrets

### 3. Server Setup

#### Staging Server
```bash
# Install Docker and Docker Compose
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh

# Create deployment directory
sudo mkdir -p /opt/ponder
sudo chown $USER:$USER /opt/ponder
cd /opt/ponder

# Clone repository (or copy deployment files)
git clone https://github.com/your-org/ponder.git .

# Set up environment
cp .env.staging.example .env
# Edit .env with actual values

# Add SSH public key to authorized_keys
echo "your-staging-public-key" >> ~/.ssh/authorized_keys
```

#### Production Server
Similar setup as staging, but with production configuration.

### 4. Container Registry

Set up a container registry (GitHub Container Registry recommended):

```bash
# Login to GitHub Container Registry
echo $GITHUB_TOKEN | docker login ghcr.io -u USERNAME --password-stdin

# Or use Docker Hub
echo $DOCKER_PASSWORD | docker login -u USERNAME --password-stdin
```

## Usage

### Running Tests Locally

```bash
# Backend tests
cd backend
python -m pytest tests/ -v

# Frontend tests
cd frontend
npm test

# Integration tests
python test_websocket_integration.py
```

### Manual Deployment

#### Staging Deployment
Staging deployments happen automatically on push to `main`. To trigger manually:

1. Go to Actions tab in GitHub
2. Select "Deploy" workflow
3. Click "Run workflow"
4. Select "staging" environment

#### Production Deployment
Production deployments require manual approval:

1. Go to Actions tab in GitHub
2. Select "Deploy" workflow
3. Click "Run workflow"
4. Select "production" environment
5. Approve the deployment in the environment protection rules

### Monitoring Deployments

#### Health Checks
The pipeline includes automated health checks:
- API endpoint health (`/api/v1/health`)
- Frontend health (`/health`)
- Database connectivity
- Service availability

#### Notifications
Slack notifications are sent for:
- Deployment start/completion
- Deployment failures
- Production deployments (with special alerts)

#### Rollback Procedure
If a production deployment fails:
1. Automatic rollback is triggered
2. Previous version is restored
3. Notifications are sent
4. Manual verification required

## Security Features

### Automated Security Scanning
- **Dependency Vulnerabilities**: Safety checks Python packages
- **Code Security**: Bandit scans for security issues
- **Secret Detection**: TruffleHog prevents secret leaks
- **Static Analysis**: Semgrep finds security patterns

### Deployment Security
- **SSH Key Authentication**: Secure server access
- **Environment Isolation**: Separate staging/production
- **Secret Management**: GitHub secrets for sensitive data
- **Backup Before Deploy**: Automatic backups before production changes

### Access Control
- **Branch Protection**: Only main branch can deploy
- **Required Reviews**: Production requires approval
- **Environment Secrets**: Separate secrets per environment
- **Audit Trail**: All deployments logged

## Troubleshooting

### Common Issues

#### Test Failures
1. Check test logs in GitHub Actions
2. Run tests locally to reproduce
3. Check database/service connectivity
4. Verify environment variables

#### Deployment Failures
1. Check deployment logs
2. Verify server connectivity
3. Check Docker image availability
4. Validate environment configuration

#### Security Scan Failures
1. Review security reports in artifacts
2. Fix identified vulnerabilities
3. Update dependencies
4. Remove detected secrets

### Getting Help

1. Check the logs in GitHub Actions
2. Review the deployment guide: `infrastructure/DEPLOYMENT_GUIDE.md`
3. Run health checks: `./infrastructure/scripts/deploy.sh health`
4. Contact the development team

## Best Practices

### Development Workflow
1. Create feature branch from `develop`
2. Write tests for new features
3. Ensure all tests pass locally
4. Create pull request to `develop`
5. Merge to `main` triggers staging deployment
6. Manual production deployment after validation

### Security Practices
1. Rotate secrets regularly
2. Use least privilege access
3. Monitor security scan results
4. Keep dependencies updated
5. Review deployment logs

### Monitoring
1. Set up alerts for deployment failures
2. Monitor application health post-deployment
3. Track deployment frequency and success rate
4. Review security scan trends

## Maintenance

### Regular Tasks
- [ ] Update GitHub Actions versions quarterly
- [ ] Rotate SSH keys and secrets annually
- [ ] Review and update security scanning tools
- [ ] Test disaster recovery procedures
- [ ] Update documentation

### Monitoring
- [ ] Check deployment success rates
- [ ] Review security scan results
- [ ] Monitor test execution times
- [ ] Track coverage trends

This CI/CD pipeline provides a robust foundation for automated testing, security scanning, and deployment while maintaining security and reliability standards.