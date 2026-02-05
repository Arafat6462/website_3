#!/bin/bash
# =============================================================================
# Production Deployment Commands for ecom.arafat2.me
# =============================================================================
# Run these commands on your DigitalOcean server after setup script completes
# =============================================================================

set -e  # Exit on error

echo "🚀 Starting deployment to ecom.arafat2.me..."

# Navigate to app directory
cd /opt/ecommerce

# -----------------------------------------------------------------------------
# STEP 1: Login to GitHub Container Registry
# -----------------------------------------------------------------------------
echo "📦 Logging into GitHub Container Registry..."
echo "⚠️  You need to replace YOUR_GITHUB_TOKEN with your actual token"
echo "   Get token from: https://github.com/settings/tokens"
echo "   Permissions needed: write:packages, read:packages"
echo ""
read -sp "Enter your GitHub Personal Access Token: " GITHUB_TOKEN
echo ""
echo "$GITHUB_TOKEN" | docker login ghcr.io -u Arafat6462 --password-stdin

# -----------------------------------------------------------------------------
# STEP 2: Clone Repository
# -----------------------------------------------------------------------------
echo "📥 Cloning repository..."
if [ -d ".git" ]; then
    echo "   Repository already exists, pulling latest changes..."
    git pull origin master
else
    echo "   Cloning fresh repository..."
    git clone https://github.com/Arafat6462/website_3.git .
fi

# -----------------------------------------------------------------------------
# STEP 3: Generate SECRET_KEY if not set
# -----------------------------------------------------------------------------
echo "🔐 Checking environment configuration..."
if grep -q "CHANGE-THIS" .env.production 2>/dev/null; then
    echo "⚠️  WARNING: .env.production still has placeholder values!"
    echo "   Generating SECRET_KEY for you..."
    
    # Generate a random SECRET_KEY
    NEW_SECRET_KEY=$(openssl rand -base64 50 | tr -d '\n')
    
    # Replace placeholder in .env.production
    sed -i "s|SECRET_KEY=CHANGE-THIS-TO-A-RANDOM-50-CHARACTER-STRING-GENERATE-WITH-openssl-rand-base64-50|SECRET_KEY=$NEW_SECRET_KEY|g" .env.production
    
    echo "✓ SECRET_KEY generated"
    echo ""
    echo "⚠️  You still need to manually set:"
    echo "   - DB_PASSWORD (line 20 in .env.production)"
    echo "   - GITHUB_REPOSITORY=Arafat6462/website_3 (add this line)"
    echo ""
    read -p "Press Enter after you've edited .env.production..."
fi

# Add GITHUB_REPOSITORY if missing
if ! grep -q "GITHUB_REPOSITORY" .env.production; then
    echo "GITHUB_REPOSITORY=Arafat6462/website_3" >> .env.production
fi

# -----------------------------------------------------------------------------
# STEP 4: Start Containers
# -----------------------------------------------------------------------------
echo "🐳 Starting Docker containers..."
docker compose -f docker-compose.prod.yml pull
docker compose -f docker-compose.prod.yml up -d

# Wait for database to be ready
echo "⏳ Waiting for database to be ready..."
sleep 10

# -----------------------------------------------------------------------------
# STEP 5: Run Migrations
# -----------------------------------------------------------------------------
echo "🗄️  Running database migrations..."
docker compose -f docker-compose.prod.yml exec -T web python manage.py migrate --noinput

# -----------------------------------------------------------------------------
# STEP 6: Create Superuser (Interactive)
# -----------------------------------------------------------------------------
echo "👤 Creating superuser account..."
echo "   (This will prompt you for username, email, and password)"
docker compose -f docker-compose.prod.yml exec web python manage.py createsuperuser

# -----------------------------------------------------------------------------
# STEP 7: Collect Static Files
# -----------------------------------------------------------------------------
echo "📁 Collecting static files..."
docker compose -f docker-compose.prod.yml exec -T web python manage.py collectstatic --noinput

# -----------------------------------------------------------------------------
# STEP 8: Health Check
# -----------------------------------------------------------------------------
echo "🏥 Running health check..."
sleep 5
HEALTH_CHECK=$(curl -s http://localhost:8000/api/v1/health/ || echo "FAILED")

if [[ "$HEALTH_CHECK" == *"healthy"* ]]; then
    echo "✅ Deployment successful!"
    echo ""
    echo "🌐 Your site is live at:"
    echo "   https://ecom.arafat2.me/admin/"
    echo ""
    echo "📊 View logs:"
    echo "   docker compose -f /opt/ecommerce/docker-compose.prod.yml logs -f web"
else
    echo "❌ Health check failed!"
    echo "   Check logs: docker compose -f /opt/ecommerce/docker-compose.prod.yml logs web"
fi

echo ""
echo "🎉 Done!"
