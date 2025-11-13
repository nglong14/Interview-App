from fastapi import FastAPI
from .routers import auth, users
from . import models
from .database import engine, SessionLocal

models.Base.metadata.create_all(bind=engine)
app = FastAPI()

# app.include_router(auth.router)   
app.include_router(users.router)