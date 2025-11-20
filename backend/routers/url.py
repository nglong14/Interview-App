
from .. import models, schemas, oauth2, utils, cache
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
    
    # Invalidate user's URLs cache
    cache.invalidate_user_urls_cache(current_user.id)
    
    return db_url

# Get all URLs for the current user
@router.get("/", response_model=list[schemas.URLResponse])
def get_urls(db: Session = Depends(get_db), current_user: models.User = Depends(oauth2.get_current_user)):
    if current_user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Could not validate credentials")
    
    # Try to get from cache first
    cache_key = f"user_urls:{current_user.id}"
    cached_urls = cache.get_cache(cache_key)
    if cached_urls:
        return cached_urls
    
    # If not in cache, get from database
    urls = db.query(models.URL).filter(models.URL.user_id == current_user.id).order_by(models.URL.created_at.desc()).all()
    
    # Cache the result for 1 hour (3600 seconds)
    urls_data = [{"id": url.id, "original_url": url.original_url, "short_code": url.short_code, "created_at": url.created_at.isoformat()} for url in urls]
    cache.set_cache(cache_key, urls_data, ttl=3600)
    
    return urls

# Redirect short URL (public, no auth)
@router.get("/r/{short_code}")
def redirect_short_url(short_code: str, db: Session = Depends(get_db)):
    # Try cache first
    cache_key = f"short_url:{short_code}"
    cached_url = cache.get_cache(cache_key)
    if cached_url:
        return cached_url
    
    # Get from database
    url = db.query(models.URL).filter(models.URL.short_code == short_code).first()
    if not url:
        raise HTTPException(status_code=404, detail="Short URL not found")
    
    result = {"original_url": url.original_url}
    
    # Cache for 24 hours (URLs don't change often)
    cache.set_cache(cache_key, result, ttl=86400)
    
    return result