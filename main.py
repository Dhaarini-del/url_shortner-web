from fastapi import FastAPI, HTTPException, Query, Depends, Request
from fastapi.responses import HTMLResponse, FileResponse, RedirectResponse, JSONResponse
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
    # Clean input
    url = url.strip()
    alias = alias.strip() if alias and alias.strip() else None

    if not utils.check_url_safety(url):
        raise HTTPException(status_code=400, detail="URL contains suspicious content")
    
    # CRITICAL: If the URL doesn't have http/https, the browser will treat the 
    # redirect as a relative path on YOUR domain, causing a 404.
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

    # Dynamically determine the base URL. This handles the case where APP_URL env is wrong.
    if APP_URL_ENV:
        base = APP_URL_ENV
    else:
        base = str(request.base_url).rstrip("/")

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
    clean_id = short_id.strip()
    
    link = db.query(models.Link).filter(models.Link.short_code == clean_id).first()
    
    if link:
        print(f"DEBUG: ID '{clean_id}' found. Redirecting to: {link.original_url}")
        new_click = models.Click(
            link_id=link.id,
            ip_address=request.client.host,
            user_agent=request.headers.get("user-agent")
        )
        db.add(new_click)
        db.commit()
        return RedirectResponse(url=link.original_url, status_code=302)
    
    print(f"DEBUG: ID '{clean_id}' NOT FOUND. Current DB Links: {db.query(models.Link).count()}")
    raise HTTPException(status_code=404, detail="Link not found")
