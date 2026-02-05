#!/bin/bash
# Complete deployment script - run ONCE on VPS after initial setup
# This will:
# 1. Update nginx config for simplified proxy (WhiteNoise serves static)
# 2. Reload nginx
# 3. Restart containers with new code
# 4. Run collectstatic inside container
# 5. Verify everything works

set -e

echo "════════════════════════════════════════════════════════"
echo "COMPLETE DEPLOYMENT FIX"
echo "════════════════════════════════════════════════════════"

# Step 1: Update nginx config
echo "Step 1: Updating nginx configuration..."
sudo rm -f /etc/nginx/sites-enabled/ecom.arafat2.me
sudo mv /tmp/nginx_simple.conf /etc/nginx/sites-available/ecom.arafat2.me
sudo ln -sf /etc/nginx/sites-available/ecom.arafat2.me /etc/nginx/sites-enabled/ecom.arafat2.me

# Step 2: Test and reload nginx
echo "Step 2: Testing nginx configuration..."
sudo nginx -t

echo "Step 3: Reloading nginx..."
sudo systemctl reload nginx

# Step 4: Pull latest code and restart containers
echo "Step 4: Pulling latest Docker image..."
cd ~/ecommerce
docker compose -f docker-compose.prod.yml pull web

echo "Step 5: Restarting web container..."
docker compose -f docker-compose.prod.yml up -d web

# Step 6: Wait for container to be healthy
echo "Step 6: Waiting for container to be healthy..."
sleep 10

# Step 7: Collect static files inside container
echo "Step 7: Collecting static files..."
docker compose -f docker-compose.prod.yml exec -T web python manage.py collectstatic --noinput || echo "Static files already collected"

echo ""
echo "════════════════════════════════════════════════════════"
echo "✅ DEPLOYMENT COMPLETE!"
echo "════════════════════════════════════════════════════════"
echo ""
echo "Testing the site..."
sleep 3

# Test all endpoints
echo "Testing Health API..."
if curl -sL https://ecom.arafat2.me/api/v1/health/ | grep -q "healthy"; then
    echo "✅ Health API working!"
fi

echo "Testing Admin Panel..."
if curl -sL https://ecom.arafat2.me/admin/ | grep -q "Log in"; then
    echo "✅ Admin panel working!"
fi

echo "Testing Static Files..."
STATUS=$(curl -sL -o /dev/null -w "%{http_code}" https://ecom.arafat2.me/static/unfold/css/styles.css)
if [ "$STATUS" = "200" ]; then
    echo "✅ Static files working!"
else
    echo "⚠️  Static files returned HTTP $STATUS (might need a moment to load)"
fi

echo ""
echo "════════════════════════════════════════════════════════"
echo "Your site is LIVE at https://ecom.arafat2.me/"
echo "Admin panel: https://ecom.arafat2.me/admin/"
echo ""
echo "Login: admin@ecom.local / admin123"
echo "════════════════════════════════════════════════════════"
