# Phase 20 - Production Deployment

## Overview

Phase 20 completes the e-commerce backend with production-ready deployment infrastructure, monitoring, and operational tools.

## What Was Implemented

### 1. Production Docker Configuration

**Dockerfile.prod** - Multi-stage build for optimized production images:
- **Builder stage**: Installs dependencies in virtual environment
- **Runtime stage**: Minimal image with non-root user (appuser)
- **Health checks**: Built-in health monitoring
- **Gunicorn**: Production WSGI server

**docker-compose.prod.yml** - Complete production stack:
- PostgreSQL 16 (persistent database)
- Redis 7 (cache and rate limiting)
- Django + Gunicorn (application server)
- Nginx (reverse proxy and static file server)
- Health checks on all services
- Persistent volumes for data
- Restart policies for resilience

### 2. Web Server Configuration

**Gunicorn** (`src/gunicorn.conf.py`):
- Auto-scaled workers: `(2 * CPU cores) + 1`
- Request timeouts: 120 seconds
- Worker recycling: 1000 requests per worker
- Access and error logging
- Security limits for requests
- Lifecycle hooks for monitoring

**Nginx** (`nginx/nginx.conf` and `nginx/conf.d/app.conf`):
- Reverse proxy to Gunicorn
- HTTP server (port 80) - active
- HTTPS server (port 443) - ready for SSL certificates
- Static file serving with 30-day cache
- Media file serving with 7-day cache
- Gzip compression (level 6)
- Security headers (X-Frame-Options, X-XSS-Protection, etc.)
- Health check endpoint

### 3. Environment Configuration

**.env.production.example** - Comprehensive template with 50+ variables:
- Django core settings (SECRET_KEY, DEBUG, ALLOWED_HOSTS)
- Database credentials (PostgreSQL)
- Redis configuration
- CORS and CSRF trusted origins
- Email service (SMTP)
- Cloud storage (S3/R2/Spaces)
- Security settings (ADMIN_URL, IP whitelist)
- Monitoring (Sentry DSN)
- Payment gateways (bKash, Nagad, SSLCommerz)

### 4. Automation Scripts

**backup.sh** - Automated backup system:
- PostgreSQL database dump (compressed)
- Media files archive (tar.gz)
- Cloud upload capability (AWS CLI ready)
- Automatic cleanup (7-day rotation)
- Timestamped backups
- Color-coded logging

**deploy.sh** - Deployment automation:
- **Fresh deployment**: Complete setup with volume creation
- **Update deployment**: Zero-downtime rolling updates
- **Rollback**: Framework for version rollback
- Pre-deployment checks
- Automatic backups before deploy
- Migration execution
- Static file collection
- Health verification

**validate_production.sh** - Pre-deployment validation:
- Environment file verification
- Docker installation check
- File permissions audit
- SSL certificate validation
- Port availability check
- Disk space monitoring
- Git status verification
- Security configuration review
- Comprehensive summary report

**test_health_check.sh** - Health endpoint testing:
- Tests enhanced health check
- Verifies database connectivity check
- Validates cache connectivity check
- Confirms storage accessibility check

### 5. Enhanced Health Checks

**api/v1/urls.py** - Upgraded health endpoint (`/api/v1/health/`):
- **Database check**: Tests PostgreSQL connectivity with SELECT 1
- **Cache check**: Tests Redis read/write operations
- **Storage check**: Verifies cloud storage accessibility
- **Status codes**: 200 (healthy), 503 (unhealthy)
- **Detailed response**: Component-level status reporting

Example response:
```json
{
    "status": "healthy",
    "version": "1.0",
    "api": "v1",
    "timestamp": 1738613456.789,
    "checks": {
        "database": {
            "status": "healthy",
            "message": "Database connection successful"
        },
        "cache": {
            "status": "healthy",
            "message": "Cache connection successful"
        },
        "storage": {
            "status": "healthy",
            "message": "Storage accessible"
        }
    }
}
```

### 6. Documentation

