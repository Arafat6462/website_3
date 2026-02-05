#!/bin/bash
# =============================================================================
# FIRST TIME SERVER SETUP
# =============================================================================
# Run this ONCE on your DigitalOcean server before GitHub Actions can deploy
# SSH to server: ssh arafat@ecom.arafat2.me
# Then run: bash <(curl -s https://raw.githubusercontent.com/Arafat6462/website_3/master/FIRST_TIME_SETUP.sh)
# =============================================================================

set -e

echo "🚀 First Time Server Setup for ecom.arafat2.me"
echo "================================================"

# -----------------------------------------------------------------------------
# 1. Create application directory
# -----------------------------------------------------------------------------
echo "📁 Creating application directory..."
sudo mkdir -p /opt/ecommerce
sudo chown -R $USER:$USER /opt/ecommerce
cd /opt/ecommerce

# -----------------------------------------------------------------------------
# 2. Clone repository
# -----------------------------------------------------------------------------
echo "📥 Cloning repository..."
if [ -d ".git" ]; then
    echo "   Repository already exists, pulling latest..."
    git pull origin master
else
    git clone https://github.com/Arafat6462/website_3.git .
fi

# -----------------------------------------------------------------------------
# 3. Setup environment file
# -----------------------------------------------------------------------------
echo "🔐 Setting up environment..."
if [ ! -f ".env.production" ]; then
    cp .env.production .env.production.example
fi

# Generate SECRET_KEY
echo "   Generating SECRET_KEY..."
SECRET_KEY=$(openssl rand -base64 50 | tr -d '\n')

# Generate DB_PASSWORD
echo "   Generating DB_PASSWORD..."
DB_PASSWORD=$(openssl rand -base64 32 | tr -d '\n' | tr '+/' '-_')

# Update .env.production
cat > .env.production << EOF
# =============================================================================
# Production Environment Variables - AUTO-GENERATED
# =============================================================================

# -----------------------------------------------------------------------------
# Django Settings
# -----------------------------------------------------------------------------
DJANGO_SETTINGS_MODULE=config.settings.production
DEBUG=False
SECRET_KEY=$SECRET_KEY
ALLOWED_HOSTS=ecom.arafat2.me,165.22.217.133

# -----------------------------------------------------------------------------
# Database Configuration
# -----------------------------------------------------------------------------
DB_NAME=ecom_prod
DB_USER=ecom_user
DB_PASSWORD=$DB_PASSWORD
DB_HOST=db
DB_PORT=5432

# -----------------------------------------------------------------------------
# Redis Configuration
# -----------------------------------------------------------------------------
REDIS_URL=redis://redis:6379/0

# -----------------------------------------------------------------------------
# GitHub Configuration
# -----------------------------------------------------------------------------
GITHUB_REPOSITORY=Arafat6462/website_3

# -----------------------------------------------------------------------------
# Storage Configuration (Optional - for now using local storage)
# -----------------------------------------------------------------------------
USE_S3=False

# -----------------------------------------------------------------------------
# Email Configuration (Optional - configure later)
# -----------------------------------------------------------------------------
EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=
EMAIL_HOST_PASSWORD=

# -----------------------------------------------------------------------------
# Security
# -----------------------------------------------------------------------------
SECURE_SSL_REDIRECT=True
SESSION_COOKIE_SECURE=True
CSRF_COOKIE_SECURE=True
CSRF_TRUSTED_ORIGINS=https://ecom.arafat2.me

# -----------------------------------------------------------------------------
# Logging
# -----------------------------------------------------------------------------
LOG_LEVEL=INFO
EOF

echo "✓ Environment file created with random secrets"

# -----------------------------------------------------------------------------
# 4. Ask for GitHub Personal Access Token
# -----------------------------------------------------------------------------
echo ""
echo "🔑 GitHub Container Registry Login"
echo "   You need a Personal Access Token with 'read:packages' permission"
echo "   Get it from: https://github.com/settings/tokens"
echo ""
read -sp "Enter your GitHub Personal Access Token: " GITHUB_TOKEN
echo ""

# Login to GitHub Container Registry
echo "$GITHUB_TOKEN" | docker login ghcr.io -u Arafat6462 --password-stdin

# -----------------------------------------------------------------------------
# 5. Pull and start containers
# -----------------------------------------------------------------------------
echo "🐳 Starting Docker containers..."
docker compose -f docker-compose.prod.yml pull
docker compose -f docker-compose.prod.yml up -d

# -----------------------------------------------------------------------------
# 6. Wait for database
# -----------------------------------------------------------------------------
echo "⏳ Waiting for database to be ready..."
sleep 15

# -----------------------------------------------------------------------------
# 7. Run migrations
# -----------------------------------------------------------------------------
echo "🗄️  Running database migrations..."
docker compose -f docker-compose.prod.yml exec -T web python manage.py migrate --noinput

# -----------------------------------------------------------------------------
# 8. Create superuser
# -----------------------------------------------------------------------------
echo ""
echo "👤 Creating superuser account..."
echo "   (Enter username, email, and password when prompted)"
docker compose -f docker-compose.prod.yml exec web python manage.py createsuperuser

# -----------------------------------------------------------------------------
# 9. Collect static files
# -----------------------------------------------------------------------------
echo "📁 Collecting static files..."
docker compose -f docker-compose.prod.yml exec -T web python manage.py collectstatic --noinput

# -----------------------------------------------------------------------------
# 10. Health check
# -----------------------------------------------------------------------------
echo "🏥 Running health check..."
sleep 5
HEALTH_CHECK=$(curl -s http://localhost:8000/api/v1/health/ || echo "FAILED")

echo ""
echo "================================================"
if [[ "$HEALTH_CHECK" == *"healthy"* ]]; then
    echo "✅ SETUP COMPLETE!"
    echo ""
    echo "🌐 Your site is live at:"
    echo "   https://ecom.arafat2.me/admin/"
    echo ""
    echo "📊 Useful commands:"
    echo "   View logs: cd /opt/ecommerce && docker compose -f docker-compose.prod.yml logs -f web"
    echo "   Restart:   cd /opt/ecommerce && docker compose -f docker-compose.prod.yml restart"
    echo "   Stop:      cd /opt/ecommerce && docker compose -f docker-compose.prod.yml down"
    echo ""
    echo "🚀 Next steps:"
    echo "   1. Add GitHub secrets (see QUICK_DEPLOY.md)"
    echo "   2. Push code to trigger auto-deployment"
else
    echo "❌ Health check failed!"
    echo "   View logs: docker compose -f /opt/ecommerce/docker-compose.prod.yml logs web"
fi
echo "================================================"
