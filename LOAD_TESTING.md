# 🔥 Load Testing with Locust - Quick Start Guide

## 🚀 How to Run

### Option 1: Start Everything (Web + Database + Locust)
```bash
docker compose -f docker-compose.dev.yml --profile testing up --build
```

### Option 2: Start Web First, Then Locust Separately
```bash
# Terminal 1 - Start web and database
docker compose -f docker-compose.dev.yml up --build

# Terminal 2 - Start Locust (after web is running)
docker compose -f docker-compose.dev.yml up locust
```

### Option 3: Locust Only (if web already running)
```bash
docker compose -f docker-compose.dev.yml --profile testing up locust
```

---

## 📊 Access Locust Web UI

1. Open browser: **http://localhost:8089**
2. You'll see the Locust start screen

### Configure Your Test:
- **Number of users (peak)**: Start with `10`, then try `50`, `100`, `500`
- **Spawn rate**: `1` or `2` users/second (gradual ramp-up)
- **Host**: Already set to `http://web:8000` (internal Docker network)
- Click **Start swarming**

---

## 🎯 Understanding the Test Scenarios

The `locustfile.py` defines 4 user types:

### 1. AnonymousBrowser (80% of users)
- Browses products, searches, views categories
- Simulates window shoppers
- Wait time: 1-3 seconds between actions

### 2. ShoppingUser (20% of users)
- Views cart, checks shipping, browses products
- Simulates serious buyers
- Wait time: 2-5 seconds

### 3. AdminUser (<1% of users)
- Accesses admin panel
- Very rare, but tests admin load
- Wait time: 10-30 seconds

### 4. APIStressTest (DISABLED by default)
- Rapid-fire requests for stress testing
- Edit `locustfile.py` and change `weight = 0` to `weight = 1` to enable
- Wait time: 0.1-0.5 seconds (VERY fast)

---

## 📈 Progressive Testing Strategy

### Test 1: Baseline (Light Load)
```
Users: 10
Spawn rate: 1/sec
Duration: 2 minutes
```
**Expected:** All green, <500ms response time

### Test 2: Normal Load
```
Users: 50
Spawn rate: 2/sec
Duration: 5 minutes
```
**Expected:** Mostly green, <1000ms response time

### Test 3: Peak Load
```
Users: 100
Spawn rate: 5/sec
Duration: 5 minutes
```
**Expected:** Some yellow, may see slower responses

### Test 4: Stress Test
```
Users: 200
Spawn rate: 10/sec
Duration: 3 minutes
```
**Expected:** Find breaking point, watch for errors

### Test 5: Spike Test
```
Users: 500
Spawn rate: 50/sec
Duration: 1 minute
```
**Expected:** Definitely breaking, check error rate

---

## 🎮 Using the Locust UI

### Main Charts:
1. **Total Requests per Second (RPS)** - How many requests handled
2. **Response Times** - 50th, 95th, 99th percentiles
3. **Number of Users** - Current active users

### Statistics Table:
- **Type**: HTTP method
- **Name**: Endpoint path
- **# Requests**: Total requests made
- **# Fails**: Failed requests
- **Median (ms)**: 50th percentile response time
- **95%ile (ms)**: 95th percentile response time
- **Average (ms)**: Average response time
- **Min/Max**: Fastest and slowest requests
- **RPS**: Requests per second for this endpoint

### Color Coding:
- 🟢 Green: <500ms response time
- 🟡 Yellow: 500ms-1000ms
- 🔴 Red: >1000ms or errors

---

## 🔧 Monitoring While Testing

### Check Docker Stats (In Another Terminal)
```bash
docker stats ecom_web ecom_db ecom_locust
```

You'll see:
- CPU% - How much CPU each container uses
- MEM USAGE / LIMIT - Memory consumption
- NET I/O - Network throughput

### Check Web Logs
```bash
docker compose -f docker-compose.dev.yml logs -f web
```

Watch for:
- Database query times
- Error messages
- Slow endpoint warnings

---

## 📊 What to Look For

### Good Performance Indicators:
✅ Response times under 500ms (p95)
✅ Zero failures
✅ Stable RPS as users increase
✅ CPU usage under 70%
✅ Memory stable

### Warning Signs:
⚠️ Response times over 1 second
⚠️ Increasing failure rate
⚠️ RPS plateauing as users increase
⚠️ CPU hitting 90%+
⚠️ Memory constantly increasing

