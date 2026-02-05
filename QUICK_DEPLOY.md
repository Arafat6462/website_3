# Quick Deployment Guide

## Your GitHub Repository
**Repo:** https://github.com/Arafat6462/website_3  
**Username:** Arafat6462  
**Server:** ecom.arafat2.me (165.22.217.133)

---

## Step 1: Push Code to GitHub (On Your Local Machine)

```bash
cd /home/arafat/Documents/Code/Platform/website_3

git add .
git commit -m "Add deployment configuration"
git push origin master
```

---

## Step 2: Setup GitHub Secrets (On GitHub Website)

### Go to: https://github.com/Arafat6462/website_3/settings/secrets/actions

Add these 4 secrets:

| Secret Name | Value | How to Get |
|-------------|-------|------------|
| `DO_HOST` | `165.22.217.133` | Your server IP |
| `DO_USERNAME` | `arafat` | Your SSH username |
| `DO_SSH_KEY` | Your private key | Run: `cat ~/.ssh/id_rsa` |
| `CR_PAT` | GitHub token | See below ⬇️ |

### Create GitHub Personal Access Token:
1. Go to: https://github.com/settings/tokens
2. Click **"Generate new token (classic)"**
3. Name: `Docker Registry`
4. Check boxes: ✅ `write:packages` ✅ `read:packages`
5. Click **Generate token**
6. Copy the token and save as `CR_PAT` secret

---

## Step 3: Run Server Setup (SSH to DigitalOcean)

```bash
# SSH to your server
ssh arafat@ecom.arafat2.me

# Clone repository
git clone https://github.com/Arafat6462/website_3.git ~/ecommerce
cd ~/ecommerce

# Run setup script (installs Docker, Nginx, SSL, etc.)
chmod +x scripts/server_setup.sh
sudo ./scripts/server_setup.sh

# This takes ~5 minutes. It will:
# ✓ Install Docker & Docker Compose
# ✓ Install Nginx
# ✓ Setup SSL certificate for ecom.arafat2.me
# ✓ Configure firewall
# ✓ Create application directories
```

---

## Step 4: Configure Environment & Deploy

### Option A: Use Automated Script (Recommended)

```bash
# Create app directory
sudo mkdir -p /opt/ecommerce
sudo chown -R arafat:arafat /opt/ecommerce
cd /opt/ecommerce

# Copy deployment script
cp ~/ecommerce/deploy_commands.sh .
cp ~/ecommerce/.env.production .
chmod +x deploy_commands.sh

# Edit database password
nano .env.production
# Change line 20: DB_PASSWORD=your_strong_password_here
# Save: Ctrl+X, Y, Enter

# Run deployment script
./deploy_commands.sh
# It will ask for your GitHub token - paste it when prompted
```

### Option B: Manual Commands

```bash
cd /opt/ecommerce

# 1. Login to GitHub Container Registry
# First, create token at: https://github.com/settings/tokens
# Then run:
echo YOUR_GITHUB_TOKEN | docker login ghcr.io -u Arafat6462 --password-stdin

# 2. Clone repo
git clone https://github.com/Arafat6462/website_3.git .

# 3. Configure environment
cp .env.production .env.production.backup
nano .env.production

# Update these values:
# SECRET_KEY=paste_output_of: openssl rand -base64 50
# DB_PASSWORD=create_strong_password
# GITHUB_REPOSITORY=Arafat6462/website_3

# 4. Start containers
docker compose -f docker-compose.prod.yml up -d

# 5. Run migrations
docker compose -f docker-compose.prod.yml exec web python manage.py migrate

# 6. Create superuser
docker compose -f docker-compose.prod.yml exec web python manage.py createsuperuser

# 7. Collect static files
docker compose -f docker-compose.prod.yml exec web python manage.py collectstatic --noinput

# 8. Test
curl http://localhost:8000/api/v1/health/
```

---

## Step 5: Verify Deployment

Visit these URLs in your browser:

- **Admin Panel:** https://ecom.arafat2.me/admin/
- **API Health:** https://ecom.arafat2.me/api/v1/health/

---

## 🎉 You're Done!

### From now on, automatic deployments:
```bash
# On your local machine
git add .
git commit -m "Your changes"
git push origin master

# GitHub Actions automatically:
# 1. Builds Docker image
# 2. Pushes to registry
# 3. Deploys to server
# 4. Runs migrations
# 5. Restarts containers

# Takes ~3-5 minutes
```

### Monitor deployments:
- **GitHub Actions:** https://github.com/Arafat6462/website_3/actions
- **Server logs:** `docker compose -f /opt/ecommerce/docker-compose.prod.yml logs -f web`

---

## Useful Commands

```bash
# View logs
docker compose -f /opt/ecommerce/docker-compose.prod.yml logs -f web

# Restart containers
docker compose -f /opt/ecommerce/docker-compose.prod.yml restart

# Stop everything
docker compose -f /opt/ecommerce/docker-compose.prod.yml down

# Check container status
docker compose -f /opt/ecommerce/docker-compose.prod.yml ps

# Run Django commands
docker compose -f /opt/ecommerce/docker-compose.prod.yml exec web python manage.py shell

# Database backup
docker compose -f /opt/ecommerce/docker-compose.prod.yml exec db pg_dump -U ecom_user ecom_prod > backup.sql
```

---

## Troubleshooting

**Container won't start?**
```bash
docker compose -f /opt/ecommerce/docker-compose.prod.yml logs web
```

**Database connection error?**
```bash
# Check DB is running
docker compose -f /opt/ecommerce/docker-compose.prod.yml ps db

# Check DB password in .env.production matches
grep DB_PASSWORD /opt/ecommerce/.env.production
```

**SSL not working?**
```bash
sudo certbot renew --dry-run
sudo nginx -t
sudo systemctl restart nginx
```

**Need to rebuild image?**
```bash
# Trigger GitHub Actions manually:
# Go to: https://github.com/Arafat6462/website_3/actions
# Click "Deploy to DigitalOcean"
# Click "Run workflow"
```
