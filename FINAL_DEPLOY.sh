#!/bin/bash
# Run this on server AFTER GitHub Actions finishes building

cd ~/ecommerce

echo "🐳 Pulling latest image..."
docker compose -f docker-compose.prod.yml pull

echo "🚀 Starting containers..."
docker compose -f docker-compose.prod.yml up -d

echo "⏳ Waiting for containers..."
sleep 25

echo "🗄️ Running migrations..."
docker compose -f docker-compose.prod.yml exec -T web python manage.py migrate --noinput

echo "📁 Collecting static files..."
docker compose -f docker-compose.prod.yml exec -T web python manage.py collectstatic --noinput

echo ""
echo "✅ DEPLOYMENT COMPLETE!"
echo ""
echo "📊 Container status:"
docker compose -f docker-compose.prod.yml ps

echo ""
echo "🏥 Health check:"
curl -s http://localhost:8000/api/v1/health/ || echo "Waiting for app to start..."

echo ""
echo "👤 Create superuser:"
echo "   docker compose -f docker-compose.prod.yml exec web python manage.py createsuperuser"
echo ""
echo "🌐 Visit: http://ecom.arafat2.me/admin/"
