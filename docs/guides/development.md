# Development & Operations Guide

Complete guide for local environment setup, virtual environment creation, modular dependency architecture, database migrations, master data seeding, automated testing, and documentation operations.

---

## 1. Quickstart & Environment Setup

When cloning or pulling the repository from GitHub, the `.venv` folder is intentionally excluded by `.gitignore`. You must create a local virtual environment and install the platform dependencies before running any commands.

### Step 1: Clone the Repository
```bash
git clone https://github.com/nansari-0134/commodity-market-smart-analyst.git
cd commodity-market-smart-analyst
```

### Step 2: Create a Virtual Environment
Ensure you have **Python 3.11+** installed:

```bash
# Creates a virtual environment named '.venv' in the project root
python -m venv .venv
```

### Step 3: Activate the Virtual Environment

=== "Windows (PowerShell)"
    ```powershell
    .\.venv\Scripts\Activate.ps1
    ```
    *(If script execution is disabled: `Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser`)*

=== "Windows (Command Prompt)"
    ```cmd
    .\.venv\Scripts\activate.bat
    ```

=== "Linux / macOS (Bash / Zsh)"
    ```bash
    source .venv/bin/activate
    ```

Once activated, your terminal prompt will display `(.venv)` and standard CLI binaries (`python`, `pip`, `pytest`, `mkdocs`) resolve directly into your isolated environment without needing absolute paths.

### Step 4: Install Dependencies
The platform uses a 3-tier modular requirements architecture inside the `requirements/` directory. For local development and testing, install using either command:

```bash
# Option A: Standard single-command installation (proxies to requirements/local.txt)
pip install -r requirements.txt

# Option B: Explicit local development installation
pip install -r requirements/local.txt
```

