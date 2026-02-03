# Production Deployment Guide

Complete guide for deploying the E-Commerce backend to production.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Server Setup](#server-setup)
3. [Environment Configuration](#environment-configuration)
4. [SSL Certificate Setup](#ssl-certificate-setup)
5. [Deployment](#deployment)
6. [Post-Deployment](#post-deployment)
7. [Maintenance](#maintenance)
8. [Monitoring](#monitoring)
9. [Troubleshooting](#troubleshooting)
10. [Rollback Procedure](#rollback-procedure)

---

## Prerequisites

### System Requirements

- **Server:** Ubuntu 22.04 LTS or newer (recommended)
- **RAM:** Minimum 2GB, recommended 4GB+
- **Storage:** Minimum 20GB SSD
- **CPU:** 2 cores minimum
- **Network:** Static IP address, domain name configured

### Required Software

- Docker 24.0+ and Docker Compose 2.0+
- Git
- (Optional) Nginx for SSL termination outside Docker

### Domain & DNS

- Domain name registered
- DNS A record pointing to server IP
- (Optional) CDN configured for static assets

---

## Server Setup

### 1. Install Docker

```bash
# Update package index
sudo apt update
sudo apt upgrade -y

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Add user to docker group
sudo usermod -aG docker $USER

# Install Docker Compose
sudo apt install docker-compose-plugin -y

# Verify installation
docker --version
docker compose version
```

### 2. Configure Firewall

```bash
# Allow SSH, HTTP, HTTPS
sudo ufw allow 22/tcp
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw enable

# Verify
sudo ufw status
```

### 3. Create Application Directory

```bash
# Create app directory
sudo mkdir -p /opt/ecommerce
sudo chown $USER:$USER /opt/ecommerce
cd /opt/ecommerce

# Clone repository
git clone <your-repo-url> .

# Or upload files via SCP/SFTP
```

---

## Environment Configuration

### 1. Create Production Environment File

```bash
# Copy example file
cp .env.production.example .env.production

# Edit with your values
nano .env.production
```

### 2. Required Environment Variables

#### Core Settings

```bash
SECRET_KEY=<generate-with-command-below>
DEBUG=False
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com
DJANGO_SETTINGS_MODULE=config.settings.production
```

**Generate SECRET_KEY:**
```bash
python3 -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

#### Database

```bash
DB_NAME=ecom_db
DB_USER=ecom_user
DB_PASSWORD=<strong-password-here>
DB_HOST=db
DB_PORT=5432
```

#### Redis

```bash
REDIS_PASSWORD=<strong-password-here>
REDIS_URL=redis://:your-redis-password@redis:6379/0
```

#### CORS & CSRF

```bash
CORS_ALLOWED_ORIGINS=https://yourdomain.com
CSRF_TRUSTED_ORIGINS=https://yourdomain.com,https://www.yourdomain.com
```

#### Email (Gmail Example)

```bash
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=<app-specific-password>
DEFAULT_FROM_EMAIL=noreply@yourdomain.com
```

**Gmail App Password:** https://support.google.com/accounts/answer/185833

#### Cloud Storage (Cloudflare R2 Example)

```bash
AWS_ACCESS_KEY_ID=<your-r2-access-key>
AWS_SECRET_ACCESS_KEY=<your-r2-secret-key>
AWS_STORAGE_BUCKET_NAME=your-bucket-name
AWS_S3_ENDPOINT_URL=https://<account-id>.r2.cloudflarestorage.com
```

#### Site Information

```bash
SITE_NAME=Your Store Name
SITE_URL=https://yourdomain.com
```

### 3. Secure Environment File

```bash
# Restrict permissions
chmod 600 .env.production

# Never commit to Git!
echo ".env.production" >> .gitignore
```

---

## SSL Certificate Setup

### Option 1: Let's Encrypt with Certbot (Recommended)

```bash
# Install Certbot
sudo apt install certbot python3-certbot-nginx -y

# Stop nginx if running
sudo systemctl stop nginx

# Generate certificate
sudo certbot certonly --standalone -d yourdomain.com -d www.yourdomain.com

# Certificates will be in:
# /etc/letsencrypt/live/yourdomain.com/fullchain.pem
# /etc/letsencrypt/live/yourdomain.com/privkey.pem

# Copy to project
sudo mkdir -p nginx/ssl
sudo cp /etc/letsencrypt/live/yourdomain.com/fullchain.pem nginx/ssl/cert.pem
sudo cp /etc/letsencrypt/live/yourdomain.com/privkey.pem nginx/ssl/key.pem
sudo chown -R $USER:$USER nginx/ssl

# Auto-renewal
sudo certbot renew --dry-run
```

### Option 2: Self-Signed (Development/Testing Only)

```bash
# Create SSL directory
mkdir -p nginx/ssl

# Generate self-signed certificate
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout nginx/ssl/key.pem \
  -out nginx/ssl/cert.pem \
  -subj "/C=BD/ST=Dhaka/L=Dhaka/O=YourCompany/CN=yourdomain.com"
```

### 3. Enable HTTPS in Nginx

Edit `nginx/conf.d/app.conf` and uncomment the HTTPS server block.

---

## Deployment

### 1. First-Time Deployment

```bash
# Run deployment script
bash scripts/deploy.sh fresh
```

**What it does:**
- Builds Docker images
- Creates database and runs migrations
- Collects static files
- Starts all services
- Prompts to create superuser

### 2. Update Deployment

```bash
# For updates (code changes)
bash scripts/deploy.sh update
```

**What it does:**
- Creates backup
- Pulls latest code
- Rebuilds images
- Runs new migrations
- Collects static files
- Restarts services with zero downtime

### 3. Manual Deployment Steps

```bash
# 1. Build images
docker compose -f docker-compose.prod.yml build

# 2. Start services
docker compose -f docker-compose.prod.yml up -d

# 3. Run migrations
docker compose -f docker-compose.prod.yml exec web python manage.py migrate

# 4. Collect static files
docker compose -f docker-compose.prod.yml exec web python manage.py collectstatic --noinput

# 5. Create superuser
docker compose -f docker-compose.prod.yml exec web python manage.py createsuperuser
```

---

## Post-Deployment

### 1. Verify Services

```bash
# Check service status
docker compose -f docker-compose.prod.yml ps

# All services should show "running" and "healthy"
```

### 2. Test Application

```bash
# Health check
curl http://localhost/api/v1/health/

# Should return: {"status": "ok"}

# HTTPS check
curl https://yourdomain.com/api/v1/health/
```

### 3. Create Admin User

```bash
docker compose -f docker-compose.prod.yml exec web python manage.py createsuperuser
```

### 4. Access Admin Panel

Navigate to: `https://yourdomain.com/admin/`

### 5. Configure Site Settings

In Django admin:
- Site Settings → Configure store info
- Shipping Zones → Add delivery areas
- Coupons → Create promotional codes

---

## Maintenance

### Backups

#### Automated Backups

```bash
# Setup cron job for daily backups
crontab -e

# Add this line (runs daily at 2 AM)
0 2 * * * cd /opt/ecommerce && bash scripts/backup.sh >> logs/backup.log 2>&1
```

#### Manual Backup

```bash
bash scripts/backup.sh
```

Backups are stored in `./backups/` directory.

#### Restore Database

```bash
# Stop web service
docker compose -f docker-compose.prod.yml stop web

# Restore database
gunzip < backups/db_backup_YYYYMMDD_HHMMSS.sql.gz | \
  docker compose -f docker-compose.prod.yml exec -T db \
  psql -U ecom_user ecom_db

# Start web service
docker compose -f docker-compose.prod.yml start web
```

### Log Management

```bash
# View logs
docker compose -f docker-compose.prod.yml logs -f web

# View last 100 lines
docker compose -f docker-compose.prod.yml logs --tail=100 web

# Nginx logs
tail -f logs/nginx/access.log
tail -f logs/nginx/error.log

# Django logs
tail -f logs/django/gunicorn-access.log
tail -f logs/django/gunicorn-error.log
```

### Updates

```bash
# Update code
git pull origin main

# Deploy updates
bash scripts/deploy.sh update
```

### Database Migrations

```bash
# Create migration
docker compose -f docker-compose.prod.yml exec web \
  python manage.py makemigrations

# Apply migrations
docker compose -f docker-compose.prod.yml exec web \
  python manage.py migrate
```

---

## Monitoring

### Service Health Checks

```bash
# Check all services
docker compose -f docker-compose.prod.yml ps

# Check specific service
docker compose -f docker-compose.prod.yml exec web python manage.py check --deploy
```

### Resource Usage

```bash
# Docker stats
docker stats

# Disk usage
df -h

# Memory usage
free -h
```

### Application Monitoring

Recommended tools:
- **Sentry** - Error tracking
- **New Relic** - APM monitoring
- **Grafana + Prometheus** - Metrics
- **Uptime Robot** - Uptime monitoring

---

## Troubleshooting

### Services Won't Start

```bash
# Check logs
docker compose -f docker-compose.prod.yml logs

# Check specific service
docker compose -f docker-compose.prod.yml logs web

# Restart services
docker compose -f docker-compose.prod.yml restart
```

### Database Connection Issues

```bash
# Check database is running
docker compose -f docker-compose.prod.yml ps db

# Test connection
docker compose -f docker-compose.prod.yml exec web \
  python manage.py dbshell

# Check credentials in .env.production
```

### Static Files Not Loading

```bash
# Recollect static files
docker compose -f docker-compose.prod.yml exec web \
  python manage.py collectstatic --noinput

# Check Nginx configuration
docker compose -f docker-compose.prod.yml exec nginx nginx -t

# Reload Nginx
docker compose -f docker-compose.prod.yml exec nginx nginx -s reload
```

### High Memory Usage

```bash
# Restart Gunicorn
docker compose -f docker-compose.prod.yml restart web

# Adjust worker count in gunicorn.conf.py
# Reduce: workers = multiprocessing.cpu_count() + 1
```

### SSL Certificate Issues

```bash
# Renew Let's Encrypt certificate
sudo certbot renew

# Copy new certificates
sudo cp /etc/letsencrypt/live/yourdomain.com/fullchain.pem nginx/ssl/cert.pem
sudo cp /etc/letsencrypt/live/yourdomain.com/privkey.pem nginx/ssl/key.pem

# Restart Nginx
docker compose -f docker-compose.prod.yml restart nginx
```

---

## Rollback Procedure

### Quick Rollback

```bash
# 1. Stop current deployment
docker compose -f docker-compose.prod.yml down

# 2. Checkout previous version
git checkout <previous-commit-hash>

# 3. Restore database backup
gunzip < backups/db_backup_<timestamp>.sql.gz | \
  docker compose -f docker-compose.prod.yml exec -T db \
  psql -U ecom_user ecom_db

# 4. Redeploy
bash scripts/deploy.sh update
```

### Backup-Based Rollback

```bash
# Use latest backup
ls -lt backups/

# Restore specific backup
bash scripts/restore.sh backups/db_backup_20260203_020000.sql.gz
```

---

## Performance Optimization

### Database Optimization

```bash
# Analyze database
docker compose -f docker-compose.prod.yml exec db \
  psql -U ecom_user ecom_db -c "VACUUM ANALYZE;"

# Check slow queries
# Enable in settings: DATABASE['OPTIONS']['log_statement'] = 'all'
```

### Caching

Redis is configured for:
- Rate limiting cache
- Session storage
- General application cache

### CDN Configuration

For optimal performance, serve static/media files from CDN:
1. Upload static files to CDN after `collectstatic`
2. Set `AWS_S3_CUSTOM_DOMAIN` in production settings
3. Configure CDN to cache with long TTL

---

## Security Checklist

- [ ] DEBUG=False in production
- [ ] Strong SECRET_KEY generated
- [ ] Database password is strong and unique
- [ ] Redis password configured
- [ ] SSL certificate valid and auto-renewing
- [ ] Firewall configured (only 80, 443, 22 open)
- [ ] .env.production has restrictive permissions (600)
- [ ] Admin URL changed for obscurity (optional)
- [ ] Regular backups automated
- [ ] Monitoring and alerts configured
- [ ] CORS restricted to frontend domain only
- [ ] File upload limits enforced
- [ ] Rate limiting active
- [ ] Security headers configured in Nginx

---

## Support & Resources

- **Documentation:** https://docs.djangoproject.com/
- **Docker:** https://docs.docker.com/
- **Nginx:** https://nginx.org/en/docs/
- **Let's Encrypt:** https://letsencrypt.org/docs/

---

## License

[Your License Here]

## Contact

[Your Contact Information]
