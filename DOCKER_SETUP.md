# Docker Setup Guide

This guide walks you through using the containerized full-stack application locally and deploying to Azure Container Apps.

## Quick Start (Local Development)

### Prerequisites
- Docker Desktop installed and running
- Docker Compose v3.8+
- 8GB+ RAM available for Docker

### Start All Services

```bash
# From project root
docker-compose up -d

# View logs
docker-compose logs -f

# View specific service logs
docker-compose logs -f frontend
docker-compose logs -f backend
```

### Access the Application
- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health

### Stop Services

```bash
# Stop all services
docker-compose down

# Stop and remove volumes (⚠️ deletes database data)
docker-compose down -v
```

---

## Development Workflow

### Hot-Reload is Enabled
Changes to your code will automatically reflect in the containers:
- **Frontend**: Changes to `/frontend/src` trigger Next.js hot-reload
- **Backend**: Changes to `/backend/app` trigger uvicorn hot-reload

### Running Tests

```bash
# Backend unit tests (SQLite)
docker-compose exec backend pytest -q -m "not integration"

# Backend integration tests (Postgres)
docker-compose exec backend pytest -q -m integration

# Verbose output
docker-compose exec backend pytest -vv
```

### Database Operations

```bash
# Run migrations
docker-compose exec backend alembic upgrade head

# Create new migration
docker-compose exec backend alembic revision --autogenerate -m "description"

# Access PostgreSQL shell
docker-compose exec db psql -U postgres -d llmpaa

# View database tables
docker-compose exec db psql -U postgres -d llmpaa -c "\dt"
```

### Rebuilding After Dependency Changes

```bash
# Rebuild all services
docker-compose up --build -d

# Rebuild specific service
docker-compose up --build -d frontend
```

---

## Testing Production Build Locally

To test the production-optimized build without hot-reload:

```bash
# Comment out volume mounts in docker-compose.yml
# Then rebuild
docker-compose up --build

# Frontend will use standalone build
# Backend will use production command (without --reload)
```

---

## Azure Container Apps Deployment

### Prerequisites
- Azure CLI installed (`az --version`)
- Azure subscription with Container Apps enabled
- Azure Container Registry (ACR) created

### Step 1: Create Azure Container Registry

```bash
# Login to Azure
az login

# Create resource group
az group create --name llmpaa-rg --location eastus

# Create ACR
az acr create \
  --name llmpaacr \
  --resource-group llmpaa-rg \
  --sku Basic \
  --admin-enabled true
```

### Step 2: Build and Push Images

```bash
# Login to ACR
az acr login --name llmpaacr

# Build frontend for production (replace backend URL)
docker build \
  --platform linux/amd64 \
  --build-arg NEXT_PUBLIC_API_BASE=https://llmpaa-backend.azurecontainerapps.io \
  -t llmpaacr.azurecr.io/llmpaa-frontend:latest \
  ./frontend

# Build backend
docker build \
  --platform linux/amd64 \
  -t llmpaacr.azurecr.io/llmpaa-backend:latest \
  ./backend

# Tag and push database image
docker pull postgres:15-alpine
docker tag postgres:15-alpine llmpaacr.azurecr.io/llmpaa-db:latest

# Push all images
docker push llmpaacr.azurecr.io/llmpaa-frontend:latest
docker push llmpaacr.azurecr.io/llmpaa-backend:latest
docker push llmpaacr.azurecr.io/llmpaa-db:latest
```

### Step 3: Create Container Apps Environment

```bash
az containerapp env create \
  --name llmpaa-env \
  --resource-group llmpaa-rg \
  --location eastus
```

### Step 4: Deploy Database

```bash
az containerapp create \
  --name llmpaa-db \
  --resource-group llmpaa-rg \
  --environment llmpaa-env \
  --image llmpaacr.azurecr.io/llmpaa-db:latest \
  --target-port 5432 \
  --ingress internal \
  --min-replicas 1 \
  --max-replicas 1 \
  --cpu 0.5 \
  --memory 1.0Gi \
  --env-vars \
    POSTGRES_USER=postgres \
    POSTGRES_PASSWORD=secretref:db-password \
    POSTGRES_DB=llmpaa \
  --secrets db-password=your-secure-password \
  --registry-server llmpaacr.azurecr.io
```

### Step 5: Deploy Backend

```bash
# Get ACR credentials
ACR_USERNAME=$(az acr credential show --name llmpaacr --query username -o tsv)
ACR_PASSWORD=$(az acr credential show --name llmpaacr --query passwords[0].value -o tsv)

az containerapp create \
  --name llmpaa-backend \
  --resource-group llmpaa-rg \
  --environment llmpaa-env \
  --image llmpaacr.azurecr.io/llmpaa-backend:latest \
  --target-port 8000 \
  --ingress external \
  --min-replicas 0 \
  --max-replicas 3 \
  --cpu 0.5 \
  --memory 1.0Gi \
  --env-vars \
    APP_ENV=production \
    API_KEY=secretref:api-key \
    DB_HOST=llmpaa-db \
    DB_USER=postgres \
    DB_PASS=secretref:db-password \
    DB_NAME=llmpaa \
    DATABASE_URL=secretref:database-url \
    ENCRYPTION_KEY=secretref:encryption-key \
    FRONTEND_URL=https://llmpaa-frontend.azurecontainerapps.io \
  --secrets \
    api-key=your-api-key-here \
    db-password=your-secure-password \
    database-url=postgresql://postgres:your-secure-password@llmpaa-db:5432/llmpaa \
    encryption-key=your-fernet-key-here \
  --registry-server llmpaacr.azurecr.io \
  --registry-username "$ACR_USERNAME" \
  --registry-password "$ACR_PASSWORD"
```

