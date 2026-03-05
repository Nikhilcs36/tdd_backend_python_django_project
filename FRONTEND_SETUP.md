# 🎨 Frontend Setup Guide

## 🚀 Quick Setup

Update your `docker-compose.yml`:

```yaml
services:
  frontend:
    # ... your existing configuration ...
    networks:
      - tdd-network
    # ... rest of config ...

networks:
  tdd-network:
    external: true  # ← Required: Use pre-existing network
    name: tdd-network
```

## 🏃 Setup Instructions

### Prerequisites
- Backend team has created the network (`tdd-network`)
- Backend container is running with name `backend`

### Step 1: Configure API URL

Set your API base URL to:
```
http://backend:8000
```

Example (React/Vite):
```javascript
// .env
VITE_API_URL=http://backend:8000
```

Example (Axios):
```javascript
axios.defaults.baseURL = 'http://backend:8000';
```

### Step 2: Start Frontend

```bash
docker-compose up -d
```

### Step 3: Verify Connection

```bash
# Test from frontend container
docker exec -it frontend wget -qO- http://backend:8000/api/health/
```

## 🌐 Access Points

| From | URL |
|------|-----|
| Frontend Container → Backend | `http://backend:8000` |
| Host → Frontend | `http://localhost:3000` (or your port) |
| Host → Backend | `http://localhost:8000` |

## 🛠️ Troubleshooting

### Network Not Found
**Error:** `Network tdd-network declared as external, but could not be found`

**Solution:** Ask backend team to create the network:
```bash
docker network create tdd-network
```

### Cannot Connect to Backend
**Check:**
```bash
# Is backend running?
docker ps | findstr backend    # Windows
docker ps | grep backend       # Linux/Mac

# Is backend connected to network?
docker network inspect tdd-network
```

### Connection Refused
- Verify backend is fully started (may need time to initialize)
- Check backend logs: `docker logs backend`
- Ensure API URL is `http://backend:8000` (not localhost)

## 📋 API Endpoints

| Endpoint | URL |
|----------|-----|
| Base API | `http://backend:8000` |
| Health Check | `http://backend:8000/api/health/` |
