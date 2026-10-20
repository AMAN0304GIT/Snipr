from datetime import datetime, timedelta, timezone

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app import models
from app.database import Base, get_db
from app.main import app, create_limiter

engine = create_engine(
    "sqlite://",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSession = sessionmaker(bind=engine, autoflush=False, autocommit=False)


def override_get_db():
    db = TestingSession()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db
app.dependency_overrides[create_limiter] = lambda: None

client = TestClient(app)
OWNER_A = {"X-Owner-Id": "owner-aaaaaaaa"}
OWNER_B = {"X-Owner-Id": "owner-bbbbbbbb"}


@pytest.fixture(autouse=True)
def fresh_db():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield


def create(url="https://example.com/page", headers=OWNER_A, **extra):
    return client.post("/api/links", json={"url": url, **extra}, headers=headers)


def test_health():
    assert client.get("/health").json() == {"status": "ok"}


def test_create_and_list_link():
    res = create()
    assert res.status_code == 201
    body = res.json()
    assert len(body["code"]) == 6
    assert body["click_count"] == 0

    listed = client.get("/api/links", headers=OWNER_A).json()
    assert [l["code"] for l in listed] == [body["code"]]


def test_missing_owner_header_is_rejected():
    res = client.post("/api/links", json={"url": "https://example.com"})
    assert res.status_code == 422


def test_redirect_counts_clicks_and_updates_analytics():
    code = create().json()["code"]

    for _ in range(3):
        res = client.get(f"/{code}", follow_redirects=False)
        assert res.status_code == 302
        assert res.headers["location"].startswith("https://example.com/page")

    stats = client.get(f"/api/links/{code}/analytics", headers=OWNER_A).json()
    assert stats["total_clicks"] == 3
    assert sum(d["count"] for d in stats["clicks_by_day"]) == 3
    assert stats["referrers"][0]["label"] == "Direct"


def test_custom_alias_and_conflict():
    assert create(custom_alias="my-link").status_code == 201
    assert create(custom_alias="my-link").status_code == 409


def test_reserved_alias_is_rejected():
    assert create(custom_alias="docs").status_code == 400


def test_invalid_alias_characters_are_rejected():
    assert create(custom_alias="bad alias!").status_code == 422


def test_blocks_own_and_private_urls():
    assert create(url="http://localhost:8000/abc").status_code == 400
    assert create(url="http://192.168.1.10/admin").status_code == 400
    assert create(url="http://127.0.0.1:5000").status_code == 400


def test_unknown_code_returns_404_page():
    res = client.get("/doesnotexist", follow_redirects=False)
    assert res.status_code == 404
    assert "Link not found" in res.text


def test_expired_link_returns_410():
    code = create(expires_in_days=1).json()["code"]

    db = TestingSession()
    link = db.query(models.Link).filter_by(code=code).first()
    link.expires_at = datetime.now(timezone.utc) - timedelta(days=1)
    db.commit()
    db.close()

    res = client.get(f"/{code}", follow_redirects=False)
    assert res.status_code == 410


def test_owner_isolation():
    code = create(headers=OWNER_A).json()["code"]

    assert client.get("/api/links", headers=OWNER_B).json() == []
    assert client.get(f"/api/links/{code}/analytics", headers=OWNER_B).status_code == 404
    assert client.delete(f"/api/links/{code}", headers=OWNER_B).status_code == 404


def test_delete_link():
    code = create().json()["code"]
    assert client.delete(f"/api/links/{code}", headers=OWNER_A).status_code == 204
    assert client.get(f"/{code}", follow_redirects=False).status_code == 404