**DEPLOYMENT.md** - Complete deployment guide:
- Prerequisites and system requirements
- Server setup instructions
- Environment configuration
- SSL certificate setup (Let's Encrypt & self-signed)
- Deployment procedures (fresh & update)
- Post-deployment verification
- Maintenance procedures (backups, logs, updates)
- Monitoring setup recommendations
- Troubleshooting common issues
- Rollback procedures
- Performance optimization tips

**PRODUCTION_CHECKLIST.md** - Pre-deployment checklist:
- Environment & configuration verification
- Security checklist
- Cloud services setup
- Database preparation
- Application readiness
- Infrastructure validation
- Monitoring & logging setup
- Performance checks
- Content setup guide
- Domain & DNS configuration
- Testing procedures
- Documentation review
- Backup & recovery verification
- Final go-live checklist

## File Structure

```
website_3/
├── Dockerfile.prod                    # Production Docker image
├── docker-compose.prod.yml            # Production orchestration
├── .env.production.example            # Environment template
├── DEPLOYMENT.md                      # Deployment guide
├── PRODUCTION_CHECKLIST.md            # Pre-deployment checklist
├── src/
│   └── gunicorn.conf.py              # Gunicorn configuration
├── nginx/
│   ├── nginx.conf                     # Main Nginx config
│   ├── conf.d/
│   │   └── app.conf                  # Application server config
│   └── ssl/                           # SSL certificates (create this)
│       ├── cert.pem
│       └── key.pem
├── scripts/
│   ├── backup.sh                      # Backup automation
│   ├── deploy.sh                      # Deployment automation
│   ├── validate_production.sh         # Pre-deployment validation
│   └── test_health_check.sh          # Health check testing
└── logs/                              # Log files (created on deploy)
    ├── django/
    └── nginx/
```

## Quick Start

### 1. Environment Setup

```bash
# Copy environment template
cp .env.production.example .env.production

# Edit with your values
nano .env.production

# Generate SECRET_KEY
python3 -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"

# Set restrictive permissions
chmod 600 .env.production
```

### 2. Validation

```bash
# Run production validation
bash scripts/validate_production.sh
```

### 3. SSL Certificate (Let's Encrypt)

```bash
# Install Certbot
sudo apt install certbot

# Generate certificate
sudo certbot certonly --standalone -d yourdomain.com

# Copy certificates
sudo mkdir -p nginx/ssl
sudo cp /etc/letsencrypt/live/yourdomain.com/fullchain.pem nginx/ssl/cert.pem
sudo cp /etc/letsencrypt/live/yourdomain.com/privkey.pem nginx/ssl/key.pem
```

### 4. Deploy

```bash
# Fresh deployment (first time)
bash scripts/deploy.sh fresh

# Update deployment (subsequent deploys)
bash scripts/deploy.sh update
```

### 5. Verify

```bash
# Check services
docker compose -f docker-compose.prod.yml ps

# Test health check
curl http://localhost/api/v1/health/

# Or with HTTPS
curl https://yourdomain.com/api/v1/health/
```

## Deployment Modes

### Fresh Deployment

Complete setup from scratch:
```bash
bash scripts/deploy.sh fresh
```

**What it does:**
- Stops and removes all containers
- Deletes volumes (⚠️ WARNING: Data loss!)
- Builds fresh Docker images
- Creates new database
- Runs migrations
- Collects static files
- Creates superuser (interactive)

**Use when:** Initial deployment or complete reset needed

### Update Deployment

Zero-downtime rolling update:
```bash
bash scripts/deploy.sh update
```

**What it does:**
- Creates backup (database + media)
- Pulls latest code (if Git configured)
- Rebuilds Docker images
- Runs new migrations
- Collects static files
- Restarts web service (zero-downtime)
- Verifies health checks

**Use when:** Deploying code updates, migrations, or config changes

### Rollback

Revert to previous version:
```bash
bash scripts/deploy.sh rollback
```

**Note:** Rollback implementation requires customization based on your version control strategy.

## Monitoring

### Service Health

```bash
# All services status
docker compose -f docker-compose.prod.yml ps

# Web service logs
docker compose -f docker-compose.prod.yml logs -f web

# Database logs
docker compose -f docker-compose.prod.yml logs -f db
```

### Application Health

```bash
# Health check API
curl http://localhost/api/v1/health/

# Django admin check
docker compose -f docker-compose.prod.yml exec web \
  python manage.py check --deploy
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

## Backup & Restore

### Manual Backup

```bash
bash scripts/backup.sh
```

Backups stored in `./backups/`:
- `db_backup_YYYYMMDD_HHMMSS.sql.gz` - Database dump
- `media_backup_YYYYMMDD_HHMMSS.tar.gz` - Media files

### Automated Backups

Setup cron job:
```bash
crontab -e

# Add daily backup at 2 AM
0 2 * * * cd /opt/ecommerce && bash scripts/backup.sh >> logs/backup.log 2>&1
```

### Restore Database

```bash
# Stop web service
docker compose -f docker-compose.prod.yml stop web

# Restore from backup
gunzip < backups/db_backup_20260203_020000.sql.gz | \
  docker compose -f docker-compose.prod.yml exec -T db \
  psql -U ecom_user ecom_db

# Restart web service
docker compose -f docker-compose.prod.yml start web
```

## Security Features

- ✅ Non-root container user (appuser)
- ✅ Multi-stage Docker build (minimal attack surface)
- ✅ Environment variable separation (.env.production)
- ✅ SSL/TLS ready (HTTPS configuration)
- ✅ Security headers (X-Frame-Options, XSS Protection, etc.)
- ✅ Restricted CORS (frontend domain only)
- ✅ Rate limiting (django-ratelimit)
- ✅ API throttling (DRF)
- ✅ Input validation and sanitization
- ✅ Security middleware (suspicious request detection)
- ✅ Secure cookies (HttpOnly, Secure, SameSite)
- ✅ Database connection pooling
- ✅ Redis password protection
- ✅ File upload limits
- ✅ Static file caching

## Performance Optimizations

- ✅ Gunicorn worker auto-scaling
- ✅ Worker recycling (prevents memory leaks)
- ✅ Nginx gzip compression
- ✅ Static file caching (30 days)
- ✅ Media file caching (7 days)
- ✅ Database connection pooling (CONN_MAX_AGE=600)
- ✅ Redis caching layer
- ✅ Health checks at all layers

## Troubleshooting

### Services Won't Start

```bash
# Check logs
docker compose -f docker-compose.prod.yml logs

# Rebuild images
docker compose -f docker-compose.prod.yml build --no-cache

# Restart
docker compose -f docker-compose.prod.yml restart
```

### Database Connection Issues

```bash
# Check database container
docker compose -f docker-compose.prod.yml ps db

# Test connection
docker compose -f docker-compose.prod.yml exec web \
  python manage.py dbshell

# Verify credentials in .env.production
```

### Static Files Not Loading

```bash
# Recollect static files
docker compose -f docker-compose.prod.yml exec web \
  python manage.py collectstatic --noinput

# Restart Nginx
docker compose -f docker-compose.prod.yml restart nginx
```

### High Memory Usage

```bash
# Restart web service
docker compose -f docker-compose.prod.yml restart web

# Monitor resources
docker stats
```

## Production Checklist Summary

Before deploying, ensure:
- [ ] .env.production configured with all variables
- [ ] DEBUG=False
- [ ] SECRET_KEY generated
- [ ] Database password changed from default
- [ ] SSL certificates installed
- [ ] HTTPS enabled in Nginx
- [ ] CORS restricted to frontend domain
- [ ] Firewall configured (ports 80, 443, 22)
- [ ] Backup cron job configured
- [ ] Monitoring configured
- [ ] Domain DNS pointing to server
- [ ] All scripts executable (chmod +x scripts/*.sh)
- [ ] Validation passed (bash scripts/validate_production.sh)

## Next Steps

After deployment:
1. Create superuser account
2. Configure site settings in admin
3. Add shipping zones
4. Create product types and attributes
5. Add initial products
6. Test order workflow
7. Configure payment gateways
8. Set up monitoring alerts
9. Schedule regular backups
10. Monitor logs for errors

## Support & Resources

- **Django Documentation**: https://docs.djangoproject.com/
- **Docker Documentation**: https://docs.docker.com/
- **Nginx Documentation**: https://nginx.org/en/docs/
- **Gunicorn Documentation**: https://docs.gunicorn.org/
- **Let's Encrypt**: https://letsencrypt.org/

---

## Implementation Summary

**Phase 20 Status**: ✅ **COMPLETE**

**Files Created**: 10
- Dockerfile.prod
- docker-compose.prod.yml
- src/gunicorn.conf.py
- nginx/nginx.conf
- nginx/conf.d/app.conf
- .env.production.example
- scripts/backup.sh
- scripts/deploy.sh
- scripts/validate_production.sh
- scripts/test_health_check.sh

**Files Modified**: 1
- api/v1/urls.py (enhanced health check)

**Documentation Created**: 3
- DEPLOYMENT.md
- PRODUCTION_CHECKLIST.md
- PHASE_20_README.md (this file)

**Features Delivered**:
- ✅ Production Docker configuration
- ✅ Multi-stage builds
- ✅ Gunicorn WSGI server
- ✅ Nginx reverse proxy
- ✅ SSL/TLS support
- ✅ Automated backups
- ✅ Deployment automation
- ✅ Health monitoring
- ✅ Production validation
- ✅ Comprehensive documentation

**Ready for Production**: ✅ YES

---

## License

[Your License Here]
