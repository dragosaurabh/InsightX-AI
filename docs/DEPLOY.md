# InsightX AI - Deployment Guide

This guide covers deploying InsightX AI to production environments.

## Prerequisites

- Docker and Docker Compose installed
- Domain name (for production)
- SSL certificate (Let's Encrypt recommended)
- Google Gemini API key

## Local Development

```bash
# 1. Generate sample data
python scripts/ingest_sample_data.py --rows 50000

# 2. Create .env file
cp .env.example .env
# Edit .env with your GEMINI_API_KEY

# 3. Start services
docker compose -f infra/docker-compose.yml up --build
```

Access at http://localhost:3000

## Production Deployment

### Option 1: VPS Deployment

#### 1. Server Setup

```bash
# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Install Docker Compose
sudo apt-get install docker-compose-plugin
```

#### 2. Clone Repository

```bash
git clone https://github.com/your-org/insightx-ai.git
cd insightx-ai
```

#### 3. Configure Environment

```bash
cp .env.example .env
nano .env
```

Set production values:
```env
GEMINI_API_KEY=your_production_key
GEMINI_MODEL=gemini-1.5-flash
FRONTEND_ORIGIN=https://your-domain.com
NEXT_PUBLIC_API_URL=https://your-domain.com
DATA_PATH=/app/data/transactions.csv
RATE_LIMIT_PER_MIN=20
```

#### 4. Upload Data

```bash
# Upload your transaction CSV
scp local_transactions.csv user@server:/path/to/insightx-ai/data/transactions.csv
```

#### 5. Configure Nginx for SSL

Edit `infra/nginx.conf` and uncomment SSL sections:
```nginx
# Uncomment these lines:
listen 443 ssl http2;
ssl_certificate /etc/nginx/ssl/fullchain.pem;
ssl_certificate_key /etc/nginx/ssl/privkey.pem;
```

#### 6. Generate SSL Certificate

```bash
# Install Certbot
sudo apt install certbot

# Generate certificate
sudo certbot certonly --standalone -d your-domain.com

# Copy to project
sudo cp /etc/letsencrypt/live/your-domain.com/fullchain.pem infra/ssl/
sudo cp /etc/letsencrypt/live/your-domain.com/privkey.pem infra/ssl/
```

#### 7. Start Services

```bash
# Start with nginx profile
docker compose -f infra/docker-compose.yml --profile with-nginx up -d --build
```

#### 8. Verify Deployment

```bash
# Check health
curl https://your-domain.com/api/health

# View logs
docker compose -f infra/docker-compose.yml logs -f
```

### Option 2: Cloud Platform Deployment

#### Render.com

**Backend:**
1. Create new Web Service
2. Connect GitHub repo
3. Set:
   - Root Directory: `backend`
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
4. Add environment variables from `.env.example`

**Frontend:**
1. Create new Static Site
2. Set:
   - Root Directory: `frontend/nextjs-app`
   - Build Command: `npm ci && npm run build`
   - Publish Directory: `.next`
3. Set `NEXT_PUBLIC_API_URL` to backend URL

#### Vercel (Frontend) + Railway (Backend)

**Frontend on Vercel:**
```bash
cd frontend/nextjs-app
vercel
```

**Backend on Railway:**
1. Create new project from GitHub
2. Select `backend` directory
3. Add environment variables
4. Deploy

### Option 3: Kubernetes

See `infra/k8s/` for Kubernetes manifests (if created).

## Production Checklist

- [ ] GEMINI_API_KEY is set (not placeholder)
- [ ] FRONTEND_ORIGIN matches actual domain
- [ ] SSL/TLS enabled (HTTPS only)
- [ ] Rate limiting configured
- [ ] Logs configured and rotated
- [ ] Health checks enabled
- [ ] Backup strategy for data
- [ ] Monitoring/alerting setup

## Scaling

### Horizontal Scaling

```yaml
# docker-compose.yml
services:
  backend:
    deploy:
      replicas: 3
```

### Redis for Sessions

Enable Redis for distributed session storage:
```env
REDIS_URL=redis://redis:6379/0
```

Start with Redis profile:
```bash
docker compose -f infra/docker-compose.yml --profile with-redis up -d
```

## Monitoring

### Health Check

```bash
curl http://localhost:8000/api/health
```

### Logs

```bash
# All services
docker compose logs -f

# Backend only
docker compose logs -f backend
```

### Metrics

The backend exposes execution times in responses for monitoring.

## Troubleshooting

### Backend not starting
```bash
# Check logs
docker compose logs backend

# Common issues:
# - Missing GEMINI_API_KEY
# - DATA_PATH file not found
```

### Frontend can't reach backend
```bash
# Check NEXT_PUBLIC_API_URL is correct
# Check CORS settings (FRONTEND_ORIGIN)
# Check network connectivity
```

### LLM Rate Limiting
```bash
# Increase rate limit
RATE_LIMIT_PER_MIN=30
```

## SSL Certificate Renewal

```bash
# Renew with Certbot
sudo certbot renew

# Copy new certificates
sudo cp /etc/letsencrypt/live/your-domain.com/*.pem infra/ssl/

# Restart nginx
docker compose restart nginx
```
