# Ponder Test Environment Setup Guide

This document provides comprehensive instructions for setting up a test environment for the Ponder application, including both the backend (AWS EC2) and frontend (Vercel) components.

## Overview

The test environment consists of:
- A separate EC2 instance for the backend API
- A separate Vercel deployment for the frontend
- Separate environment configurations for test settings

This setup allows you to test changes without affecting the production environment.

## 1. Backend Test Environment (AWS EC2)

### 1.1 Launch an EC2 Instance

1. Log in to the AWS Management Console
2. Navigate to EC2 service
3. Click "Launch Instance"
4. Choose an Amazon Machine Image (AMI)
   - Recommended: Ubuntu Server 22.04 LTS
5. Choose an Instance Type
   - Recommended: t2.micro (sufficient for testing)
6. Configure Instance Details
   - Default VPC is fine for testing
7. Add Storage
   - Default 8GB is sufficient
8. Add Tags
   - Key: Name, Value: ponder-test
9. Configure Security Group
   - Allow SSH (port 22) from your IP
   - Allow HTTP (port 80) from anywhere
   - Allow HTTPS (port 443) from anywhere
   - Allow Custom TCP (port 8000) from anywhere (for direct API access)
10. Review and Launch
11. Create or select an existing key pair
12. Launch Instance

### 1.2 Connect to the EC2 Instance

```bash
ssh -i /path/to/your-key.pem ubuntu@your-test-ec2-ip
```

Replace `/path/to/your-key.pem` with the path to your key file and `your-test-ec2-ip` with the public IP of your EC2 instance.

### 1.3 Set Up the Backend Environment

Once connected to the EC2 instance, run the following commands:

```bash
# Update system packages
sudo apt update
sudo apt upgrade -y

# Install required packages
sudo apt install -y python3-pip python3-venv postgresql postgresql-contrib nginx git

# Set up PostgreSQL
sudo -u postgres psql -c "CREATE USER ubuntu WITH PASSWORD 'password';"
sudo -u postgres psql -c "CREATE DATABASE ponder_test;"
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE ponder_test TO ubuntu;"

# Clone repository (replace with your actual repository URL)
git clone https://github.com/yourusername/ponder.git ~/ponder

# Navigate to repository
cd ~/ponder

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
cd backend
pip install -r requirements.txt

# Create test environment file
cat > .env.test << EOL
# Test Environment Settings
ENVIRONMENT=test
RESET_DB=false

# Database
DATABASE_URL=postgresql://ubuntu@localhost/ponder_test
DATABASE_BACKUP_DIR=./backups
ANALYTICS_EXPORT_DIR=./analytics

# Data Management
MAX_BACKUP_COUNT=5
BACKUP_RETENTION_DAYS=30

# Security (Test Keys - Not Sensitive)
ADMIN_API_KEY=test-admin-key
JWT_SECRET=test-jwt-secret

# OpenAI
OPENAI_API_KEY=your_openai_api_key_here

# Active AI Model
ACTIVE_MODEL=deepseek-reasoner

# Logging
LOG_LEVEL=INFO
LOG_TO_FILE=true

# Redis
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_PASSWORD=
EOL

# Copy test environment file to .env
cp .env.test .env

# Create systemd service file
sudo bash -c 'cat > /etc/systemd/system/ponder-test.service << EOL
[Unit]
Description=Ponder Test Backend
After=network.target

[Service]
User=ubuntu
WorkingDirectory=/home/ubuntu/ponder/backend
Environment="PATH=/home/ubuntu/ponder/venv/bin"
Environment="ENVIRONMENT=test"
ExecStart=/home/ubuntu/ponder/venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000
Restart=always

[Install]
WantedBy=multi-user.target
EOL'

# Enable and start the service
sudo systemctl daemon-reload
sudo systemctl enable ponder-test
sudo systemctl start ponder-test

# Set up Nginx
sudo bash -c 'cat > /etc/nginx/sites-available/ponder-test << EOL
server {
    listen 80;
    server_name test-api.ponder.school;

    location / {
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
    }
}
EOL'

# Enable Nginx site
sudo ln -s /etc/nginx/sites-available/ponder-test /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx

# Create deployment script
cat > ~/deploy-test.sh << EOL
#!/bin/bash
# Test Environment Deployment Script

echo "Deploying to test environment..."

# Navigate to repository directory
cd ~/ponder

# Pull latest changes
git pull origin main

# Activate virtual environment
source venv/bin/activate

# Install dependencies
cd backend
pip install -r requirements.txt

# Copy test environment file
cp .env.test .env

# Restart the service
sudo systemctl restart ponder-test

echo "Test deployment complete!"
EOL

# Make deployment script executable
chmod +x ~/deploy-test.sh
```

### 1.4 Verify Backend Setup

Check if the service is running:

```bash
sudo systemctl status ponder-test
```

Test the API endpoint:

```bash
curl http://localhost:8000/api/v1/health
```

