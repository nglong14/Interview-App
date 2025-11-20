
from .. import models, schemas, oauth2, utils
from fastapi import APIRouter, HTTPException, Depends, status
from ..database import get_db
from sqlalchemy.orm import Session
import string, random, datetime

router = APIRouter(
    prefix="/urls",
    tags=['URLs']
)

def generate_short_code(length=6):
    chars = string.ascii_letters + string.digits
    return ''.join(random.choices(chars, k=length))

# Create a short URL
@router.post("/", response_model=schemas.URLResponse, status_code=status.HTTP_201_CREATED)
def create_short_url(url: schemas.URLCreate, db: Session = Depends(get_db), current_user: models.User = Depends(oauth2.get_current_user)):
    if current_user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Could not validate credentials")
    short_code = generate_short_code()
    # Ensure uniqueness
    while db.query(models.URL).filter(models.URL.short_code == short_code).first():
        short_code = generate_short_code()
    db_url = models.URL(
        original_url=url.original_url,
        short_code=short_code,
        user_id=current_user.id,
        created_at=datetime.datetime.utcnow()
    )
    db.add(db_url)
    db.commit()
    db.refresh(db_url)
    return db_url

# Get all URLs for the current user
@router.get("/", response_model=list[schemas.URLResponse])
def get_urls(db: Session = Depends(get_db), current_user: models.User = Depends(oauth2.get_current_user)):
    if current_user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Could not validate credentials")
    urls = db.query(models.URL).filter(models.URL.user_id == current_user.id).all()
    return urls

# Redirect short URL (public, no auth)
@router.get("/r/{short_code}")
def redirect_short_url(short_code: str, db: Session = Depends(get_db)):
    url = db.query(models.URL).filter(models.URL.short_code == short_code).first()
    if not url:
        raise HTTPException(status_code=404, detail="Short URL not found")
    return {"original_url": url.original_url}