### Step 6: Deploy Frontend

```bash
az containerapp create \
  --name llmpaa-frontend \
  --resource-group llmpaa-rg \
  --environment llmpaa-env \
  --image llmpaacr.azurecr.io/llmpaa-frontend:latest \
  --target-port 3000 \
  --ingress external \
  --min-replicas 0 \
  --max-replicas 5 \
  --cpu 0.25 \
  --memory 0.5Gi \
  --registry-server llmpaacr.azurecr.io \
  --registry-username "$ACR_USERNAME" \
  --registry-password "$ACR_PASSWORD"
```

### Step 7: Get Application URLs

```bash
# Get backend URL
az containerapp show \
  --name llmpaa-backend \
  --resource-group llmpaa-rg \
  --query properties.configuration.ingress.fqdn -o tsv

# Get frontend URL
az containerapp show \
  --name llmpaa-frontend \
  --resource-group llmpaa-rg \
  --query properties.configuration.ingress.fqdn -o tsv
```

### Step 8: Run Database Migrations

```bash
# Connect to backend container
az containerapp exec \
  --name llmpaa-backend \
  --resource-group llmpaa-rg \
  --command "alembic upgrade head"
```

---

## Troubleshooting

### Frontend won't build
- **Issue**: `pnpm-lock.yaml` out of sync
- **Solution**: Delete `frontend/node_modules` and rebuild

### Backend health check fails
- **Issue**: curl not installed in container
- **Solution**: Backend Dockerfile includes curl (already configured)

### CORS errors in production
- **Issue**: Frontend URL not in CORS allowed origins
- **Solution**: Verify `FRONTEND_URL` env var in backend matches frontend URL

### Database connection refused
- **Issue**: Backend can't reach database
- **Solution**: Check `DB_HOST=db` in docker-compose or `DB_HOST=llmpaa-db` in Azure

### Hot-reload not working
- **Issue**: Volume mounts incorrect
- **Solution**: Check paths in docker-compose.yml match your project structure

### ARM Mac build issues
- **Issue**: Images won't run in Azure (built for ARM)
- **Solution**: Use `--platform linux/amd64` flag when building

---

## Environment Variables Reference

### Frontend
- `NEXT_PUBLIC_API_BASE` - Backend API URL (build-time only)

### Backend
- `APP_ENV` - Environment (dev/production)
- `API_KEY` - API key for secured endpoints
- `DB_HOST` - Database host (db or llmpaa-db)
- `DB_USER` - Database username
- `DB_PASS` - Database password
- `DB_NAME` - Database name
- `DATABASE_URL` - Full PostgreSQL connection string
- `MOCK_LLM` - Use mock LLM responses (true/false)
- `ENCRYPTION_KEY` - Fernet key for credential encryption
- `FRONTEND_URL` - Frontend URL for CORS
- `JWT_SECRET` - Secret for JWT signing
- `OPENAI_API_KEY` - OpenAI API key (optional)
- `LANGCHAIN_API_KEY` - LangChain API key (optional)

### Database
- `POSTGRES_USER` - PostgreSQL username
- `POSTGRES_PASSWORD` - PostgreSQL password
- `POSTGRES_DB` - Database name

---

## Cost Estimates

### Local Development
- **Cost**: $0 (runs on your machine)
- **Resources**: ~4GB RAM, 10GB disk

### Azure Container Apps (Dev/Test)
- **Frontend**: ~$0-5/month (scales to zero)
- **Backend**: ~$0-10/month (scales to zero)
- **Database**: ~$15-30/month (1 replica always on)
- **Total**: ~$15-45/month

### Azure Container Apps (Production)
- **Frontend**: ~$5-20/month (autoscaling)
- **Backend**: ~$10-50/month (autoscaling)
- **Database**: ~$20-100/month (based on size/performance)
- **Total**: ~$35-170/month

*Note: Actual costs vary based on traffic, compute duration, and storage.*

---

## Next Steps

1. ✅ Test locally with `docker-compose up -d`
2. ✅ Verify frontend at http://localhost:3000
3. ✅ Verify backend at http://localhost:8000/docs
4. ✅ Run tests with `docker-compose exec backend pytest`
5. ⬜ Set up Azure Container Registry
6. ⬜ Build and push production images
7. ⬜ Deploy to Azure Container Apps
8. ⬜ Configure custom domain (optional)
9. ⬜ Set up CI/CD pipeline (optional)
10. ⬜ Enable monitoring with Application Insights (optional)

---

## Additional Resources

- [Docker Compose Documentation](https://docs.docker.com/compose/)
- [Azure Container Apps Documentation](https://learn.microsoft.com/azure/container-apps/)
- [Next.js Deployment](https://nextjs.org/docs/deployment)
- [FastAPI Deployment](https://fastapi.tiangolo.com/deployment/)

For detailed implementation plan, see: [`.claude/plans/steady-swinging-kahan.md`](.claude/plans/steady-swinging-kahan.md)
