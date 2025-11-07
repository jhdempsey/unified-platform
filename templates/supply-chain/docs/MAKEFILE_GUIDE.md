# Makefile Quick Reference

## 🚀 **Complete Workflow**

### **First Time Setup**
```bash
# 1. Install dependencies
make install

# 2. Create .env file
make setup-env
# Then edit .env and add your ANTHROPIC_API_KEY

# 3. Start infrastructure
make infra-up

# 4. Start services
make start
```

### **Daily Development**
```bash
# Start everything
make infra-up
make start

# Check status
make status
make health

# View logs
make logs

# Stop everything
make stop
make infra-down
```

---

## 📋 **All Commands**

### **Setup & Installation**
```bash
make install       # Install Python dependencies
make setup-env     # Create .env template
```

### **Infrastructure (Docker)**
```bash
make infra-up      # Start Kafka, PostgreSQL, Redis, etc.
make infra-down    # Stop Docker services
make infra-status  # Check Docker services
```

### **Application Services**
```bash
make start         # Start all services in background
make stop          # Stop all services
make restart       # Restart all services
make status        # Show running services with PIDs
```

### **Monitoring & Logs**
```bash
make logs              # Tail all logs
make logs-product      # Tail Product Service only
make logs-generator    # Tail Product Generator only
make logs-discovery    # Tail Discovery Agent only
make logs-analysis     # Tail Stream Analysis only
```

### **Health & Testing**
```bash
make health        # Check health of all services
make test          # Run smoke tests
```

### **Cleanup**
```bash
make clean         # Remove logs and PID files
make clean-all     # Stop services + clean
```

---

## 🎯 **Common Workflows**

### **Start Fresh Development Session**
```bash
make infra-up && make start
make logs  # Watch logs in real-time
```

### **Check if Everything is Running**
```bash
make status
make health
```

### **Restart a Stuck Service**
```bash
make restart
```

### **Debug a Specific Service**
```bash
# Stop all background services
make stop

# Run the problematic service manually
pipenv shell
cd services/product-service
python main.py
# See errors directly
```

### **End of Day Cleanup**
```bash
make stop
make infra-down
```

---

## 🔧 **How It Works**

### **Process Management**
- Services start in **background** with `&`
- PIDs saved to `.pids` file
- `make stop` kills all PIDs from `.pids`
- Logs saved to `logs/` directory

### **Environment Variables**
- Loaded from `.env` file automatically
- Use `set -a; source .env; set +a` in Makefile
- Override with: `ANTHROPIC_API_KEY=xxx make start`

### **Logs**
All logs go to `logs/` directory:
```
logs/
├── product-service.log
├── product-generator.log
├── discovery-agent.log
└── stream-analysis.log
```

---

## ⚠️ **Troubleshooting**

### **"Services may already be running"**
```bash
make stop
rm -f .pids  # Force clean
make start
```

### **Port already in use**
```bash
# Find what's using the port
lsof -i :8001

# Kill it
kill -9 <PID>
```

### **Services start but immediately die**
```bash
# Check logs
make logs-product

# Or run manually to see errors
pipenv shell
cd services/product-service
python main.py
```

### **Infrastructure not healthy**
```bash
make infra-down
docker-compose down -v  # Remove volumes
make infra-up
```

---

## 💡 **Pro Tips**

### **Watch Logs in Another Terminal**
```bash
# Terminal 1: Start services
make start

# Terminal 2: Watch logs
make logs
```

### **Quick Health Check**
```bash
make health | grep ❌  # See only failed services
```

### **Auto-restart on Code Changes**
For development, run services manually with auto-reload:
```bash
pipenv shell
cd services/product-service
uvicorn main:app --reload --port 8001
```

### **Check Service URLs**
```bash
# After starting
echo "Product Service:   http://localhost:8001/docs"
echo "Product Generator: http://localhost:8003/docs"
echo "Discovery Agent:   http://localhost:8004/docs"
```

---

## 🎉 **Complete Example Session**

```bash
# Morning: Start work
cd ~/Work/AI_Development/platform-monorepo
make infra-up           # Start Docker
make start              # Start services
make health             # Verify everything works

# During development
make logs               # Watch logs (Ctrl+C to exit)
make test               # Run tests

# Make code changes, restart
make restart

# End of day
make stop
make infra-down

# Or just leave infra running:
make stop  # Only stop application services
```

---

## 📊 **Service Ports Quick Reference**

| Service | Port | URL |
|---------|------|-----|
| Product Service | 8001 | http://localhost:8001/docs |
| Product Generator | 8003 | http://localhost:8003/docs |
| Discovery Agent | 8004 | http://localhost:8004/docs |
| PostgreSQL | 5432 | localhost:5432 |
| Redis | 6380 | localhost:6380 |
| Kafka | 19093 | localhost:19093 |
| Schema Registry | 18081 | http://localhost:18081 |
| Prometheus | 9095 | http://localhost:9095 |
| Grafana | 3002 | http://localhost:3002 |

---

**That's it! Use `make help` anytime to see all commands.** 🚀