### Breaking Point Indicators:
🔴 High failure rate (>1%)
🔴 Response times over 5 seconds
🔴 Container crashes
🔴 Database connection errors
🔴 OOM (Out of Memory) errors

---

## 🎯 Example Testing Session

```bash
# 1. Start everything
docker compose -f docker-compose.dev.yml --profile testing up --build

# 2. Open http://localhost:8089

# 3. Run baseline test
#    Users: 10, Spawn: 1/sec
#    Watch for 2 minutes, note RPS and response times

# 4. Stop test, wait 30 seconds

# 5. Run normal load test
#    Users: 50, Spawn: 2/sec
#    Watch for 5 minutes

# 6. Stop test, wait 30 seconds

# 7. Run stress test
#    Users: 100, Spawn: 5/sec
#    Watch for breaking point

# 8. Stop test

# 9. Export results (Download Data tab in Locust UI)

# 10. Stop containers
#     Ctrl+C or: docker compose -f docker-compose.dev.yml down
```

---

## 🔥 Advanced: Enable Stress Test Mode

Edit `locustfile.py`:

```python
class APIStressTest(HttpUser):
    weight = 1  # Change from 0 to 1 (or higher for more aggressive)
```

This will add rapid-fire requests to your test mix.

**WARNING:** This can overwhelm your local machine. Use with caution!

---

## 💡 Tips & Tricks

### 1. Edit Tests Live
You can edit `locustfile.py` while Locust is running. Click "Restart" in the UI to reload.

### 2. Headless Mode (No UI)
```bash
docker compose -f docker-compose.dev.yml run --rm locust \
    -f /mnt/locust/locustfile.py \
    --host=http://web:8000 \
    --users 50 \
    --spawn-rate 2 \
    --run-time 5m \
    --headless
```

### 3. Export Results
In Locust UI, go to "Download Data" tab:
- Download statistics CSV
- Download failures CSV
- Download response time distribution

### 4. Custom Scenarios
Edit `locustfile.py` to add your own test scenarios:
```python
@task(5)
def my_custom_test(self):
    self.client.get("/api/v1/my-endpoint/")
```

---

## 🆘 Troubleshooting

**"Connection refused" errors:**
- Make sure web service is healthy: `docker compose -f docker-compose.dev.yml ps`
- Check logs: `docker compose -f docker-compose.dev.yml logs web`

**Locust UI not accessible:**
- Check port 8089 is not in use: `lsof -i :8089`
- Try restarting: `docker compose -f docker-compose.dev.yml restart locust`

**Tests running too slow:**
- Reduce spawn rate
- Reduce number of users
- Check your machine's CPU/RAM usage

**Container keeps crashing:**
- You've found the breaking point! Reduce load.
- Check: `docker compose -f docker-compose.dev.yml logs web`

---

## 📈 Expected Results (Rough Estimates)

For typical development machine (4 CPU cores, 16GB RAM):

| Users | Expected RPS | Expected Response Time | Status |
|-------|--------------|------------------------|--------|
| 10 | 30-50 | <200ms | ✅ Comfortable |
| 50 | 100-150 | <500ms | ✅ Good |
| 100 | 150-250 | <1000ms | 🟡 Acceptable |
| 200 | 200-300 | 1-3 seconds | 🟠 Stressed |
| 500+ | Variable | 5+ seconds | 🔴 Breaking |

**Note:** These are rough estimates. Your actual results will vary based on:
- Your machine specs
- Database query complexity
- Whether you have products/data in database
- What other apps are running

---

## ✅ Quick Commands Reference

```bash
# Start with Locust
docker compose -f docker-compose.dev.yml --profile testing up --build

# Start without Locust (normal dev)
docker compose -f docker-compose.dev.yml up --build

# Stop everything
docker compose -f docker-compose.dev.yml down

# View logs
docker compose -f docker-compose.dev.yml logs -f web
docker compose -f docker-compose.dev.yml logs -f locust

# Restart just Locust
docker compose -f docker-compose.dev.yml restart locust

# Remove everything (including volumes)
docker compose -f docker-compose.dev.yml down -v
```

---

**Ready to test? 🚀**

```bash
docker compose -f docker-compose.dev.yml --profile testing up --build
```

Then open: **http://localhost:8089**
