#!/bin/bash
set -e

echo "========================================"
echo "Setting up SSL for Ponder backend..."
echo "========================================"

# Check if running as root or with sudo
if [ "$EUID" -ne 0 ]; then
    echo "This script needs to be run with sudo privileges"
    exit 1
fi

# Variables (customize these)
DOMAIN="${DOMAIN:-api.ponder.school}"
EMAIL="${EMAIL:-admin@ponder.school}"
NGINX_CONFIG_NAME="ponder"

echo "Domain: $DOMAIN"
echo "Email: $EMAIL"

# Install Nginx and Certbot
echo "Installing Nginx and Certbot..."
apt update
apt install -y nginx certbot python3-certbot-nginx

# Check if nginx config exists
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
NGINX_CONFIG_FILE="$SCRIPT_DIR/nginx.conf"

if [ -f "$NGINX_CONFIG_FILE" ]; then
    echo "Copying Nginx configuration..."
    cp "$NGINX_CONFIG_FILE" "/etc/nginx/sites-available/$NGINX_CONFIG_NAME"
else
    echo "Warning: nginx.conf not found at $NGINX_CONFIG_FILE"
    echo "Creating basic Nginx configuration..."
    cat > "/etc/nginx/sites-available/$NGINX_CONFIG_NAME" << EOF
server {
    listen 80;
    server_name $DOMAIN;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }
}
EOF
fi

# Enable the site
echo "Enabling Nginx site..."
ln -sf "/etc/nginx/sites-available/$NGINX_CONFIG_NAME" "/etc/nginx/sites-enabled/"

# Remove default site if it exists
if [ -f "/etc/nginx/sites-enabled/default" ]; then
    rm "/etc/nginx/sites-enabled/default"
fi

# Test Nginx configuration
echo "Testing Nginx configuration..."
nginx -t

# Reload Nginx
echo "Reloading Nginx..."
systemctl reload nginx

# Get SSL certificate
echo "Obtaining SSL certificate for $DOMAIN..."
if certbot --nginx -d "$DOMAIN" --non-interactive --agree-tos --email "$EMAIL"; then
    echo "✅ SSL certificate obtained successfully"
else
    echo "❌ Failed to obtain SSL certificate"
    exit 1
fi

# Reload Nginx again
echo "Reloading Nginx with SSL configuration..."
systemctl reload nginx

# Test the configuration
echo "----------------------------------------"
echo "Testing SSL configuration..."
if curl -f "https://$DOMAIN/api/v1/health" 2>/dev/null; then
    echo "✅ HTTPS endpoint is responding"
else
    echo "❌ HTTPS endpoint is not responding"
fi

echo ""
echo "========================================"
echo "SSL setup completed for $DOMAIN"
echo "========================================"
