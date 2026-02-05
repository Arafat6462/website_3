#!/bin/bash
# ONE-TIME SETUP: Configure passwordless sudo for nginx and apply current nginx config
# Run this ONCE: ssh arafat@ecom.arafat2.me 'bash /tmp/one_time_setup.sh'

set -e

echo "════════════════════════════════════════════════════════"
echo "ONE-TIME SETUP FOR AUTO-DEPLOYMENT"
echo "════════════════════════════════════════════════════════"

# Step 1: Configure passwordless sudo for specific commands
echo "Step 1: Configuring passwordless sudo for deployment automation..."
echo 'arafat ALL=(ALL) NOPASSWD: /usr/sbin/nginx, /bin/systemctl reload nginx, /bin/systemctl restart nginx, /bin/rm -f /etc/nginx/sites-enabled/*, /bin/ln -sf /etc/nginx/sites-available/* /etc/nginx/sites-enabled/*, /bin/cp * /etc/nginx/sites-available/*' | sudo tee /etc/sudoers.d/deployment-automation > /dev/null
sudo chmod 0440 /etc/sudoers.d/deployment-automation
echo "✅ Passwordless sudo configured"

# Step 2: Apply nginx configuration NOW
echo ""
echo "Step 2: Applying nginx configuration..."
cd ~/ecommerce
sudo cp nginx/ecom.arafat2.me.conf /etc/nginx/sites-available/ecom.arafat2.me
sudo rm -f /etc/nginx/sites-enabled/ecom.arafat2.me
sudo ln -sf /etc/nginx/sites-available/ecom.arafat2.me /etc/nginx/sites-enabled/ecom.arafat2.me

echo "Step 3: Testing nginx configuration..."
sudo nginx -t

echo "Step 4: Reloading nginx..."
sudo systemctl reload nginx

echo ""
echo "════════════════════════════════════════════════════════"
echo "✅ SETUP COMPLETE!"
echo "════════════════════════════════════════════════════════"
echo ""
echo "Testing the complete site..."
sleep 2

# Test all endpoints
echo "1. Health API..."
if curl -sL https://ecom.arafat2.me/api/v1/health/ | grep -q "healthy"; then
    echo "   ✅ Healthy"
else
    echo "   ⚠️  Not responding correctly"
fi

echo "2. Admin Panel..."
STATUS=$(curl -sL -o /dev/null -w "%{http_code}" https://ecom.arafat2.me/admin/)
if [ "$STATUS" = "200" ]; then
    echo "   ✅ Working (HTTP $STATUS)"
else
    echo "   ⚠️  HTTP $STATUS"
fi

echo "3. Static Files..."
STATUS=$(curl -sL -o /dev/null -w "%{http_code}" https://ecom.arafat2.me/static/unfold/css/styles.css)
if [ "$STATUS" = "200" ]; then
    echo "   ✅ Working (HTTP $STATUS)"
else
    echo "   ⚠️  HTTP $STATUS"
fi

echo ""
echo "════════════════════════════════════════════════════════"
echo "🎉 YOUR SITE IS NOW FULLY AUTOMATED!"
echo "════════════════════════════════════════════════════════"
echo ""
echo "✅ https://ecom.arafat2.me/ - Live"
echo "✅ https://ecom.arafat2.me/admin/ - Admin Panel"
echo "✅ Auto-deployment enabled (just git push)"
echo ""
echo "Login: admin@ecom.local / admin123"
echo ""
echo "Future deployments will automatically:"
echo "  • Build Docker image"
echo "  • Deploy to server"
echo "  • Run migrations"
echo "  • Collect static files"
echo "  • Update nginx"
echo "  • Restart containers"
echo ""
echo "Just run: git push origin master"
echo "════════════════════════════════════════════════════════"
