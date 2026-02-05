#!/bin/bash
# Quick fix for server - Run this on your DigitalOcean server

cd ~/ecommerce

# Stop everything
docker compose -f docker-compose.prod.yml down

# Generate secrets
SECRET_KEY=$(openssl rand -base64 50 | tr -d '\n')
DB_PASSWORD=$(openssl rand -base64 32 | tr -d '\n')

# Create .env.production
cat > .env.production <<EOF
DJANGO_SETTINGS_MODULE=config.settings.production
DEBUG=False
SECRET_KEY=${SECRET_KEY}
ALLOWED_HOSTS=ecom.arafat2.me,165.22.217.133
DB_NAME=ecom_prod
DB_USER=ecom_user
DB_PASSWORD=${DB_PASSWORD}
DB_HOST=db
DB_PORT=5432
REDIS_URL=redis://redis:6379/0
GITHUB_REPOSITORY=Arafat6462/website_3
USE_S3=False
EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend
SECURE_SSL_REDIRECT=False
SESSION_COOKIE_SECURE=False
CSRF_COOKIE_SECURE=False
CSRF_TRUSTED_ORIGINS=https://ecom.arafat2.me,http://165.22.217.133
LOG_LEVEL=INFO
EOF

echo "✓ Created .env.production"

# Remove old volumes (fresh start)
docker volume rm $(docker volume ls -q | grep ecom) 2>/dev/null || true

# Pull images
docker compose -f docker-compose.prod.yml pull

# Start everything
docker compose -f docker-compose.prod.yml up -d

# Wait for database
echo "Waiting for database..."
sleep 15

# Run migrations
docker compose -f docker-compose.prod.yml exec -T web python manage.py migrate --noinput

# Collect static
docker compose -f docker-compose.prod.yml exec -T web python manage.py collectstatic --noinput

# Show status
echo ""
echo "✅ Containers running:"
docker compose -f docker-compose.prod.yml ps

echo ""
echo "📝 Create superuser:"
echo "   docker compose -f docker-compose.prod.yml exec web python manage.py createsuperuser"

echo ""
echo "🌐 Visit: http://165.22.217.133/admin/"
