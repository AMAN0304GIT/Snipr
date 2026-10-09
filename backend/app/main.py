import os
from collections import Counter
from datetime import timedelta
from typing import List

from fastapi import Depends, FastAPI, Header, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from . import models, schemas
from .database import Base, engine, get_db
from .models import utcnow
from .utils import RESERVED_CODES, as_utc, generate_code, parse_user_agent, referrer_domain

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Snipr API", version="1.0.0")

BASE_URL = os.getenv("BASE_URL", "http://localhost:8000").rstrip("/")
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


@app.post("/api/links", response_model=schemas.LinkOut, status_code=201)
def create_link(
    payload: schemas.LinkCreate,
    db: Session = Depends(get_db),
    owner_id: str = Depends(get_owner_id),
):
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
        original_url=str(payload.url),
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
        raise HTTPException(status_code=404, detail="Short link not found")
    if link.expires_at and as_utc(link.expires_at) < utcnow():
        raise HTTPException(status_code=410, detail="This link has expired")

    target = link.original_url
    device, browser = parse_user_agent(request.headers.get("user-agent", ""))
    referrer = referrer_domain(request.headers.get("referer"))[:255]

    db.add(models.Click(link_id=link.id, device=device, browser=browser, referrer=referrer))
    db.query(models.Link).filter(models.Link.id == link.id).update(
        {models.Link.click_count: models.Link.click_count + 1}
    )
    db.commit()

    return RedirectResponse(url=target, status_code=302)