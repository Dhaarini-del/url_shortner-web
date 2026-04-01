from fastapi import FastAPI, HTTPException, Query, Depends, Request
from fastapi.responses import HTMLResponse, FileResponse, RedirectResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
import os, string, random, logging
import models, database, utils

# Setup logging for Render console
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

# Enable CORS for frontend communication
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://astounding-lollipop-f34198.netlify.app",
        "http://localhost:3000",
        "http://127.0.0.1:5500"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize Database Tables
try:
    logger.info(f"Attempting to connect to database: {database.SQLALCHEMY_DATABASE_URL.split('?')[0].split('@')[-1]}") # Log without credentials
    models.Base.metadata.create_all(bind=database.engine)
    logger.info("Database tables initialized successfully.")
except Exception as e:
    # This is a critical error. The app cannot function without database access.
    logger.error(f"Database initialization failed: {e}")

# Configuration
APP_URL_ENV = (os.getenv("APP_URL") or "").rstrip("/")

def get_db():
    db = database.SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.get("/")
async def health_check():
    """Backend Health Check - Now that frontend is on Netlify"""
    return {
        "status": "online",
        "api": "Link Master API",
        "version": "1.0.0"
    }

@app.post("/shorten")
async def shorten_url(request: Request, url: str, alias: str = Query(None), db: Session = Depends(get_db)):
    # Clean input
    url = url.strip()
    alias = alias.strip() if alias and alias.strip() else None

    if not utils.check_url_safety(url):
        logger.warning(f"Attempt to shorten unsafe URL: {url}")
        raise HTTPException(status_code=400, detail="URL contains suspicious content")
    
    # CRITICAL: If the URL doesn't have http/https, the browser will treat the 
    # redirect as a relative path on YOUR domain, causing a 404.
    if not url.startswith(("http://", "https://")):
        url = "https://" + url

    short_id = alias if alias else ''.join(random.choices(string.ascii_lowercase + string.digits, k=6))

    # Check if this short_id already exists in the database. Use .ilike for case-insensitivity on PostgreSQL
    existing = db.query(models.Link).filter(
        (models.Link.short_code == short_id) | 
        (models.Link.custom_alias == short_id) # custom_alias should be exact match
    ).first()
    if existing:
        logger.warning(f"Alias/short code '{short_id}' already taken for URL: {url}")
        raise HTTPException(status_code=400, detail="Short code or alias already taken")

    domain, ip = utils.get_url_metadata(url)
    
    new_link = models.Link(
        original_url=url,
        short_code=short_id,
        custom_alias=alias,
        domain_name=domain or "Unknown",
        website_ip=ip
    )
    db.add(new_link)
    try:
        db.commit()
        logger.info(f"Successfully committed new link to DB: {short_id} -> {url}")
    except Exception as commit_error:
        db.rollback()
        logger.error(f"Database commit failed for {short_id}: {commit_error}")
        raise HTTPException(status_code=500, detail="Failed to save link to database.")

    # Determine the base URL dynamically or from Env
    if APP_URL_ENV:
        base = APP_URL_ENV
    else:
        base = str(request.base_url).rstrip("/") # Fallback to current request's base URL
        logger.warning(f"APP_URL environment variable not set. Using request.base_url for link generation: {base}")

    final_short_url = f"{base}/r/{short_id}"

    logger.info(f"Generated short URL: {final_short_url} (for {url})")
    qr_code = utils.generate_qr_base64(final_short_url)

    return {
        "short_url": final_short_url,
        "domain": domain,
        "ip": ip,
        "qr_code": qr_code
    }

@app.get("/r/{short_id}")
@app.get("/r/{short_id}/")
async def redirect_url(short_id: str, request: Request, db: Session = Depends(get_db)):
    # Clean ID to prevent lookup failures
    clean_id = short_id.strip()
    logger.info(f"Attempting to redirect for short_id: '{clean_id}'")
    
    # Query for both short_code and custom_alias
    link = db.query(models.Link).filter(
        (models.Link.short_code == clean_id) |
        (models.Link.custom_alias == clean_id)
    ).first()
    
    if link:
        logger.info(f"Redirecting ID '{clean_id}' to: {link.original_url}")
        new_click = models.Click(
            link_id=link.id,
            ip_address=request.client.host,
            user_agent=request.headers.get("user-agent"),
            country="Unknown" # Default for now
        )
        db.add(new_click)
        db.commit()
        return RedirectResponse(url=link.original_url, status_code=302)
    
    logger.warning(f"Short ID '{clean_id}' not found in database. Links in DB: {db.query(models.Link).count()}. Check DB connection and APP_URL.")
    raise HTTPException(status_code=404, detail="Link not found")
