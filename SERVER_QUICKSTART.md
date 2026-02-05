# 🚀 Zero-Config Server Setup

## One-Time Server Setup (5 minutes)

SSH to your server and run these commands:

```bash
ssh arafat@ecom.arafat2.me

# 1. Add user to docker group (no more sudo needed)
sudo usermod -aG docker $USER
newgrp docker

# 2. Install Nginx
sudo apt update
sudo apt install -y nginx

# 3. Configure Nginx
sudo tee /etc/nginx/sites-available/ecom << 'EOF'
upstream django {
    server 127.0.0.1:8000;
}

server {
    listen 80;
    server_name ecom.arafat2.me 165.22.217.133;
    client_max_body_size 100M;

    location /static/ {
        alias /home/arafat/ecommerce/staticfiles/;
        expires 30d;
    }

    location /media/ {
        alias /home/arafat/ecommerce/media/;
        expires 30d;
    }

    location / {
        proxy_pass http://django;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
EOF

# 4. Enable site
sudo ln -sf /etc/nginx/sites-available/ecom /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default
sudo nginx -t
sudo systemctl restart nginx

# 5. Setup firewall
sudo ufw allow 'Nginx Full'
sudo ufw allow OpenSSH
sudo ufw --force enable

# 6. Optional: SSL (later, after first deploy works)
# sudo apt install -y certbot python3-certbot-nginx
# sudo certbot --nginx -d ecom.arafat2.me
```

## ✅ That's It!

Now:
1. **Push code:** `git push origin master`
2. **GitHub Actions deploys automatically**
3. **Visit:** http://165.22.217.133/admin/

First deployment takes ~3 minutes (downloads images, runs migrations, creates DB).

---

## Create Superuser (After First Deploy)

```bash
ssh arafat@ecom.arafat2.me
cd ~/ecommerce
docker compose -f docker-compose.prod.yml exec web python manage.py createsuperuser
```

---

## Useful Commands

```bash
# View logs
cd ~/ecommerce
docker compose -f docker-compose.prod.yml logs -f web

# Restart
docker compose -f docker-compose.prod.yml restart

# Check status
docker compose -f docker-compose.prod.yml ps

# Manual deploy (if needed)
cd ~/ecommerce
git pull origin master
docker compose -f docker-compose.prod.yml up -d
```

---

## Troubleshooting

**"Permission denied" on docker?**
```bash
sudo usermod -aG docker $USER
newgrp docker
```

**Containers won't start?**
```bash
cd ~/ecommerce
docker compose -f docker-compose.prod.yml logs
```

**Nginx errors?**
```bash
sudo nginx -t
sudo systemctl status nginx
```

**Database errors?**
```bash
cd ~/ecommerce
docker compose -f docker-compose.prod.yml exec db psql -U ecom_user -d ecom_prod
```
