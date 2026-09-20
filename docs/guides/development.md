# Development & Operations Guide

Instructions for running tests, database migrations, data seeding, and previewing documentation.

---

## 1. Documentation Operations

### Preview Documentation Locally (Live Reload)
To run the documentation server locally with instant browser refresh on save:

```powershell
.\.venv\Scripts\mkdocs serve
```
Open your browser at: `http://127.0.0.1:8000` (or `http://127.0.0.1:8001` if Django is running).

### Build Production Static Documentation Bundle
```powershell
.\.venv\Scripts\mkdocs build
```
This produces a static HTML/CSS/JS website in `site/` with zero server dependencies.

### Deploy to GitHub Pages for Free
```powershell
.\.venv\Scripts\mkdocs gh-deploy
```
Automatically builds and publishes the documentation to the `gh-pages` branch on your GitHub repository!

---

## 2. Automated Testing

Run the full automated test suite using `pytest`:

```powershell
# Run all tests with verbose output
.\.venv\Scripts\pytest tests/ -v

# Run only exchange tests
.\.venv\Scripts\pytest tests/test_exchanges.py -v

# Run fast unit tests skipping remote API network calls
.\.venv\Scripts\pytest tests/ -v -m "not remote"
```

---

## 3. Database & Seeding Commands

### Database Migrations
```powershell
.\.venv\Scripts\python manage.py makemigrations
.\.venv\Scripts\python manage.py migrate
```

### Seeding Canonical Master Data
```powershell
# Phase 2: Metadata Taxonomy & Units
.\.venv\Scripts\python manage.py seed_metadata

# Phase 3: Global Commodity Exchanges & Calendars
.\.venv\Scripts\python manage.py seed_exchanges

# Sync holidays on demand for a specific venue and year
.\.venv\Scripts\python manage.py sync_exchange_holidays --exchange NYMEX --year 2026
```

---

## 4. Local Web Server & Admin Portal

### Start Development Server
```powershell
.\.venv\Scripts\python manage.py runserver 127.0.0.1:8000
```

- **Dashboard UI**: `http://127.0.0.1:8000/`
- **Django Admin Portal**: `http://127.0.0.1:8000/admin/`
- **API Health Diagnostic**: `http://127.0.0.1:8000/api/health/`
- **Exchange Summary REST**: `http://127.0.0.1:8000/api/exchanges/summary/`
- **Metadata Summary REST**: `http://127.0.0.1:8000/api/metadata/summary/`