*(See [Section 2: Dependency Architecture & Requirements Hierarchy](#dependency-architecture) for details on why this structure is used).*

### Step 5: Configure Environment Variables
```bash
# Copy the example environment file
cp .env.example .env
```
Customize `.env` with your API keys, database settings, and pluggable provider selections as needed.

### Step 6: Initialize Database & Run Migrations
```bash
python manage.py migrate
```

### Step 7: Seed Foundational Master Data
Run the idempotent management seeders in sequence:

```bash
# 1. Units of Measure, Taxonomy & Observation Frequencies
python manage.py seed_metadata

# 2. Global Exchanges, Sessions & Holiday Rules
python manage.py seed_exchanges

# 3. Physical Commodities & Multi-Exchange Listings
python manage.py seed_commodities

# 4. Derivative Contract Specifications & Expiry Calendars
python manage.py seed_contracts

# 5. Metadata Catalog (Providers, Datasets, Endpoints, Variables)
python manage.py seed_providers
python manage.py seed_datasets
python manage.py seed_endpoints
python manage.py seed_variables

# 6. Ingest Historical Time-Series Observations (Prices, COT, Fundamentals)
python manage.py ingest_market_data
```

---

## 2. Dependency Architecture & Requirements Hierarchy {: #dependency-architecture }

Instead of maintaining a single monolithic `requirements.txt` that bloats production Docker containers with testing tools and documentation generators, the platform adopts an institutional **3-tier modular dependency architecture** inside the `requirements/` directory:

```
commodity-market-smart-analyst/
├── requirements.txt            # Root convenience proxy (points to requirements/local.txt)
└── requirements/
    ├── base.txt                # Core runtime dependencies (Django, DRF, Pydantic, Celery, Redis)
    ├── local.txt               # Development & testing tools (-r base.txt + pytest, ruff, mkdocs)
    └── production.txt          # Production server dependencies (-r base.txt + gunicorn, uvicorn)
```

### The 3 Tier Breakdown

| File | Target Environment | Included Packages | Purpose |
| :--- | :--- | :--- | :--- |
| **`requirements/base.txt`** | All environments | `Django`, `psycopg[binary]`, `djangorestframework`, `pydantic`, `httpx`, `celery`, `redis`, `python-dateutil`, `pytz`, `django-environ` | Core application runtime, relational database drivers, data validation schemas, and async task queuing. |
| **`requirements/local.txt`** | Local dev & CI test runners | `-r base.txt`<br/>`pytest`, `pytest-django`, `ruff`, `ipython`, `mkdocs-material` | Unit testing, linting, interactive debugging, and local documentation live-reload server. |
| **`requirements/production.txt`** | Production containers & K8s | `-r base.txt`<br/>`gunicorn`, `uvicorn[standard]` | High-concurrency WSGI and ASGI application server workers. Excludes test and doc libraries to minimize image attack surface and build size. |
| **`requirements.txt` (Root)** | New developers cloning repo | `-r requirements/local.txt` | Standard GitHub entry point so running `pip install -r requirements.txt` immediately installs the complete local development environment. |

### Environment Decision Guide

* **When onboarding locally or contributing code**:
  ```bash
  pip install -r requirements.txt
  ```
* **When running headless CI/CD test pipelines (GitHub Actions)**:
  ```bash
  pip install -r requirements/local.txt
  ```
* **When building production Docker images**:
  ```dockerfile
  RUN pip install --no-cache-dir -r requirements/production.txt
  ```

### Rules for Adding New Dependencies
1. **Core Runtime Libraries**: If a package is imported inside `apps/` or `config/` (e.g. `numpy`, `scipy` for quant models), add it to `requirements/base.txt`.
2. **Developer & Testing Tools**: If a package is only used for debugging, mocking, profiling, or documentation (e.g. `pytest-mock`, `factory-boy`), add it to `requirements/local.txt`.
3. **Deployment Tools**: If a package is only used for serving or process management in production, add it to `requirements/production.txt`.

---

## 3. Local Web Server & Terminal Dashboard

Start the Django development server:

```bash
python manage.py runserver 127.0.0.1:8000
```

- **Intelligence Terminal UI**: [http://127.0.0.1:8000/](http://127.0.0.1:8000/)
- **Visual Data Explorer**: [http://127.0.0.1:8000/explorer/](http://127.0.0.1:8000/explorer/)
- **Django Admin Portal**: [http://127.0.0.1:8000/admin/](http://127.0.0.1:8000/admin/)
- **API Health Diagnostic**: [http://127.0.0.1:8000/api/health/](http://127.0.0.1:8000/api/health/)
- **Market Data Summary API**: [http://127.0.0.1:8000/api/market-data/summary/](http://127.0.0.1:8000/api/market-data/summary/)

---

## 4. Automated Testing

Run the full automated test suite using `pytest`:

```bash
# Run the entire test suite (107+ tests) with verbose output
pytest tests/ -v

# Run fast unit tests skipping remote network APIs
pytest tests/ -v -m "not remote"

# Run tests for a specific domain module
pytest tests/test_market_data.py -v
pytest tests/test_variables.py -v
pytest tests/test_commodities.py -v
```

---

## 5. Documentation Operations

The documentation is powered by **Material for MkDocs**.

### Preview Documentation Locally (Hot-Reload)
Run the documentation server locally with instant browser refresh on save:

```bash
mkdocs serve
```
*(Or specify port if 8000 is occupied by Django: `mkdocs serve -a 127.0.0.1:8001`)*

Open your browser at: [http://127.0.0.1:8001](http://127.0.0.1:8001).

### Strict Build Validation
Validate that all links, anchors, and cross-references resolve with zero warnings:

```bash
mkdocs build --strict
```

### Deploy to GitHub Pages
Publish the production documentation to GitHub Pages:

```bash
mkdocs gh-deploy
```

---

## 6. Management & Ingestion CLI Commands

| Command | Description |
| :--- | :--- |
| `python manage.py makemigrations` | Detect schema changes and generate migration files. |
| `python manage.py migrate` | Apply pending database migrations. |
| `python manage.py seed_commodities [--clear]` | Populate physical commodity benchmarks. |
| `python manage.py seed_contracts [--clear]` | Populate derivative specifications and calendar roll rules. |
| `python manage.py seed_datasets [--clear]` | Populate benchmark datasets catalog. |
| `python manage.py seed_variables [--clear]` | Populate variable and feature catalog. |
| `python manage.py seed_providers [--clear]` | Populate data vendor registry and rate limits. |
| `python manage.py seed_endpoints [--clear]` | Populate API route templates and schemas. |
| `python manage.py ingest_market_data [--type=prices\|cot\|fundamentals] [--days=N]` | Ingest historical or live observations. |
| `python manage.py add_feature --code=... --unit=...` | Declaratively onboard a new feature into the 4-tier catalog. |
| `python manage.py sync_exchange_holidays --exchange NYMEX --year 2026` | Sync institutional trading calendar holidays. |
