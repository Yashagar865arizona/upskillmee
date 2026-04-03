# Ponder Deployment Steps

This document outlines the current deployment process for the Ponder project. The architecture is as follows:

- **WordPress Homepage:** `ponder.school` (Hosted on Hostinger – **no changes needed**)
- **React Frontend:** Deployed via Vercel (served as `ponder.school/app` or via a custom subdomain like `app.ponder.school`)
- **FastAPI Backend API:** Hosted on AWS EC2 (exposed at `api.ponder.school`), managed with a systemd service and Nginx as a reverse proxy.

---

## 1. WordPress Setup (Hostinger)

Your WordPress installation on `ponder.school` remains unchanged. You do not need to perform any updates here.

---

## 2. React Frontend Deployment (Vercel)

Since Vercel handles the frontend, ensure the following:

### A. Configuration in Package.json

In your `/frontend/package.json`, set the `"homepage"` key:
```json
{
  "homepage": "https://ponder.school/app"
}
```

### B. Vercel Configuration

Create or update the `/frontend/vercel.json` file to handle SPA rewrites:
```json
{
  "rewrites": [
    { "source": "/(.*)", "destination": "/index.html" }
  ]
}
```

### C. Vercel Setup Steps

1. **Connect Your Repository:**  
   Use the Vercel dashboard to link the repository and select the `/frontend` folder as the project root.

2. **Build Settings:**  
   - Build Command: `npm run build`  
   - Output Directory: Typically `build`

3. **Custom Domain:**  
   - Add your desired custom domain (e.g., `app.ponder.school`) via Vercel's domain settings.
   - Ensure DNS is set as instructed by Vercel.

---

## 3. FastAPI Backend Deployment (AWS EC2)

Your backend is a FastAPI application running on an AWS EC2 instance. Follow these steps:

### A. EC2 Environment Setup

1. **SSH into the EC2 Instance:**
   ```bash
   ssh -i /path/to/your-key.pem ubuntu@your-ec2-public-ip
   ```

2. **Navigate to the Backend Directory:**
   ```bash
   cd /home/ubuntu/app/backend
   ```

3. **Activate the Virtual Environment & Update Code:**
   ```bash
   source venv/bin/activate
   git pull origin main
   pip install -r requirements.txt
   ```

### B. Deploying with the Deployment Script

Use the deployment script located at `/backend/deploy_backend.sh` to update and restart your backend services:

```bash
#!/usr/bin/env bash
set -e

echo "========================================"
echo "Starting backend deployment on EC2..."
echo "========================================"

# Navigate to the repository directory (assumes the script is in the backend directory)
cd "$(dirname "$0")"

# Pull the latest code
echo "Pulling latest code from remote repository..."
git pull origin main

# Activate the virtual environment and install dependencies
echo "Activating virtual environment and installing dependencies..."
source venv/bin/activate
pip install -r requirements.txt

# Restart the uvicorn service (ensure your systemd service is set up correctly)
echo "Restarting uvicorn.service..."
sudo systemctl restart uvicorn.service

# Restart nginx to update any reverse proxy configurations
echo "Restarting nginx.service..."
sudo systemctl restart nginx.service

# Display service statuses
echo "----------------------------------------"
echo "Uvicorn Service Status:"
sudo systemctl status uvicorn.service --no-pager

echo "----------------------------------------"
echo "Testing FastAPI health endpoint (should return {'status': 'ok'}):"
curl http://127.0.0.1:8000

echo ""
echo "========================================"
echo "Deployment complete. Ensure that DNS for api.ponder.school points to this EC2 instance's public IP."
```

> **Note:** Make this script executable if it isn't already:
> ```bash
> chmod +x deploy_backend.sh
> ```

### C. Systemd Service Configuration

Your backend is managed via systemd. An example service file named `ponder.service` (likely located within your `/backend` folder or installed into `/etc/systemd/system/`) might look like this:

```ini
[Unit]
Description=Ponder FastAPI Application
After=network.target

[Service]
User=ubuntu
Group=ubuntu
WorkingDirectory=/home/ubuntu/app/backend
Environment="PATH=/home/ubuntu/app/venv/bin"
ExecStart=/home/ubuntu/app/venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4

[Install]
WantedBy=multi-user.target
```

After any changes, reload and start your service:
```bash
sudo systemctl daemon-reload
sudo systemctl enable ponder.service
sudo systemctl start ponder.service
```

### D. Nginx Reverse Proxy Configuration

Configure Nginx to forward requests from `api.ponder.school` to your FastAPI backend:

1. **Create an Nginx Config File** (e.g., at `/etc/nginx/sites-available/ponder`):
   ```nginx
   server {
       listen 80;
       server_name api.ponder.school;
       return 301 https://$server_name$request_uri;
   }

   server {
       listen 443 ssl;
       server_name api.ponder.school;

       # SSL configuration (assumes usage of Let's Encrypt)
       ssl_certificate /etc/letsencrypt/live/api.ponder.school/fullchain.pem;
       ssl_certificate_key /etc/letsencrypt/live/api.ponder.school/privkey.pem;
       ssl_protocols TLSv1.2 TLSv1.3;
       ssl_prefer_server_ciphers on;

       location / {
           proxy_pass http://127.0.0.1:8000;
           proxy_http_version 1.1;
           proxy_set_header Upgrade $http_upgrade;
           proxy_set_header Connection "upgrade";
           proxy_set_header Host $host;
           proxy_set_header X-Real-IP $remote_addr;
           proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
           proxy_set_header X-Forwarded-Proto $scheme;
           proxy_read_timeout 300s;
           proxy_connect_timeout 75s;
       }

       gzip on;
       gzip_types text/plain text/css application/json application/javascript text/xml application/xml application/xml+rss text/javascript;
       gzip_min_length 1000;
   }
   ```

2. **Enable and Test the Configuration:**
   ```bash
   sudo ln -s /etc/nginx/sites-available/ponder /etc/nginx/sites-enabled/
   sudo nginx -t
   sudo systemctl restart nginx
   ```

---

## 4. DNS & SSL Considerations

- **DNS:**  
  - `api.ponder.school` must point to your AWS EC2 instance's public IP.
  - The WordPress homepage (`ponder.school`) and frontend (via Vercel) remain as currently set up.

- **SSL Certificates:**  
  - The backend uses Let's Encrypt via Nginx for SSL.
  - Vercel manages SSL for your frontend automatically.

---

## 5. Troubleshooting & Verification

- **Frontend:**  
  - Verify the React app loads at `https://ponder.school/app` (or your configured domain).
  - Use the browser console to confirm that API calls are directed to `https://api.ponder.school`.

- **Backend:**  
  - Test the backend locally on the EC2 instance:
    ```bash
    curl http://127.0.0.1:8000
    ```
  - Check the service status:
    ```bash
    sudo systemctl status uvicorn.service
    ```
  - If issues arise, review the Nginx logs (`/var/log/nginx/`) and systemd logs via `journalctl -u uvicorn.service`.

---

This file now reflects your actual deployment process—frontend via Vercel and backend on AWS EC2 (with systemd and Nginx). Use this guide to deploy future updates without affecting your WordPress homepage.
