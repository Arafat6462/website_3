#!/bin/bash
# =============================================================================
# DigitalOcean Server Setup Script
# =============================================================================
# Run this ONCE on your DigitalOcean droplet
# Usage: bash server_setup.sh
# =============================================================================

set -e

echo "🚀 Starting DigitalOcean Server Setup for E-Commerce Backend..."
echo "================================================================"

# -----------------------------------------------------------------------------
# 1. Update system
# -----------------------------------------------------------------------------
echo ""
echo "📦 Step 1/10: Updating system packages..."
sudo apt update
sudo apt upgrade -y

# -----------------------------------------------------------------------------
# 2. Install Docker
# -----------------------------------------------------------------------------
echo ""
echo "🐳 Step 2/10: Installing Docker..."
sudo apt install -y apt-transport-https ca-certificates curl software-properties-common

curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg
echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

sudo apt update
sudo apt install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

# Add user to docker group
sudo usermod -aG docker $USER
echo "✓ Docker installed"

# -----------------------------------------------------------------------------
# 3. Install Git
# -----------------------------------------------------------------------------
echo ""
echo "📥 Step 3/10: Installing Git..."
sudo apt install -y git
echo "✓ Git installed"

# -----------------------------------------------------------------------------
# 4. Setup application directory
# -----------------------------------------------------------------------------
echo ""
echo "📁 Step 4/10: Setting up application directory..."
sudo mkdir -p /opt/ecommerce
sudo chown $USER:$USER /opt/ecommerce
echo "✓ Directory created: /opt/ecommerce"

# -----------------------------------------------------------------------------
# 5. Setup SSL with Let's Encrypt
# -----------------------------------------------------------------------------
echo ""
echo "🔒 Step 5/10: Installing Certbot for SSL..."
sudo apt install -y certbot python3-certbot-nginx
echo "✓ Certbot installed"

# -----------------------------------------------------------------------------
# 6. Configure Nginx
# -----------------------------------------------------------------------------
echo ""
echo "⚙️  Step 6/10: Configuring Nginx..."

# Nginx should already be installed, but let's make sure
sudo apt install -y nginx

# Create nginx configuration
sudo tee /etc/nginx/sites-available/ecommerce > /dev/null << 'EOF'
# HTTP - Redirect to HTTPS
server {
    listen 80;
    server_name ecom.arafat2.me 165.22.217.133;
    
    # Let's Encrypt challenge
    location /.well-known/acme-challenge/ {
        root /var/www/html;
    }
    
    location / {
        return 301 https://$server_name$request_uri;
    }
}

# HTTPS - Main application
server {
    listen 443 ssl http2;
    server_name ecom.arafat2.me;

    # SSL Configuration (will be added after certbot)
    ssl_certificate /etc/letsencrypt/live/ecom.arafat2.me/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/ecom.arafat2.me/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;

    # Security Headers
    add_header X-Frame-Options "DENY" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;

    # Client upload size
    client_max_body_size 10M;

    # Proxy to Docker container
    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_redirect off;
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }

    # Static files
    location /static/ {
        alias /opt/ecommerce/staticfiles/;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }

    # Media files
    location /media/ {
        alias /opt/ecommerce/media/;
        expires 7d;
        add_header Cache-Control "public";
    }
}
EOF

# Enable site
sudo ln -sf /etc/nginx/sites-available/ecommerce /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default
echo "✓ Nginx configured"

# -----------------------------------------------------------------------------
# 7. Get SSL Certificate
# -----------------------------------------------------------------------------
echo ""
echo "🔐 Step 7/10: Getting SSL certificate..."
echo "⚠️  Make sure DNS A record for ecom.arafat2.me points to 165.22.217.133"
read -p "Press ENTER when DNS is configured..."

# Stop nginx to free port 80
sudo systemctl stop nginx

# Get certificate
sudo certbot certonly --standalone -d ecom.arafat2.me --non-interactive --agree-tos --email arafat6462@gmail.com || {
    echo "⚠️  SSL certificate failed. You can run this later:"
    echo "    sudo certbot certonly --standalone -d ecom.arafat2.me"
}

# Start nginx
sudo nginx -t && sudo systemctl start nginx
sudo systemctl enable nginx
echo "✓ SSL configured"

# -----------------------------------------------------------------------------
# 8. Setup firewall
# -----------------------------------------------------------------------------
echo ""
echo "🔥 Step 8/10: Configuring firewall..."
sudo ufw allow OpenSSH
sudo ufw allow 'Nginx Full'
sudo ufw --force enable
echo "✓ Firewall configured"

# -----------------------------------------------------------------------------
# 9. Setup directories
# -----------------------------------------------------------------------------
echo ""
echo "📂 Step 9/10: Creating application directories..."
mkdir -p /opt/ecommerce/logs
mkdir -p /opt/ecommerce/staticfiles
mkdir -p /opt/ecommerce/media
echo "✓ Directories created"

# -----------------------------------------------------------------------------
# 10. Setup log rotation
# -----------------------------------------------------------------------------
echo ""
echo "📋 Step 10/10: Setting up log rotation..."
sudo tee /etc/logrotate.d/ecommerce > /dev/null << 'EOF'
/opt/ecommerce/logs/*.log {
    daily
    missingok
    rotate 14
    compress
    delaycompress
    notifempty
    create 0640 arafat arafat
    sharedscripts
}
EOF
echo "✓ Log rotation configured"

# -----------------------------------------------------------------------------
# Completion
# -----------------------------------------------------------------------------
echo ""
echo "================================================================"
echo "✅ Server setup complete!"
echo "================================================================"
echo ""
echo "📋 Next steps:"
echo ""
echo "1. Clone your repository:"
echo "   cd /opt/ecommerce"
echo "   git clone https://github.com/YOUR_USERNAME/YOUR_REPO.git ."
echo ""
echo "2. Edit .env.production file with your secrets"
echo ""
echo "3. Login to GitHub Container Registry:"
echo "   docker login ghcr.io -u YOUR_GITHUB_USERNAME"
echo ""
echo "4. Pull and start containers:"
echo "   docker compose -f docker-compose.prod.yml up -d"
echo ""
echo "5. Run initial migrations:"
echo "   docker compose -f docker-compose.prod.yml exec web python manage.py migrate"
echo ""
echo "6. Create superuser:"
echo "   docker compose -f docker-compose.prod.yml exec web python manage.py createsuperuser"
echo ""
echo "7. Test: https://ecom.arafat2.me/api/v1/health/"
echo ""
echo "🔑 GitHub Secrets to add (for CI/CD):"
echo "   DO_HOST: 165.22.217.133"
echo "   DO_USERNAME: arafat"
echo "   DO_SSH_KEY: (contents of ~/.ssh/id_rsa)"
echo ""
