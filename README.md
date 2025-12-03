# FastURL

A fast and scalable URL shortening service built with FastAPI, PostgreSQL, and Redis.

## Features

- Shorten long URLs into short, shareable links
- Caching for low latency
- User authentication with JWT tokens
- Rate limiting to prevent abuse
- RESTful API design
- Cloud-ready deployment

## Tech Stack

- **Backend:** FastAPI (Python 3.11)
- **Database:** PostgreSQL
- **Cache:** Redis
- **Authentication:** JWT
- **ORM:** SQLAlchemy
- **Deployment:** Google Cloud Run

## Quick Start

### Prerequisites

- Python 3.11+
- Docker & Docker Compose
- PostgreSQL
- Redis

### Installation

```bash
git clone https://github.com/nglong14/Interview-App.git
cd URL-Shortener

python -m venv .venv
.venv\Scripts\activate

pip install -r requirements.txt
```

### Environment Setup

Create `.env` file:

```env
DATABASE_HOSTNAME=localhost
DATABASE_PORT=5432
DATABASE_PASSWORD=yourpassword
DATABASE_NAME=url_shortener
DATABASE_USERNAME=postgres
SECRET_KEY=your-secret-key
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REDIS_HOST=localhost
REDIS_PORT=6379
ENVIRONMENT=development
```

### Run Application

```bash
docker-compose up -d

uvicorn backend.main:app --reload
```

Access at `http://localhost:8000`

Documentation at `http://localhost:8000/docs`

## API Endpoints

### Authentication

```bash
POST /register
POST /login
```

### URLs

```bash
POST   /urls/              # Create short URL
GET    /urls/              # Get user's URLs
GET    /urls/r/{code}      # Redirect to original URL
DELETE /urls/{id}          # Delete URL
```

### Health

```bash
GET /health
```

## Project Structure

```
URL-Shortener/
├── backend/
│   ├── routers/
│   │   ├── auth.py
│   │   ├── users.py
│   │   └── url.py
│   ├── models.py
│   ├── database.py
│   ├── config.py
│   ├── oauth2.py
│   ├── utils.py
│   └── main.py
├── test/
│   ├── conftest.py
│   └── test_url.py
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
├── DEPLOYMENT_GUIDE.md
└── README.md
```

## Deployment

See [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md) for complete deployment instructions to Google Cloud Platform.

