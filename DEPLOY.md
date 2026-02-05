# 🚀 Deployment Guide - Step by Step

## Prerequisites Checklist

- [x] DigitalOcean Droplet (Ubuntu 24.04 LTS) - **165.22.217.133**
- [x] Domain DNS configured: **ecom.arafat2.me → 165.22.217.133**
- [x] SSH access: **arafat@ecom.arafat2.me**
- [x] Nginx installed
- [x] SSH key setup
- [ ] GitHub repository with code
- [ ] GitHub Actions enabled

---

## Part 1: One-Time Server Setup (On DigitalOcean)

### Step 1: Connect to Server

```bash
ssh arafat@ecom.arafat2.me
```

### Step 2: Download and Run Setup Script

```bash
cd ~
wget https://raw.githubusercontent.com/YOUR_USERNAME/YOUR_REPO/main/scripts/server_setup.sh
chmod +x server_setup.sh
./server_setup.sh
```

This script will:
- Install Docker & Docker Compose
- Configure Nginx with SSL (Let's Encrypt)
- Setup firewall
- Create application directories

### Step 3: Clone Your Repository

```bash
cd /opt/ecommerce
git clone https://github.com/YOUR_USERNAME/YOUR_REPO.git .
```

If you haven't pushed yet, do it from your local machine first!

### Step 4: Configure Production Environment

```bash
cd /opt/ecommerce
nano .env.production
```

**Update these values:**

```bash
# Generate SECRET_KEY
SECRET_KEY=$(openssl rand -base64 50)

# Set strong database password
DB_PASSWORD=$(openssl rand -base64 32)

# Update GitHub repository
GITHUB_REPOSITORY=your-username/website_3

# Set email (if you have Gmail)
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-gmail-app-password
```

Save and exit (Ctrl+X, Y, Enter)

### Step 5: Login to GitHub Container Registry

```bash
# Create GitHub Personal Access Token (PAT):
# GitHub → Settings → Developer settings → Personal access tokens → Tokens (classic)
# Generate with 'read:packages' permission

# Login
docker login ghcr.io -u YOUR_GITHUB_USERNAME
# Password: paste your PAT
```

### Step 6: Initial Deployment (Manual)

```bash
cd /opt/ecommerce

# Build and start services
docker compose -f docker-compose.prod.yml up -d

# Wait for services to start (30 seconds)
sleep 30

# Run migrations
docker compose -f docker-compose.prod.yml exec web python manage.py migrate

# Create superuser
docker compose -f docker-compose.prod.yml exec web python manage.py createsuperuser

# Collect static files
docker compose -f docker-compose.prod.yml exec web python manage.py collectstatic --noinput
```

### Step 7: Verify Deployment

```bash
# Check services are running
docker compose -f docker-compose.prod.yml ps

# Test health endpoint
curl https://ecom.arafat2.me/api/v1/health/

# Check logs
docker compose -f docker-compose.prod.yml logs -f web
```

**Visit in browser:**
- **API Health**: https://ecom.arafat2.me/api/v1/health/
- **Admin Panel**: https://ecom.arafat2.me/admin/
- **API Docs**: https://ecom.arafat2.me/api/v1/docs/

---

## Part 2: GitHub Actions CI/CD Setup

### Step 1: Get SSH Private Key

**On your LOCAL machine:**

```bash
cat ~/.ssh/id_rsa
```

Copy the ENTIRE output (including `-----BEGIN` and `-----END` lines)

### Step 2: Add GitHub Secrets

Go to your GitHub repository:

**Settings → Secrets and variables → Actions → New repository secret**

Add these 3 secrets:

| Name | Value |
|------|-------|
| `DO_HOST` | `165.22.217.133` |
| `DO_USERNAME` | `arafat` |
| `DO_SSH_KEY` | Paste your SSH private key |

### Step 3: Push CI/CD Workflow

**On your LOCAL machine:**

```bash
cd /home/arafat/Documents/Code/Platform/website_3

# Add all files
git add .

# Commit
git commit -m "Add CI/CD deployment pipeline"

# Push to GitHub
git push origin main
```

### Step 4: Watch First Deployment

1. Go to GitHub repository
2. Click **Actions** tab
3. Watch the workflow run
4. If successful, your app auto-deploys! 🎉

---

## Part 3: Daily Workflow (After Setup)

### Make Changes and Deploy

```bash
# 1. Make your code changes locally
# 2. Test locally
docker compose -f docker-compose.dev.yml up

# 3. Commit and push
git add .
git commit -m "Your changes"
git push origin main

# 4. GitHub Actions automatically:
#    - Builds Docker image
#    - Runs tests
#    - Deploys to server
#    - Runs migrations
#    - Restarts services
```

**No manual deployment needed!** ✨

---

## Useful Commands

### On Server (SSH)

```bash
# View logs
docker compose -f docker-compose.prod.yml logs -f web

# Restart services
docker compose -f docker-compose.prod.yml restart web

# Run Django commands
docker compose -f docker-compose.prod.yml exec web python manage.py shell

# Check database
docker compose -f docker-compose.prod.yml exec db psql -U ecom_user -d ecom_prod

# Backup database
docker compose -f docker-compose.prod.yml exec db pg_dump -U ecom_user ecom_prod > backup.sql
```

### On Local Machine

```bash
# Test before pushing
docker compose -f docker-compose.dev.yml up
docker compose -f docker-compose.dev.yml exec web python manage.py test

# Manual deployment trigger (if needed)
# GitHub → Actions → Deploy workflow → Run workflow
```

---

## Troubleshooting

### SSL Certificate Issues
```bash
sudo certbot certonly --standalone -d ecom.arafat2.me --force-renew
sudo systemctl restart nginx
```

### Container Won't Start
```bash
docker compose -f docker-compose.prod.yml logs web
docker compose -f docker-compose.prod.yml restart
```

### Clear Everything and Restart
```bash
docker compose -f docker-compose.prod.yml down
docker compose -f docker-compose.prod.yml up -d
```

---

## Security Checklist

- [x] Firewall enabled (UFW)
- [x] SSH key-based authentication
- [x] SSL/TLS certificate (Let's Encrypt)
- [x] Strong database password
- [x] Django DEBUG=False in production
- [x] Obscured admin URL
- [x] CORS configured
- [x] Security headers in Nginx

---

## 📊 Monitoring

**Check application health:**
```bash
curl https://ecom.arafat2.me/api/v1/health/
```

**Monitor resources:**
```bash
docker stats
htop
df -h
```

**View all logs:**
```bash
# Django logs
docker compose -f docker-compose.prod.yml logs -f web

# Nginx logs
sudo tail -f /var/log/nginx/access.log
sudo tail -f /var/log/nginx/error.log

# System logs
sudo journalctl -u nginx -f
```

---

## 🎯 Next Steps After Deployment

1. **Setup Backups**: Configure automatic database backups
2. **Add Monitoring**: Sentry for error tracking
3. **Configure Storage**: Setup Cloudflare R2 or DO Spaces for media files
4. **Email Service**: Configure production email SMTP
5. **Payment Gateways**: Add bKash/Nagad credentials
6. **Performance**: Setup Redis caching
7. **Analytics**: Add Google Analytics or similar

---

**Your deployment is ready! 🚀**

Questions? Check logs first, then GitHub Actions output.
