# ⚡ Snipr: URL Shortener & Analytics

![CI](https://github.com/AMAN0304GIT/Snipr/actions/workflows/ci.yml/badge.svg)

Shorten links, set custom aliases and expiry dates, and see who clicks them.

**Live demo:** <your-vercel-url> · **API docs:** <your-render-url>/docs

> The backend runs on a free tier and sleeps when idle, so the first request can take up to a minute.

![Home](docs/home.png)
![Analytics](docs/analytics.png)

## Features
- Short links with random Base62 codes or custom aliases
- Link expiry (1, 7 or 30 days)
- Click tracking on redirect: device, browser, referrer
- Analytics dashboard with a 14-day chart
- Per-browser link ownership (no login required)
- Per-IP rate limiting, private/own-URL blocking, friendly 404/410 pages
- Dark mode

## Tech stack
FastAPI · SQLAlchemy · PostgreSQL (SQLite locally) · Pydantic · pytest · Angular 18 · GitHub Actions · Vercel · Render · Neon

## Architecture
Angular SPA (Vercel) → FastAPI REST API (Render) → PostgreSQL (Neon).
`GET /{code}` records a click and returns a 302 redirect.

## Run locally

Backend:
```bash
cd backend
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Frontend:
```bash
cd frontend
npm install
npx ng serve
```

Tests: `cd backend && pip install -r requirements-dev.txt && python -m pytest -q`

## API
| Method | Endpoint | Description |
|---|---|---|
| POST | `/api/links` | Create a short link |
| GET | `/api/links` | List your links |
| DELETE | `/api/links/{code}` | Delete a link |
| GET | `/api/links/{code}/analytics` | Click analytics |
| GET | `/{code}` | Redirect to the original URL |

## Roadmap
JWT authentication · Redis caching · QR codes · Docker