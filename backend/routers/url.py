
from .. import models, schemas, oauth2, utils, cache
from fastapi import APIRouter, HTTPException, Depends, status, BackgroundTasks, Request
from ..database import get_db
from slowapi import Limiter
from slowapi.util import get_remote_address
from sqlalchemy.orm import Session
import string, random, datetime
import asyncio

router = APIRouter(
    prefix="/urls",
    tags=['URLs']
)

limiter = Limiter(key_func=get_remote_address)

def generate_short_code(length=6):
    chars = string.ascii_letters + string.digits
    return ''.join(random.choices(chars, k=length))

# Create a short URL
@router.post("/", response_model=schemas.URLResponse, status_code=status.HTTP_201_CREATED
async def create_short_url(url: schemas.URLCreate, db: Session = Depends(get_db), current_user: models.User = Depends(oauth2.get_current_user)):
@limiter.limit("1500/minute")
def create_short_url(request: Request, url: schemas.URLCreate, db: Session = Depends(get_db), current_user: models.User = Depends(oauth2.get_current_user
    if current_user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Could not validate credentials")
    short_code = generate_short_code()

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
    await asyncio.to_thread(cache.invalidate_user_urls_cache, current_user.id)
    
    return db_url

# Get all URLs for the current user
@router.get("/", response_model=list[schemas.URLResponse])
async def get_urls(db: Session = Depends(get_db), current_user: models.User = Depends(oauth2.get_current_user)):
    if current_user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Could not validate credentials")
    
    cache_key = f"user_urls:{current_user.id}"
    cached_urls = await asyncio.to_thread(cache.get_cache, cache_key)
    if cached_urls:
        return cached_urls
    
    # If not in cache, get from database
    urls = db.query(models.URL).filter(models.URL.user_id == current_user.id).order_by(models.URL.created_at.desc()).all()
    
    urls_data = [{"id": url.id, "original_url": url.original_url, "short_code": url.short_code, "created_at": url.created_at.isoformat(), "clicks": url.clicks} for url in urls]
    await asyncio.to_thread(cache.set_cache, cache_key, urls_data, ttl=3600)
    
    return urls

async def update_click_count(short_code: str, db: Session):
    """Background task to update click count in database"""
    url = db.query(models.URL).filter(models.URL.short_code == short_code).first()
    if url:
        # Get current count from Redis
        redis_clicks = await asyncio.to_thread(cache.get_clicks, short_code)
        # Update database with Redis count
        url.clicks = redis_clicks
        db.commit()

# Redirect short URL
@router.get("/r/{short_code}")
async def redirect_short_url(short_code: str, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    # Try cache first
    cache_key = f"short_url:{short_code}"
    cached_url = await asyncio.to_thread(cache.get_cache, cache_key)
    
    if cached_url:
        # Increment click count in Redis (instant)
        await asyncio.to_thread(cache.increment_clicks, short_code)
        # Schedule background task to sync to database
        background_tasks.add_task(update_click_count, short_code, db)
        return cached_url
    
    # Get from database
    url = db.query(models.URL).filter(models.URL.short_code == short_code).first()
    if not url:
        raise HTTPException(status_code=404, detail="Short URL not found")
    
    result = {"original_url": url.original_url}
    
    # Increment click count in Redis
    await asyncio.to_thread(cache.increment_clicks, short_code)
    
    # Cache for 24 hours (URLs don't change often)
    await asyncio.to_thread(cache.set_cache, cache_key, result, ttl=86400)
    
    background_tasks.add_task(update_click_count, short_code, db)
    
    return result