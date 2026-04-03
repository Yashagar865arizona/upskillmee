# Backend Scripts

This directory contains utility scripts for maintaining and deploying the Ponder backend.

## Directory Structure

```
scripts/
├── deployment/          # Deployment-related scripts
│   ├── deploy_backend.sh    # Main deployment script
│   └── setup_ssl.sh         # SSL certificate setup
└── maintenance/         # Database and system maintenance
    ├── check_db.py          # Database content checker
    ├── clear_chat_data.py   # Chat data cleanup utility
    └── run_migration.py     # Database migration runner
```

## Deployment Scripts

### deploy_backend.sh

Automated deployment script for the backend application.

**Usage:**
```bash
cd backend/scripts/deployment
./deploy_backend.sh
```

**What it does:**
- Pulls latest code from git repository
- Activates virtual environment
- Installs/updates dependencies
- Restarts systemd services (uvicorn, nginx)
- Tests health endpoint

**Prerequisites:**
- Git repository setup
- Virtual environment (venv or .venv)
- Systemd services configured
- Proper permissions for service restart

### setup_ssl.sh

SSL certificate setup using Let's Encrypt and Certbot.

**Usage:**
```bash
cd backend/scripts/deployment
sudo DOMAIN=your-domain.com EMAIL=your-email@domain.com ./setup_ssl.sh
```

**Environment Variables:**
- `DOMAIN`: Your domain name (default: api.ponder.school)
- `EMAIL`: Email for Let's Encrypt registration (default: admin@ponder.school)

**What it does:**
- Installs Nginx and Certbot
- Configures Nginx reverse proxy
- Obtains SSL certificate from Let's Encrypt
- Tests HTTPS endpoint

## Maintenance Scripts

### check_db.py

Database content inspection utility.

**Usage:**
```bash
cd backend
python scripts/maintenance/check_db.py
```

**What it does:**
- Connects to the database using DATABASE_URL
- Shows record counts for main tables
- Displays sample records

**Prerequisites:**
- `.env.development` file with DATABASE_URL
- Database connection access

### clear_chat_data.py

Safe chat data cleanup utility.

**Usage:**
```bash
cd backend
python scripts/maintenance/clear_chat_data.py
```

**What it does:**
- Prompts for confirmation before deletion
- Safely removes chat-related data
- Respects foreign key constraints
- Provides detailed logging

**Warning:** This permanently deletes chat data. Use with caution.

### run_migration.py

Database migration runner for schema updates.

**Usage:**
```bash
cd backend
python scripts/maintenance/run_migration.py
```

**What it does:**
- Runs specific database migrations
- Handles schema updates safely
- Provides rollback on errors
- Logs migration progress

## Prerequisites

### Environment Setup

1. **Environment Variables**: Ensure `.env.development` exists with:
   ```
   DATABASE_URL=postgresql://user:password@localhost/ponder
   ```

2. **Virtual Environment**: Create and activate:
   ```bash
   python -m venv venv
   source venv/bin/activate  # Linux/Mac
   # or
   venv\Scripts\activate     # Windows
   ```

3. **Dependencies**: Install required packages:
   ```bash
   pip install -r requirements.txt
   ```

### System Services (for deployment)

1. **Uvicorn Service** (`/etc/systemd/system/uvicorn.service`):
   ```ini
   [Unit]
   Description=Uvicorn instance to serve Ponder API
   After=network.target

   [Service]
   User=your-user
   Group=your-group
   WorkingDirectory=/path/to/ponder/backend
   Environment="PATH=/path/to/ponder/backend/venv/bin"
   ExecStart=/path/to/ponder/backend/venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000
   Restart=always

   [Install]
   WantedBy=multi-user.target
   ```

2. **Enable Services**:
   ```bash
   sudo systemctl daemon-reload
   sudo systemctl enable uvicorn
   sudo systemctl start uvicorn
   ```

## Security Notes

- Scripts that require sudo access are clearly marked
- Database operations include confirmation prompts
- SSL setup uses secure defaults
- Environment variables are loaded from secure files

## Troubleshooting

### Common Issues

1. **Permission Denied**: Ensure scripts are executable:
   ```bash
   chmod +x backend/scripts/deployment/*.sh
   ```

2. **Database Connection**: Check DATABASE_URL in environment file

3. **Service Not Found**: Ensure systemd services are properly configured

4. **SSL Certificate Issues**: Check domain DNS and firewall settings

### Logs

- Deployment logs: Check systemd service logs
  ```bash
  sudo journalctl -u uvicorn -f
  ```

- Database logs: Check PostgreSQL logs
- Nginx logs: `/var/log/nginx/error.log`

## Contributing

When adding new scripts:

1. Follow the existing directory structure
2. Include proper error handling and logging
3. Add documentation to this README
4. Test scripts in development environment first
5. Use environment variables for configuration