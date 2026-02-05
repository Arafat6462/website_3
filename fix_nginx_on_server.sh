#!/bin/bash
# Complete Nginx Fix Script - Run this ONCE on your VPS
# This will fix nginx configuration and enable passwordless sudo for nginx/systemctl

set -e

echo "════════════════════════════════════════════════════════"
echo "FIXING NGINX CONFIGURATION"
echo "════════════════════════════════════════════════════════"

# Step 1: Fix the nginx symlink
echo "Step 1: Removing old nginx config file..."
sudo rm -f /etc/nginx/sites-enabled/ecom.arafat2.me

echo "Step 2: Creating proper symlink..."
sudo ln -sf /etc/nginx/sites-available/ecom.arafat2.me /etc/nginx/sites-enabled/ecom.arafat2.me

# Step 3: Test nginx configuration
echo "Step 3: Testing nginx configuration..."
sudo nginx -t

# Step 4: Reload nginx
echo "Step 4: Reloading nginx..."
sudo systemctl reload nginx

# Step 5: Enable passwordless sudo for nginx commands (for CI/CD)
echo "Step 5: Setting up passwordless sudo for nginx commands..."
echo "arafat ALL=(ALL) NOPASSWD: /usr/sbin/nginx, /bin/systemctl reload nginx, /bin/systemctl restart nginx, /bin/rm -f /etc/nginx/sites-enabled/*, /bin/ln -sf /etc/nginx/sites-available/* /etc/nginx/sites-enabled/*" | sudo tee /etc/sudoers.d/nginx-nopasswd > /dev/null

sudo chmod 0440 /etc/sudoers.d/nginx-nopasswd

echo ""
echo "════════════════════════════════════════════════════════"
echo "✅ NGINX FIXED!"
echo "════════════════════════════════════════════════════════"
echo ""
echo "Your Django app should now be visible at:"
echo "  🌐 https://ecom.arafat2.me/"
echo "  🔐 https://ecom.arafat2.me/admin/"
echo ""
echo "Testing the site..."
sleep 2

# Test the site
if curl -sL https://ecom.arafat2.me/api/v1/health/ | grep -q "healthy"; then
    echo "✅ Site is WORKING!"
else
    echo "⚠️  Health check didn't return expected response. Checking what we got:"
    curl -sL https://ecom.arafat2.me/ | head -10
fi

echo ""
echo "Future deployments will automatically reload nginx (no password needed)"
echo "════════════════════════════════════════════════════════"
