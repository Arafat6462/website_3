# Production Readiness Checklist

Complete this checklist before deploying to production.

## Environment & Configuration

- [ ] **Environment file created**
  ```bash
  cp .env.production.example .env.production
  # Edit with actual values
  ```

- [ ] **SECRET_KEY generated**
  ```bash
  python3 -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
  ```

- [ ] **DEBUG=False** in `.env.production`

- [ ] **ALLOWED_HOSTS** configured with actual domain(s)

- [ ] **Database credentials** are strong and unique

- [ ] **Redis password** configured

- [ ] **CORS_ALLOWED_ORIGINS** set to frontend domain

- [ ] **CSRF_TRUSTED_ORIGINS** includes frontend domain

---

## Security

- [ ] **SSL certificate** obtained (Let's Encrypt or commercial)

- [ ] **HTTPS enabled** in Nginx config

- [ ] **HSTS** configured (Strict-Transport-Security header)

- [ ] **Security headers** enabled in Nginx

- [ ] **File permissions** set correctly
  ```bash
  chmod 600 .env.production
  chmod +x scripts/*.sh
  ```

- [ ] **Firewall configured**
  ```bash
  sudo ufw status
  # Should allow only 22, 80, 443
  ```

- [ ] **Rate limiting** active (django-ratelimit installed)

- [ ] **Security audit passed**
  ```bash
  docker compose -f docker-compose.prod.yml exec web \
    python manage.py check --deploy
  ```

---

## Cloud Services

- [ ] **Cloud storage configured** (Cloudflare R2 / DigitalOcean Spaces / AWS S3)
  - AWS_ACCESS_KEY_ID
  - AWS_SECRET_ACCESS_KEY
  - AWS_STORAGE_BUCKET_NAME
  - AWS_S3_ENDPOINT_URL

- [ ] **Email service configured** (Gmail / SendGrid / Mailgun)
  - EMAIL_HOST
  - EMAIL_PORT
  - EMAIL_HOST_USER
  - EMAIL_HOST_PASSWORD

- [ ] **Payment gateway credentials** (bKash, Nagad, SSLCommerz)
  - Test in sandbox mode first
  - Switch to production mode after testing

---

## Database

- [ ] **PostgreSQL 16** running in Docker

- [ ] **Database migrations** applied
  ```bash
  docker compose -f docker-compose.prod.yml exec web \
    python manage.py migrate
  ```

- [ ] **Database backup** configured
  ```bash
  crontab -e
  # Add: 0 2 * * * cd /opt/ecommerce && bash scripts/backup.sh
  ```

- [ ] **Backup tested** (create and restore)

---

## Application

- [ ] **Static files collected**
  ```bash
  docker compose -f docker-compose.prod.yml exec web \
    python manage.py collectstatic --noinput
  ```

- [ ] **Superuser created**
  ```bash
  docker compose -f docker-compose.prod.yml exec web \
    python manage.py createsuperuser
  ```

- [ ] **Admin panel accessible** at `/admin/`

- [ ] **All tests passing**
  ```bash
  docker compose -f docker-compose.prod.yml exec web \
    python manage.py test
  ```

---

## Infrastructure

- [ ] **Docker and Docker Compose installed**
  ```bash
  docker --version
  docker compose version
  ```

- [ ] **All services running**
  ```bash
  docker compose -f docker-compose.prod.yml ps
  # Should show: db, redis, web, nginx all "Up" and "healthy"
  ```

- [ ] **Health check passing**
  ```bash
  curl http://localhost/api/v1/health/
  # Should return: {"status": "healthy", ...}
  ```

- [ ] **Nginx configuration tested**
  ```bash
  docker compose -f docker-compose.prod.yml exec nginx nginx -t
  ```

---

## Monitoring & Logging

- [ ] **Log directories created**
  ```bash
  mkdir -p logs/django logs/nginx
  ```

- [ ] **Logs writable**
  ```bash
  touch logs/django/gunicorn-access.log
  touch logs/django/gunicorn-error.log
  touch logs/nginx/access.log
  touch logs/nginx/error.log
  ```

- [ ] **Sentry configured** (optional but recommended)
  - SENTRY_DSN in .env.production

- [ ] **Uptime monitoring** configured (UptimeRobot, Pingdom, etc.)

---

## Performance

- [ ] **Gunicorn workers** configured appropriately
  - Default: (2 * CPU cores) + 1
  - Adjust in `gunicorn.conf.py` if needed

- [ ] **Database connection pooling** enabled (CONN_MAX_AGE=600)

- [ ] **Static files cached** (Nginx cache headers configured)

- [ ] **Gzip compression** enabled in Nginx

---

## Content Setup

- [ ] **Site settings** configured in admin
  - Site name
  - Contact information
  - Email templates

- [ ] **Shipping zones** created
  - Delivery areas
  - Shipping costs

- [ ] **Tax rules** configured (if applicable)

- [ ] **Product types** created
  - Attributes defined
  - Categories set up

- [ ] **Sample products** added (optional)

- [ ] **Payment methods** tested
  - COD working
  - bKash sandbox tested
  - Other gateways verified

---

## Domain & DNS

- [ ] **Domain pointed** to server IP (A record)

- [ ] **www subdomain** configured (CNAME or A record)

- [ ] **DNS propagation** complete
  ```bash
  nslookup yourdomain.com
  ```

- [ ] **SSL certificate** valid for domain
  ```bash
  curl -I https://yourdomain.com
  ```

---

## Testing

- [ ] **API endpoints** tested
  - Registration: POST /api/v1/auth/register/
  - Login: POST /api/v1/auth/login/
  - Products: GET /api/v1/products/
  - Cart: POST /api/v1/cart/items/
  - Checkout: POST /api/v1/checkout/

- [ ] **Frontend integration** tested
  - CORS working
  - JWT authentication working
  - Image uploads working

- [ ] **Email sending** tested
  - Order confirmation email
  - Password reset email

- [ ] **Order workflow** tested end-to-end
  - Add to cart
  - Checkout
  - Payment (COD)
  - Order confirmation
  - Status updates

---

## Documentation

- [ ] **README.md** updated with production info

- [ ] **DEPLOYMENT.md** reviewed and customized

- [ ] **API documentation** accessible (Swagger UI)

- [ ] **Team trained** on deployment process

---

## Backup & Recovery

- [ ] **Backup script** tested
  ```bash
  bash scripts/backup.sh
  # Check backups/ directory
  ```

- [ ] **Restore procedure** documented and tested

- [ ] **Rollback procedure** tested

---

## Final Checks

- [ ] **Load testing** performed (optional)
  - Use tools like Apache Bench, k6, or Locust

- [ ] **Security scan** performed
  - OWASP ZAP, Nessus, or similar

- [ ] **Accessibility check** (if frontend included)

- [ ] **Mobile responsiveness** (if frontend included)

- [ ] **Cross-browser testing** (if frontend included)

---

## Go-Live

- [ ] **Maintenance page** prepared (optional)

- [ ] **Go-live scheduled** (low-traffic time recommended)

- [ ] **Team notified** of deployment

- [ ] **Monitoring alerts** configured

- [ ] **Support contacts** ready

- [ ] **Deployment executed**
  ```bash
  bash scripts/deploy.sh fresh
  ```

- [ ] **Post-deployment verification**
  - All services healthy
  - Health check passing
  - Admin panel accessible
  - API endpoints working
  - Email sending working

- [ ] **Monitoring dashboard** reviewed

---

## Post-Launch

- [ ] **Monitor logs** for errors
  ```bash
  docker compose -f docker-compose.prod.yml logs -f web
  ```

- [ ] **Monitor performance** (response times, error rates)

- [ ] **Monitor resource usage** (CPU, memory, disk)

- [ ] **First backup** verified

- [ ] **SSL certificate renewal** scheduled (90 days for Let's Encrypt)

---

## Emergency Contacts

**Technical Lead:** [Name, Phone, Email]

**DevOps:** [Name, Phone, Email]

**Hosting Provider:** [Support URL, Phone]

**Domain Registrar:** [Support URL, Phone]

---

## Rollback Plan

If issues arise after deployment:

1. **Immediate rollback:**
   ```bash
   docker compose -f docker-compose.prod.yml down
   git checkout <previous-stable-commit>
   bash scripts/deploy.sh update
   ```

2. **Database restore** (if needed):
   ```bash
   gunzip < backups/db_backup_<timestamp>.sql.gz | \
     docker compose -f docker-compose.prod.yml exec -T db \
     psql -U ecom_user ecom_db
   ```

3. **Notify team** of rollback

4. **Investigate issues** in staging environment

---

## Notes

- This checklist should be completed BEFORE production deployment
- Keep this document updated as infrastructure changes
- Review and update quarterly
- Document any deviations from standard procedure

---

**Deployment Date:** _______________

**Deployed By:** _______________

**Sign-off:** _______________
