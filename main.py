from fastapi import FastAPI, HTTPException, Query, Depends, Request
from fastapi.responses import HTMLResponse, FileResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
import os, string, random
import models, database, utils

app = FastAPI()

# Initialize Database
models.Base.metadata.create_all(bind=database.engine)

# Configuration
APP_URL_ENV = os.getenv("APP_URL", "").rstrip("/")

def get_db():
    db = database.SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.get("/", response_class=HTMLResponse)
async def read_index():
    print("DEBUG: Serving index.html")
    return FileResponse("index.html")
@app.post("/shorten")
async def shorten_url(request: Request, url: str, alias: str = Query(None), db: Session = Depends(get_db)):
    # Handle empty alias strings from frontend
    alias = alias.strip() if alias and alias.strip() != "" else None
    
    if not utils.check_url_safety(url):
        raise HTTPException(status_code=400, detail="URL contains suspicious content")
    
    # CRITICAL: Ensure the URL has a protocol to prevent 404 relative redirects
    if not url.startswith(("http://", "https://")):
        url = "https://" + url

    short_id = alias if alias else ''.join(random.choices(string.ascii_letters + string.digits, k=6))

    # Check if this short_id already exists in the database
    existing = db.query(models.Link).filter(
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

    # Dynamically determine the base URL from the request if APP_URL is not set
    base = APP_URL_ENV if APP_URL_ENV else f"{request.url.scheme}://{request.url.netloc}"
    final_short_url = f"{base}/r/{short_id}"

    print(f"DEBUG: Created short link {short_id} -> {url} (Base: {base})")
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
    # Strip any potential whitespace or trailing slashes from the ID
    clean_id = short_id.strip()
    print(f"DEBUG: Incoming redirect request for ID: '{clean_id}'")
    link = db.query(models.Link).filter(models.Link.short_code == clean_id).first()
    if link:
        # Record click analytics
        new_click = models.Click(
            link_id=link.id,
            ip_address=request.client.host,
            user_agent=request.headers.get("user-agent")
        )
        db.add(new_click)
        db.commit()
        print(f"DEBUG: ID found! Redirecting to {link.original_url}")
        return RedirectResponse(url=link.original_url, status_code=302)
    print(f"DEBUG: ID '{clean_id}' NOT FOUND in database")
    raise HTTPException(status_code=404, detail="Link not found")
