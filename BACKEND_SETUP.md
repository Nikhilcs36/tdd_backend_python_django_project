# 🔧 Backend Setup Guide for Frontend Integration

## 🚀 Quick Setup

Your `docker-compose.yml` is already configured:

```yaml
services:
  app:
    container_name: backend  # ← Required: Frontend expects this name
    networks:
      - tdd-network
    # ... other config ...

networks:
  tdd-network:
    external: true  # ← Required: Use pre-existing network
    name: tdd-network
```

## 🏃 Setup Instructions

### Step 1: Create Network (One-time)

```bash
# Create the shared network
docker network create tdd-network

# Verify (Windows)
docker network ls | findstr tdd-network
# Verify (Linux/Mac)
docker network ls | grep tdd-network
```

### Step 2: Start Backend

```bash
docker-compose up -d
```

### Step 3: Verify Running

```bash
docker ps | findstr backend    # Windows
docker ps | grep backend       # Linux/Mac
```

## 🌐 Access Points

| From | URL |
|------|-----|
| Host Machine | `http://localhost:8000` |
| Frontend Container | `http://backend:8000` |

## 🛠️ Troubleshooting

### Network Not Found
```bash
docker network create tdd-network
docker-compose up -d
```

### Container Name Already in Use
```bash
docker-compose down
docker-compose up -d
```

### Port 8000 in Use
```bash
# Windows
netstat -ano | findstr :8000
# Kill the process or change port in docker-compose.yml
```
