import os
from collections import Counter
from datetime import timedelta
from typing import List
from urllib.parse import urlparse

from fastapi import Depends, FastAPI, Header, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from . import models, schemas
from .database import Base, engine, get_db
from .models import utcnow
from .rate_limit import RateLimiter
from .utils import (
    RESERVED_CODES,
    as_utc,
    generate_code,
    parse_user_agent,
    referrer_domain,
    validate_target_url,
)

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Snipr API", version="1.0.0")

BASE_URL = os.getenv("BASE_URL", "http://localhost:8000").rstrip("/")
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:4200").rstrip("/")
OWN_HOST = urlparse(BASE_URL).hostname
origins = [
    o.strip()
    for o in os.getenv("FRONTEND_ORIGINS", "http://localhost:4200").split(",")
    if o.strip()
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_methods=["*"],
    allow_headers=["*"],
)

create_limiter = RateLimiter(max_requests=20, window_seconds=60)

ERROR_PAGE = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>__TITLE__ · Snipr</title>
<style>
  :root { --bg:#f5f6fb; --text:#161925; --muted:#6b7280; --primary:#6366f1; }
  @media (prefers-color-scheme: dark) { :root { --bg:#0d0f15; --text:#e9ebf2; --muted:#98a1b3; } }
  body { margin:0; min-height:100vh; display:grid; place-items:center; text-align:center;
         font-family:system-ui,-apple-system,sans-serif; background:var(--bg); color:var(--text); }
  .code { font-size:5rem; font-weight:800; color:var(--primary); line-height:1; }
  p { color:var(--muted); }
  a { display:inline-block; margin-top:12px; padding:10px 18px; border-radius:10px;
      background:var(--primary); color:#fff; text-decoration:none; font-weight:600; }
</style>
</head>
<body>
  <div>
    <div class="code">__CODE__</div>
    <h1>__TITLE__</h1>
    <p>__MESSAGE__</p>
    <a href="__HOME__">Create a short link with Snipr</a>
  </div>
</body>
</html>"""


def error_page(status_code: int, title: str, message: str) -> HTMLResponse:
    html = (
        ERROR_PAGE.replace("__CODE__", str(status_code))
        .replace("__TITLE__", title)
        .replace("__MESSAGE__", message)
        .replace("__HOME__", FRONTEND_URL)
    )
    return HTMLResponse(html, status_code=status_code)


# ---------- helpers ----------
def get_owner_id(x_owner_id: str = Header(...)) -> str:
    if not (8 <= len(x_owner_id) <= 64):
        raise HTTPException(status_code=400, detail="Invalid owner id")
    return x_owner_id


def short_url(code: str) -> str:
    return f"{BASE_URL}/{code}"


def to_out(link: models.Link) -> schemas.LinkOut:
    return schemas.LinkOut(
        code=link.code,
        short_url=short_url(link.code),
        original_url=link.original_url,
        click_count=link.click_count,
        created_at=as_utc(link.created_at),
        expires_at=as_utc(link.expires_at),
    )


def get_owned_link(db: Session, code: str, owner_id: str) -> models.Link:
    link = (
        db.query(models.Link)
        .filter(models.Link.code == code, models.Link.owner_id == owner_id)
        .first()
    )
    if not link:
        raise HTTPException(status_code=404, detail="Link not found")
    return link


# ---------- routes ----------
@app.get("/health")
def health():
    return {"status": "ok"}


@app.post(
    "/api/links",
    response_model=schemas.LinkOut,
    status_code=201,
    dependencies=[Depends(create_limiter)],
)
def create_link(
    payload: schemas.LinkCreate,
    db: Session = Depends(get_db),
    owner_id: str = Depends(get_owner_id),
):
    target = str(payload.url)
    problem = validate_target_url(target, OWN_HOST)
    if problem:
        raise HTTPException(status_code=400, detail=problem)

    expires_at = (
        utcnow() + timedelta(days=payload.expires_in_days)
        if payload.expires_in_days
        else None
    )

    if payload.custom_alias:
        code = payload.custom_alias
        if code.lower() in RESERVED_CODES:
            raise HTTPException(status_code=400, detail="This alias is reserved")
        if db.query(models.Link).filter(models.Link.code == code).first():
            raise HTTPException(status_code=409, detail="This alias is already taken")
    else:
        code = generate_code()
        while db.query(models.Link).filter(models.Link.code == code).first():
            code = generate_code()

    link = models.Link(
        code=code,
        original_url=target,
        owner_id=owner_id,
        expires_at=expires_at,
    )
    db.add(link)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="Please try again")
    db.refresh(link)
    return to_out(link)


@app.get("/api/links", response_model=List[schemas.LinkOut])
def list_links(
    db: Session = Depends(get_db), owner_id: str = Depends(get_owner_id)
):
    links = (
        db.query(models.Link)
        .filter(models.Link.owner_id == owner_id)
        .order_by(models.Link.created_at.desc())
        .all()
    )
    return [to_out(link) for link in links]


@app.delete("/api/links/{code}", status_code=204)
def delete_link(
    code: str, db: Session = Depends(get_db), owner_id: str = Depends(get_owner_id)
):
    link = get_owned_link(db, code, owner_id)
    db.delete(link)
    db.commit()


@app.get("/api/links/{code}/analytics", response_model=schemas.AnalyticsOut)
def link_analytics(
    code: str, db: Session = Depends(get_db), owner_id: str = Depends(get_owner_id)
):
    link = get_owned_link(db, code, owner_id)
    clicks = db.query(models.Click).filter(models.Click.link_id == link.id).all()

    today = utcnow().date()
    days = [today - timedelta(days=i) for i in range(13, -1, -1)]
    per_day = Counter(as_utc(c.clicked_at).date() for c in clicks)
    clicks_by_day = [
        schemas.CountItem(label=d.strftime("%d %b"), count=per_day.get(d, 0))
        for d in days
    ]

    def top(values, limit: int = 5):
        return [
            schemas.CountItem(label=label, count=count)
            for label, count in Counter(values).most_common(limit)
        ]

    return schemas.AnalyticsOut(
        code=link.code,
        short_url=short_url(link.code),
        original_url=link.original_url,
        total_clicks=link.click_count,
        clicks_by_day=clicks_by_day,
        devices=top(c.device or "Other" for c in clicks),
        browsers=top(c.browser or "Other" for c in clicks),
        referrers=top(c.referrer or "Direct" for c in clicks),
    )


# Keep this LAST: it catches every /{code}
@app.get("/{code}")
def redirect_to_original(code: str, request: Request, db: Session = Depends(get_db)):
    link = db.query(models.Link).filter(models.Link.code == code).first()
    if not link:
        return error_page(404, "Link not found", "This short link doesn't exist or was deleted.")
    if link.expires_at and as_utc(link.expires_at) < utcnow():
        return error_page(410, "Link expired", "This short link has expired and is no longer active.")
    target = link.original_url
    device, browser = parse_user_agent(request.headers.get("user-agent", ""))
    referrer = referrer_domain(request.headers.get("referer"))[:255]

    db.add(models.Click(link_id=link.id, device=device, browser=browser, referrer=referrer))
    db.query(models.Link).filter(models.Link.id == link.id).update(
        {models.Link.click_count: models.Link.click_count + 1}
    )
    db.commit()

    return RedirectResponse(url=target, status_code=302)