You should see a response like `{"status":"ok"}`.

## 2. Frontend Test Environment (Vercel)

### 2.1 Create a New Project in Vercel

1. Go to [Vercel Dashboard](https://vercel.com/dashboard)
2. Click "Add New" > "Project"
3. Import your GitHub repository
4. Select the repository containing your Ponder project
5. Configure the project:
   - Framework Preset: Create React App
   - Root Directory: `frontend` (if your frontend code is in a subdirectory)
   - Build Command: `npm run build`
   - Output Directory: `build`
   - Install Command: `npm install`
6. Name the project "ponder-test" or similar

### 2.2 Configure Environment Variables

In the Vercel project settings, add the following environment variables:

- `REACT_APP_ENVIRONMENT`: `test`
- `REACT_APP_API_URL`: `http://your-test-ec2-ip:8000/api/v1` (replace with your EC2 IP)
- `REACT_APP_WS_URL`: `ws://your-test-ec2-ip:8000/api/v1` (replace with your EC2 IP)

If you have a domain set up for your test API, you can use that instead:
- `REACT_APP_API_URL`: `https://test-api.ponder.school/api/v1`
- `REACT_APP_WS_URL`: `wss://test-api.ponder.school/api/v1`

### 2.3 Deploy the Frontend

Click "Deploy" to deploy your test environment.

### 2.4 Set Up Automatic Deployments

1. Go to the "Git" tab in your project settings
2. Under "Production Branch", select "main"
3. Under "Preview Branches", add a new branch pattern: `main`
4. This will create a preview deployment whenever you push to the main branch

### 2.5 Verify Frontend Setup

Access your test frontend at the URL provided by Vercel (e.g., `https://ponder-test.vercel.app`).

## 3. Deploying Updates to the Test Environment

### 3.1 Backend Updates

SSH into the test EC2 instance and run:

```bash
~/deploy-test.sh
```

Or from your local machine:

```bash
ssh -i /path/to/your-key.pem ubuntu@your-test-ec2-ip "~/deploy-test.sh"
```

### 3.2 Frontend Updates

The frontend will automatically update when you push changes to the main branch, thanks to Vercel's automatic deployments.

## 4. Testing Your Changes

1. Make changes to your codebase
2. Push the changes to your repository
3. Deploy the changes to the test environment
4. Access the test frontend at `https://ponder-test.vercel.app`
5. Test all features thoroughly
6. Verify that everything works as expected

## 5. Troubleshooting

### 5.1 Backend Issues

#### Service not starting

Check the service logs:

```bash
sudo journalctl -u ponder-test
```

#### Database connection issues

Verify PostgreSQL is running:

```bash
sudo systemctl status postgresql
```

Check database connection:

```bash
psql -U ubuntu -d ponder_test -c "SELECT 1"
```

#### Nginx issues

Check Nginx configuration:

```bash
sudo nginx -t
```

Check Nginx logs:

```bash
sudo tail -f /var/log/nginx/error.log
```

### 5.2 Frontend Issues

#### API connection issues

- Verify that the backend API is accessible
- Check that the environment variables in Vercel are correctly set
- Check browser console for CORS errors

#### Build failures

Check the build logs in the Vercel dashboard for any errors.

## 6. Moving to Production

Once you've verified that everything works in the test environment, you can deploy to production:

1. SSH into your production EC2 instance:
   ```bash
   ssh -i /path/to/your-key.pem ubuntu@your-production-ec2-ip
   ```

2. Pull the latest changes and restart the service:
   ```bash
   cd ~/ponder
   git pull origin main
   sudo systemctl restart uvicorn.service
   ```

For the frontend, if you're using Vercel for production as well, you can promote the test deployment to production through the Vercel dashboard.

## 7. Environment Configuration

The system uses different environment files for different environments:

- Local development: `.env.development`
- Test environment: `.env.test`
- Production: `.env.production`

The appropriate environment file is loaded based on the `ENVIRONMENT` variable.

## 8. Additional Notes

- The test environment uses a separate database from production, so you can freely test database changes without affecting production data.
- The test environment uses the same codebase as production, so you can test code changes in a realistic environment.
- You can create multiple test environments if needed, just repeat the steps with different EC2 instances and Vercel projects.

## 9. Quick Reference Commands

### Backend Test Environment
```bash
# Check service status
sudo systemctl status ponder-test

# View logs
sudo journalctl -u ponder-test -f

# Restart service
sudo systemctl restart ponder-test

# Deploy updates
~/deploy-test.sh
```

### Database Operations
```bash
# Connect to test database
psql -U ubuntu -d ponder_test

# Check database status
sudo systemctl status postgresql

# Restart PostgreSQL
sudo systemctl restart postgresql
```

### Nginx Operations
```bash
# Test configuration
sudo nginx -t

# Restart Nginx
sudo systemctl restart nginx

# View error logs
sudo tail -f /var/log/nginx/error.log
```