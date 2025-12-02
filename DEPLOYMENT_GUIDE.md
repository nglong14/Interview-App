# Complete Deployment Guide - URL Shortener to Google Cloud

This guide ensures successful deployment of your URL shortener to Google Cloud Platform.

---

## Prerequisites Checklist

Before starting, ensure you have:

- [ ] Google Cloud account with billing enabled
- [ ] Google Cloud CLI installed ([Download](https://cloud.google.com/sdk/docs/install))
- [ ] Docker installed (optional, for local testing)
- [ ] Git installed
- [ ] Your project code ready

---

## Step 1: Initial Google Cloud Setup

### 1.1 Login and Configure

```bash
# Login to Google Cloud
gcloud auth login

# Set your project ID (replace with your actual project ID)
gcloud config set project fasturl-479715

# Enable required APIs
gcloud services enable run.googleapis.com
gcloud services enable sqladmin.googleapis.com
gcloud services enable redis.googleapis.com
gcloud services enable cloudbuild.googleapis.com
gcloud services enable artifactregistry.googleapis.com
```

### 1.2 Set Environment Variables

```bash
# Set these for easier commands (Windows PowerShell)
$PROJECT_ID = "fasturl-479715"
$REGION = "us-central1"
$SQL_INSTANCE = "my-postgres-instance"
$REDIS_INSTANCE = "url-shortener-redis"
$SERVICE_NAME = "fastapi-app"

# Verify
echo $PROJECT_ID
```

---

## Step 2: Create Cloud SQL (PostgreSQL)

### 2.1 Create SQL Instance

```bash
# Create PostgreSQL instance (takes 5-10 minutes)
gcloud sql instances create my-postgres-instance \
  --database-version=POSTGRES_15 \
  --tier=db-f1-micro \
  --region=us-central1 \
  --root-password=YOUR_STRONG_PASSWORD_HERE \
  --database-flags=max_connections=100

# Wait for creation
gcloud sql instances list
```

**Expected output:**
```
NAME                   DATABASE_VERSION  LOCATION       TIER         STATUS
my-postgres-instance   POSTGRES_15       us-central1-a  db-f1-micro  RUNNABLE
```

### 2.2 Create Database and User

```bash
# Create database
gcloud sql databases create myapp_db --instance=my-postgres-instance

# Create application user
gcloud sql users create myapp_user \
  --instance=my-postgres-instance \
  --password=YOUR_APP_PASSWORD_HERE

# Verify
gcloud sql databases list --instance=my-postgres-instance
gcloud sql users list --instance=my-postgres-instance
```

### 2.3 Get Connection Name

```bash
# Save this - you'll need it!
gcloud sql instances describe my-postgres-instance --format="value(connectionName)"
```

**Example output:** `fasturl-479715:us-central1:my-postgres-instance`

---

## Step 3: Create Memorystore (Redis)

### 3.1 Create Redis Instance

```bash
# Create Redis instance (takes 5-10 minutes)
gcloud redis instances create url-shortener-redis \
  --size=1 \
  --region=us-central1 \
  --redis-version=redis_7_0 \
  --tier=basic

# Wait for creation
gcloud redis instances list --region=us-central1
```

**Expected output:**
```
NAME                   VERSION    REGION        TIER   SIZE_GB  HOST          STATUS
url-shortener-redis    REDIS_7_0  us-central1   BASIC  1        10.81.160.3   READY
```

### 3.2 Get Redis Host

```bash
# Save this IP address - you'll need it!
gcloud redis instances describe url-shortener-redis \
  --region=us-central1 \
  --format="value(host)"
```

**Example output:** `10.81.160.195`

---

## Step 4: Configure Your Project

### 4.1 Update env.yaml

Create or update `env.yaml` in your project root:

```yaml
ENVIRONMENT: "production"
DATABASE_HOSTNAME: "localhost"
DATABASE_PORT: "5432"
DATABASE_NAME: "myapp_db"
DATABASE_USERNAME: "myapp_user"
DATABASE_PASSWORD: "YOUR_APP_PASSWORD_HERE"
SECRET_KEY: "YOUR_SECRET_KEY_HERE"
ALGORITHM: "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES: "45"
REDIS_HOST: "YOUR_REDIS_IP_HERE"
REDIS_PORT: "6379"
REDIS_PASSWORD: ""
CLOUD_SQL_CONNECTION_NAME: "YOUR_PROJECT_ID:us-central1:my-postgres-instance"
```

**Replace:**
- `YOUR_APP_PASSWORD_HERE` → Password you set for `myapp_user`
- `YOUR_SECRET_KEY_HERE` → Generate with: `openssl rand -hex 32`
- `YOUR_REDIS_IP_HERE` → IP from Step 3.2
- `YOUR_PROJECT_ID` → Your Google Cloud project ID

### 4.2 Verify backend/config.py

Ensure your `backend/config.py` has this code:

```python
from pydantic_settings import BaseSettings
from pydantic import ConfigDict


class Settings(BaseSettings):
    database_hostname: str
    database_port: str
    database_password: str
    database_name: str
    database_username: str
    secret_key: str
    algorithm: str
    access_token_expire_minutes: int

    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_password: str = ""
    
    environment: str = "development"
    cloud_sql_connection_name: str = ""

    model_config = ConfigDict(
        env_file=".env",
        case_sensitive=False
    )

    @property
    def is_production(self) -> bool:
        return self.environment == "production"
    
    @property
    def database_url(self) -> str:
        """Get database URL based on environment"""
        if self.is_production and self.cloud_sql_connection_name:
            # Use Unix socket for Cloud SQL
            return f"postgresql://{self.database_username}:{self.database_password}@/{self.database_name}?host=/cloudsql/{self.cloud_sql_connection_name}"
        elif self.database_hostname.startswith("/cloudsql/"):
            # Direct Unix socket path provided
            return f"postgresql://{self.database_username}:{self.database_password}@/{self.database_name}?host={self.database_hostname}"
        else:
            # Use TCP for local/development
            return f"postgresql://{self.database_username}:{self.database_password}@{self.database_hostname}:{self.database_port}/{self.database_name}"


settings = Settings()
```

### 4.3 Verify Dockerfile

Ensure your `Dockerfile` exists and is correct:

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Set port
ENV PORT=8080
EXPOSE 8080

# Run application
CMD uvicorn backend.main:app --host 0.0.0.0 --port ${PORT}
```

### 4.4 Verify requirements.txt

Ensure all dependencies are listed:

```txt
fastapi
uvicorn[standard]
sqlalchemy
psycopg2-binary
redis
pydantic
pydantic-settings
python-dotenv
PyJWT
passlib[bcrypt]
slowapi
python-multipart
```

---

## Step 5: Deploy to Cloud Run

### 5.1 Build and Push Image

```bash
# Build Docker image using Cloud Build
gcloud builds submit --tag us-central1-docker.pkg.dev/fasturl-479715/my-app-repo/fastapi-app
```

**If you get "repository does not exist" error:**

```bash
# Create Artifact Registry repository first
gcloud artifacts repositories create my-app-repo \
  --repository-format=docker \
  --location=us-central1 \
  --description="Docker repository for URL shortener"

# Then retry the build
gcloud builds submit --tag us-central1-docker.pkg.dev/fasturl-479715/my-app-repo/fastapi-app
```

### 5.2 Deploy to Cloud Run

```bash
gcloud run deploy fastapi-app \
  --image us-central1-docker.pkg.dev/fasturl-479715/my-app-repo/fastapi-app \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --add-cloudsql-instances fasturl-479715:us-central1:my-postgres-instance \
  --env-vars-file env.yaml \
  --port 8080 \
  --memory 512Mi \
  --cpu 1 \
  --max-instances 10 \
  --min-instances 0 \
  --timeout 300
```

**Expected output:**
```
Deploying container to Cloud Run service [fastapi-app] in project [fasturl-479715] region [us-central1]
✓ Deploying... Done.
  ✓ Creating Revision...
  ✓ Routing traffic...
Done.
Service [fastapi-app] revision [fastapi-app-00001-xxx] has been deployed and is serving 100 percent of traffic.
Service URL: https://fastapi-app-xxxxx-uc.a.run.app
```

### 5.3 Get Your API URL

```bash
# Get the service URL
gcloud run services describe fastapi-app \
  --region us-central1 \
  --format="value(status.url)"
```

**Save this URL!** This is your live API endpoint.

---

## Step 6: Initialize Database Tables

Your app should auto-create tables on startup, but verify:

### 6.1 Check Logs

```bash
# View startup logs
gcloud run services logs tail fastapi-app --region us-central1
```

Look for successful startup messages.

### 6.2 Manual Table Creation (if needed)

```bash
# Connect to Cloud SQL
gcloud sql connect my-postgres-instance --user=myapp_user --database=myapp_db

# In psql, check tables
\dt

# If tables don't exist, they'll be created on first API request
```

---

## Step 7: Test Your Deployment

### 7.1 Set Environment Variable

```bash
# Save your service URL (replace with actual URL)
$API_URL = "https://fastapi-app-xxxxx-uc.a.run.app"
```

### 7.2 Test Health Check

```bash
curl $API_URL/health
```

**Expected response:**
```json
{"status":"healthy"}
```

### 7.3 Test User Registration

```bash
curl -X POST "$API_URL/register" `
  -H "Content-Type: application/json" `
  -d '{"email":"test@example.com","password":"password123"}'
```

**Expected response:**
```json
{
  "id": 1,
  "email": "test@example.com",
  "created_at": "2025-11-29T..."
}
```

### 7.4 Test Login

```bash
curl -X POST "$API_URL/login" `
  -H "Content-Type: application/x-www-form-urlencoded" `
  -d "username=test@example.com&password=password123"
```

**Expected response:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

**Save the access_token for next step!**

### 7.5 Test URL Creation

```bash
# Replace YOUR_TOKEN with the token from login
curl -X POST "$API_URL/urls/" `
  -H "Authorization: Bearer YOUR_TOKEN" `
  -H "Content-Type: application/json" `
  -d '{"original_url":"https://www.google.com"}'
```

**Expected response:**
```json
{
  "id": 1,
  "short_code": "abc123",
  "original_url": "https://www.google.com",
  "clicks": 0,
  "created_at": "2025-11-29T...",
  "user_id": 1
}
```

### 7.6 Test Redirect

```bash
# Replace abc123 with your actual short_code
curl "$API_URL/urls/r/abc123"
```

**Expected response:**
```json
{
  "original_url": "https://www.google.com"
}
```

---

## Step 8: Verify Everything Works

### 8.1 Check Cloud Run Status

```bash
gcloud run services describe fastapi-app --region us-central1
```

Look for:
- `Traffic: 100% -> latest revision`
- `URL: https://...`

### 8.2 Check Cloud SQL Status

```bash
gcloud sql instances list
```

Should show `RUNNABLE`.

### 8.3 Check Redis Status

```bash
gcloud redis instances list --region us-central1
```

Should show `READY`.

### 8.4 Monitor Logs

```bash
# Real-time logs
gcloud run services logs tail fastapi-app --region us-central1

# Recent logs
gcloud run services logs read fastapi-app --region us-central1 --limit 50
```

---

## Common Issues and Solutions

### Issue 1: "Database does not exist"

**Solution:**
```bash
# Create the database
gcloud sql databases create myapp_db --instance=my-postgres-instance

# Verify
gcloud sql databases list --instance=my-postgres-instance
```

### Issue 2: "Connection refused" to PostgreSQL

**Causes:**
- Wrong `CLOUD_SQL_CONNECTION_NAME` in env.yaml
- Missing `--add-cloudsql-instances` flag in deploy command

**Solution:**
```bash
# Verify connection name matches
gcloud sql instances describe my-postgres-instance --format="value(connectionName)"

# Redeploy with correct flag
gcloud run deploy fastapi-app \
  --image us-central1-docker.pkg.dev/fasturl-479715/my-app-repo/fastapi-app \
  --add-cloudsql-instances fasturl-479715:us-central1:my-postgres-instance \
  --env-vars-file env.yaml
```

### Issue 3: Redis Connection Timeout

**Causes:**
- Wrong Redis IP in env.yaml
- Redis instance not ready

**Solution:**
```bash
# Get correct Redis IP
gcloud redis instances describe url-shortener-redis \
  --region=us-central1 \
  --format="value(host)"

# Update env.yaml with correct IP
# Redeploy
```

### Issue 4: Build Fails

**Solution:**
```bash
# Check Docker syntax
docker build -t test-local .

# If local build works, check Cloud Build logs
gcloud builds list --limit 5

# View specific build log
gcloud builds log BUILD_ID
```

### Issue 5: 502 Bad Gateway

**Causes:**
- App crashes on startup
- Port mismatch

**Solution:**
```bash
# Check logs for errors
gcloud run services logs tail fastapi-app --region us-central1

# Verify Dockerfile exposes port 8080
# Verify deploy command uses --port 8080
```

---

## Redeployment Process

### When You Change Code:

```bash
# 1. Rebuild image
gcloud builds submit --tag us-central1-docker.pkg.dev/fasturl-479715/my-app-repo/fastapi-app

# 2. Deploy new version
gcloud run deploy fastapi-app \
  --image us-central1-docker.pkg.dev/fasturl-479715/my-app-repo/fastapi-app \
  --region us-central1

# Cloud Run will:
# - Create new revision
# - Test it with 1 request
# - Switch 100% traffic if successful
# - Keep old revision as backup
```

### Quick Redeploy (from source):

```bash
# One command to rebuild and deploy
gcloud run deploy fastapi-app \
  --source . \
  --region us-central1 \
  --allow-unauthenticated \
  --add-cloudsql-instances fasturl-479715:us-central1:my-postgres-instance \
  --env-vars-file env.yaml \
  --port 8080 \
  --memory 512Mi \
  --cpu 1
```

---

## Stopping/Pausing Deployment

### Temporary Pause (Scale to Zero):

```bash
gcloud run services update fastapi-app \
  --region us-central1 \
  --max-instances 0
```

**Resume:**
```bash
gcloud run services update fastapi-app \
  --region us-central1 \
  --max-instances 10
```

### Complete Shutdown:

```bash
# Delete Cloud Run service
gcloud run services delete fastapi-app --region us-central1

# Pause Cloud SQL (saves money)
gcloud sql instances patch my-postgres-instance --activation-policy NEVER

# Delete Redis (or keep for $15/month)
gcloud redis instances delete url-shortener-redis --region us-central1
```

**To restart:**
```bash
# Reactivate Cloud SQL
gcloud sql instances patch my-postgres-instance --activation-policy ALWAYS

# Recreate Redis if deleted
gcloud redis instances create url-shortener-redis \
  --size=1 \
  --region=us-central1 \
  --redis-version=redis_7_0

# Redeploy app (use deployment commands from Step 5)
```

---

## Monitoring and Maintenance

### View Metrics:

```bash
# Go to Cloud Console
https://console.cloud.google.com/run/detail/us-central1/fastapi-app/metrics
```

### Set Up Billing Alerts:

```bash
gcloud billing budgets create \
  --display-name="URL Shortener Budget" \
  --budget-amount=30USD \
  --threshold-rule=percent=50 \
  --threshold-rule=percent=90 \
  --threshold-rule=percent=100
```

### Check Costs:

```bash
# View billing
https://console.cloud.google.com/billing
```

---

## Final Checklist

Before considering deployment complete:

- [ ] Service URL is accessible
- [ ] Health check returns `{"status":"healthy"}`
- [ ] Can register new user
- [ ] Can login and get token
- [ ] Can create short URL with authentication
- [ ] Can redirect using short code
- [ ] Logs show no errors
- [ ] Cloud SQL is connected (check logs)
- [ ] Redis is connected (check logs)
- [ ] Billing alerts are set up
- [ ] Documentation is saved

---

## Quick Reference Commands

```bash
# Get service URL
gcloud run services describe fastapi-app --region us-central1 --format="value(status.url)"

# View logs
gcloud run services logs tail fastapi-app --region us-central1

# Redeploy
gcloud run deploy fastapi-app --source . --region us-central1

# Check status
gcloud run services list
gcloud sql instances list
gcloud redis instances list --region us-central1

# Stop everything
gcloud run services delete fastapi-app --region us-central1
gcloud sql instances patch my-postgres-instance --activation-policy NEVER
gcloud redis instances delete url-shortener-redis --region us-central1
```

---

## Support

**If deployment fails:**

1. Check logs: `gcloud run services logs tail fastapi-app --region us-central1`
2. Verify all services are running: `gcloud sql instances list`
3. Check env.yaml has correct values
4. Ensure Cloud SQL connection name matches
5. Verify Redis IP is correct
6. Test locally with Docker first

**Estimated deployment time:** 30-45 minutes (first time)

**Estimated cost:** $20-30/month with light usage

---

**Deployment Complete!** 🚀

Your URL shortener is now live at: `https://fastapi-app-xxxxx-uc.a.run.app`
