from fastapi import FastAPI, HTTPException, Query, Depends, Request
from fastapi.responses import HTMLResponse, FileResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
import os, string, random
import models, database, utils

app = FastAPI()

# Initialize Database
models.Base.metadata.create_all(bind=database.engine)

BASE_URL = os.getenv("APP_URL", "http://localhost:8000").rstrip("/")

def get_db():
    db = database.SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.get("/", response_class=HTMLResponse)
async def read_index():
    return FileResponse("index.html")
@app.post("/shorten")
async def shorten_url(url: str, alias: str = Query(None), db: Session = Depends(get_db)):
    if not utils.check_url_safety(url):
        raise HTTPException(status_code=400, detail="URL contains suspicious content")
    
    # Ensure the URL has a protocol to prevent relative redirect 404s
    if not url.startswith(("http://", "https://")):
        url = "https://" + url

    short_id = alias if alias else ''.join(random.choices(string.ascii_letters + string.digits, k=6))

    # Check if alias exists
    existing = db.query(models.Link).filter(models.Link.short_code == short_id).first()
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

    qr_code = utils.generate_qr_base64(f"{BASE_URL}/r/{short_id}")

    return {
        "short_url": f"{BASE_URL}/r/{short_id}",
        "domain": domain,
        "ip": ip,
        "qr_code": qr_code
    }

@app.get("/r/{short_id}")
async def redirect_url(short_id: str, request: Request, db: Session = Depends(get_db)):
    link = db.query(models.Link).filter(models.Link.short_code == short_id).first()
    if link:
        # Record click analytics
        new_click = models.Click(
            link_id=link.id,
            ip_address=request.client.host,
            user_agent=request.headers.get("user-agent")
        )
        db.add(new_click)
        db.commit()
        return RedirectResponse(url=link.original_url, status_code=301)
    raise HTTPException(status_code=404, detail="Link not found")
