from fastapi import FastAPI, HTTPException, Query, Depends, Request
from fastapi.responses import HTMLResponse, FileResponse, RedirectResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
import os, string, random, logging
import models, database, utils

# Setup logging for Render console
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

# Initialize Database Tables
try:
    logger.info(f"Attempting to connect to database: {database.SQLALCHEMY_DATABASE_URL.split('?')[0]}")
    models.Base.metadata.create_all(bind=database.engine)
    logger.info("Database tables initialized successfully.")
except Exception as e: # Catching a broader exception for initial debugging
    logger.error(f"Database initialization failed: {e}")

# Configuration
APP_URL_ENV = (os.getenv("APP_URL") or "").rstrip("/")

def get_db():
    db = database.SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.get("/", response_class=HTMLResponse)
async def read_index():
    logger.info("Serving index.html")
    return FileResponse("index.html")
@app.post("/shorten")
async def shorten_url(request: Request, url: str, alias: str = Query(None), db: Session = Depends(get_db)):
    # Clean input
    url = url.strip()
    alias = alias.strip() if alias and alias.strip() else None

    if not utils.check_url_safety(url):
        raise HTTPException(status_code=400, detail="URL contains suspicious content")
    
    # CRITICAL: If the URL doesn't have http/https, the browser will treat the 
    # redirect as a relative path on YOUR domain, causing a 404.
    if not url.startswith(("http://", "https://")):
        url = "https://" + url

    short_id = alias if alias else ''.join(random.choices(string.ascii_lowercase + string.digits, k=6))

    # Check if this short_id already exists in the database
    existing = db.query(models.Link).filter( # Case-insensitive check for alias
        (models.Link.short_code == short_id) | 
        (models.Link.custom_alias == short_id)
    ).first()
    if existing:
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
    db.commit()

    # Determine the base URL dynamically or from Env
    if APP_URL_ENV:
        base = APP_URL_ENV
    else:
        base = str(request.base_url).rstrip("/") # Use request.base_url for more accuracy

    final_short_url = f"{base}/r/{short_id}"

    logger.info(f"Generated short URL: {final_short_url} for original: {url}")
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
    clean_id = short_id.strip().lower() # Ensure case-insensitivity for lookup
    logger.info(f"Attempting to redirect for short_id: '{clean_id}'")
    
    # Query for both short_code and custom_alias
    link = db.query(models.Link).filter((models.Link.short_code == clean_id) | (models.Link.custom_alias == clean_id)).first()
    
    if link:
        logger.info(f"Redirecting ID '{clean_id}' to: {link.original_url}")
        new_click = models.Click(
            link_id=link.id,
            ip_address=request.client.host,
            user_agent=request.headers.get("user-agent")
        )
        db.add(new_click)
        db.commit()
        return RedirectResponse(url=link.original_url, status_code=307) # Using 307 for temporary redirect
    
    logger.warning(f"Short ID '{clean_id}' not found in database. Current links in DB: {db.query(models.Link).count()}")
    raise HTTPException(status_code=404, detail="Link not found")
