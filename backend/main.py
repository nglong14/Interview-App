from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .routers import auth, url, users
from . import models
from .database import engine, SessionLocal

models.Base.metadata.create_all(bind=engine)
app = FastAPI()

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