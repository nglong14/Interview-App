from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .routers import auth, url, users
from . import models
from .database import engine, SessionLocal
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

models.Base.metadata.create_all(bind=engine)
limiter = Limiter(key_func=get_remote_address)
app = FastAPI()
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Enable CORS to allow requests from Postman and other clients
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins (change in production)
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)   
app.include_router(users.router)
app.include_router(url.router)  # URL shortener endpoints

@app.get("/health")
async def health():
    return {"status": "healthy"}