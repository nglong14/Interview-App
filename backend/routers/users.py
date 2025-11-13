from .. import models, schemas, utils
from fastapi import FastAPI, Response, HTTPException, Depends, APIRouter, status
from ..database import get_db, SessionLocal
from sqlalchemy.orm import Session

router = APIRouter(
    prefix="/users",
    tags=['Users']
)

#Create users
@router.post("/", status_code=status.HTTP_201_CREATED, response_model=schemas.UserOut)
def create_user(user:schemas.UserCreate, db: Session = Depends(get_db)):
    hashed_password = utils.get_password_hash(user.password)
    user.password = hashed_password
    new_user = models.User(**user.dict())
    db.add(new_user)
    db.commit()
    db.refresh(new_user) 
    return new_user

#Get user by id
@router.post("/", response_model=schemas.UserOut)
def create_user(id: int, db: Session = Depends(get_db)):
    pass