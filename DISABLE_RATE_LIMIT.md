# Disable Rate Limiting for Load Testing

## ⚠️ WARNING
**Only disable rate limiting temporarily for testing!**
Re-enable immediately after testing to protect your server.

---

## Option 1: Disable Nginx Rate Limiting (Recommended)

### Step 1: SSH to your VPS
```bash
ssh arafat@ecom.arafat2.me
```

### Step 2: Backup current nginx config
```bash
sudo cp /etc/nginx/sites-available/ecom.arafat2.me /tmp/nginx_backup_$(date +%Y%m%d_%H%M%S).conf
```

### Step 3: Edit nginx config
```bash
sudo nano /etc/nginx/sites-available/ecom.arafat2.me
```

### Step 4: Find and comment out rate limiting lines
Look for lines like these and add `#` at the start:
```nginx
# limit_req_zone $binary_remote_addr zone=api:10m rate=10r/s;
# limit_req zone=api burst=20 nodelay;
# limit_req_status 429;
```

Or if there's a rate limiting block:
```nginx
# http {
#     limit_req_zone $binary_remote_addr zone=api:10m rate=10r/s;
#     limit_req_zone $binary_remote_addr zone=general:10m rate=30r/s;
# }
```

### Step 5: Test nginx config
```bash
sudo nginx -t
```

Should show: `syntax is okay` and `test is successful`

### Step 6: Reload nginx
```bash
sudo systemctl reload nginx
```

### Step 7: Verify rate limiting is disabled
```bash
# Run this on your local machine
for i in {1..100}; do curl -s -o /dev/null -w "%{http_code}\n" https://ecom.arafat2.me/api/v1/health/; done
```

Should see all `200` responses, no `429` errors.

---

## Option 2: Increase Rate Limits (Safer)

Instead of disabling completely, increase limits for testing:

```nginx
# In nginx config, change:
limit_req_zone $binary_remote_addr zone=api:10m rate=10r/s;   # Was 10r/s

# To:
limit_req_zone $binary_remote_addr zone=api:10m rate=1000r/s;  # Now 1000r/s
```

Then reload:
```bash
sudo nginx -t && sudo systemctl reload nginx
```

---

## Option 3: Whitelist Your IP

Add your testing machine's IP to nginx whitelist:

```nginx
# In nginx config
geo $limit {
    default 1;
    YOUR.LOCAL.IP.ADDRESS 0;  # Replace with your actual IP
}

map $limit $limit_key {
    0 "";
    1 $binary_remote_addr;
}

limit_req_zone $limit_key zone=api:10m rate=10r/s;
```

Find your IP:
```bash
curl ifconfig.me
```

---

## After Testing: RE-ENABLE Rate Limiting!

### Restore from backup:
```bash
sudo cp /tmp/nginx_backup_*.conf /etc/nginx/sites-available/ecom.arafat2.me
sudo nginx -t && sudo systemctl reload nginx
```

### Or manually uncomment the lines:
```bash
sudo nano /etc/nginx/sites-available/ecom.arafat2.me
# Remove the # from rate limiting lines
sudo nginx -t && sudo systemctl reload nginx
```

### Verify rate limiting is back:
```bash
# Should see some 429 errors in the mix:
for i in {1..100}; do curl -s -o /dev/null -w "%{http_code}\n" https://ecom.arafat2.me/api/v1/health/; sleep 0.01; done
```

---

## Quick Commands Summary

```bash
# SSH to VPS
ssh arafat@ecom.arafat2.me

# Backup
sudo cp /etc/nginx/sites-available/ecom.arafat2.me /tmp/nginx_backup.conf

# Edit
sudo nano /etc/nginx/sites-available/ecom.arafat2.me
# Comment out rate limit lines with #

# Test & Reload
sudo nginx -t && sudo systemctl reload nginx

# AFTER TESTING - Restore
sudo cp /tmp/nginx_backup.conf /etc/nginx/sites-available/ecom.arafat2.me
sudo nginx -t && sudo systemctl reload nginx
```

---

## Now Run Comprehensive Tests

### 1. Restart Locust with new config
```bash
# On your local machine
cd /home/arafat/Documents/Code/Platform/website_3
docker restart locust_vps_test
```

### 2. Open Locust UI
```
http://localhost:8089
```

### 3. Progressive Load Testing

**Test 1: Baseline (find comfortable level)**
- Users: 10
- Spawn rate: 2/sec
- Duration: 2 minutes
- Expected: All green, <500ms

**Test 2: Normal Load**
- Users: 50
- Spawn rate: 5/sec
- Duration: 3 minutes
- Expected: Mostly green, <1000ms

**Test 3: Peak Load**
- Users: 100
- Spawn rate: 10/sec
- Duration: 3 minutes
- Expected: Some yellow, watch CPU

**Test 4: Stress Test**
- Users: 200
- Spawn rate: 20/sec
- Duration: 2 minutes
- Expected: Find breaking point

**Test 5: Max Capacity**
- Users: 500
- Spawn rate: 50/sec
- Duration: 1 minute
- Expected: Likely breaking, check errors

### 4. Monitor VPS during tests

**Terminal 1 - Resource usage:**
```bash
ssh arafat@ecom.arafat2.me "htop"
```

**Terminal 2 - Docker stats:**
```bash
ssh arafat@ecom.arafat2.me "docker stats ecom_web_prod ecom_db_prod ecom_redis_prod"
```

**Terminal 3 - Logs:**
```bash
ssh arafat@ecom.arafat2.me "docker compose -f ~/ecommerce/docker-compose.prod.yml logs -f web"
```

---

## What to Look For

### Good Signs ✅
- Response times stay under 1 second (p95)
- Failure rate stays at 0%
- CPU usage under 80%
- Memory stable
- No database errors

### Warning Signs ⚠️
- Response times over 2 seconds
- CPU hitting 90%+
- Database connection pool exhausted
- Gunicorn workers timing out

### Breaking Point 🔴
- Failure rate > 1%
- Response times > 5 seconds
- 502/503 errors
- Containers restarting
- Out of memory errors

---

## Expected VPS Capacity

Typical DigitalOcean Droplet performance:

| Droplet Size | Expected RPS | Max Concurrent Users | Response Time (p95) |
|--------------|--------------|---------------------|---------------------|
| 1 vCPU / 1GB | 50-100 | 100-200 | <1s |
| 2 vCPU / 2GB | 150-300 | 300-500 | <800ms |
| 2 vCPU / 4GB | 200-400 | 500-800 | <600ms |
| 4 vCPU / 8GB | 400-800 | 1000-1500 | <500ms |

*Your actual results will vary based on query complexity and data size*

---

## Safety Tips

1. **Test during off-peak hours** (late night/early morning)
2. **Start small** and gradually increase load
3. **Monitor continuously** - be ready to stop if server crashes
4. **Have backup ready** - know how to restore nginx config
5. **Test in stages** - don't jump straight to 500 users
6. **Re-enable rate limiting** immediately after testing

---

## Emergency: Server Crashed?

```bash
# SSH to VPS
ssh arafat@ecom.arafat2.me

# Check container status
docker ps -a

# If containers are down, restart
cd ~/ecommerce
docker compose -f docker-compose.prod.yml restart

# Check logs for errors
docker compose -f docker-compose.prod.yml logs --tail 100 web

# Restore nginx config
sudo cp /tmp/nginx_backup.conf /etc/nginx/sites-available/ecom.arafat2.me
sudo systemctl reload nginx
```
