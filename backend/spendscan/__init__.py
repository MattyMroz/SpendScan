"""SpendScan - receipt scanning and expense analysis application.

# SpendScan - technical documentation

SpendScan is a local-first web application that turns a photo of a receipt
into structured spending data. The user uploads an image (or several images
of a single receipt), and the system:

1. **OCR** - a local PaddleOCR-VL model (run through llama.cpp on the GPU)
   reads the text from the image.
2. **Structuring** - the Google Gemini language model organizes the text into
   structured JSON: merchant, date, items, prices, discounts, categories.
3. **Persistence** - the result is stored in a PostgreSQL database.
4. **Analytics** - the statistics section shows categories, shops, trends and
   a calendar.

Several images of one receipt are treated as **a single receipt** (one call to
the language model, one database record).

## Architecture

The application follows a client-server architecture. The server (FastAPI)
handles the API, OCR, language model, database and analytics. The frontend
(plain HTML, CSS, JavaScript) is served by the same process as the API, so it
uses a single origin and simple, secure cookies.

```
  upload    FastAPI (preloads OcrService in lifespan)
  ------->    POST /api/v1/receipts
                |-- OcrService.recognize(page 1..N)   -> llama-server (PaddleOCR-VL)
                |-- GeminiReceiptClient.analyze(...)   -> JSON
                |-- ReceiptRepository.save(...)        -> PostgreSQL
                +-- return ReceiptAnalysisResult
```

## Package structure

| Module | Responsibility |
|---|---|
| `spendscan.api` | FastAPI application, routers, HTTP entry points, dependencies |
| `spendscan.ocr` | OCR engine (PaddleOCR-VL) and llama-server process management |
| `spendscan.llm` | Gemini client, prompt, JSON output validation |
| `spendscan.db` | Repositories and database connection |
| `spendscan.models` | SQLModel data models (tables) |
| `spendscan.pipeline` | Processing flow: OCR -> language model -> persistence |
| `spendscan.analysis` | Data aggregation for the analytics dashboard |
| `spendscan.auth` | Authentication: JWT, bcrypt, HttpOnly cookies, CSRF protection |
| `spendscan.config` | Central configuration driven by environment variables |
| `spendscan.errors` | Application exception hierarchy |

## Technology stack

| Layer | Choice |
|---|---|
| Backend | Python 3.13, FastAPI, SQLModel, Pydantic v2 |
| OCR | PaddleOCR-VL 1.5 Q8 (GGUF) + llama-server |
| Language model | Google Gemini (with fallback models) |
| Database | PostgreSQL 18 (Docker) |
| Frontend | HTML + CSS + JavaScript (Chart.js, Lucide) |
| Tooling | uv, ruff, mypy, pytest |

## Requirements

- Windows or Linux, Python 3.13 or newer.
- NVIDIA GPU with CUDA (the OCR model runs on the GPU, ~3 GB VRAM).
- Docker Desktop (PostgreSQL container).
- The `uv` package manager.
- A Gemini API key (`SPENDSCAN_GEMINI_API_KEY`).

## Getting started (step by step)

**1. Install dependencies**

```powershell
uv sync
```

**2. Download llama.cpp and the OCR model (~1.4 GB)**

```powershell
uv run python scripts/prepare_ocr_runtime.py
```

**3. Start PostgreSQL in Docker**

```powershell
docker run --name spendscan-postgres `
  -e POSTGRES_USER=postgres `
  -e POSTGRES_PASSWORD=postgres `
  -e POSTGRES_DB=spendscan `
  -p 5432:5432 `
  -d postgres:18
```

**4. Load the database schema**

```powershell
docker cp backend/spendscan/db/migrations spendscan-postgres:/tmp/migrations
docker exec spendscan-postgres bash -lc "for f in /tmp/migrations/*.sql; do psql -U postgres -d spendscan -f $f; done"
```

**5. Configure the `.env` file**

```powershell
copy .env.example .env
```

Fill in: `SPENDSCAN_GEMINI_API_KEY`, `SPENDSCAN_JWT_SECRET` and
`SPENDSCAN_DATABASE_URL`.

**6. Start the server**

```powershell
$env:PYTHONPATH="backend"
uv run uvicorn spendscan.api.app:app --reload
```

**7. Open the application**

- Frontend: <http://127.0.0.1:8000/>
- Interactive API docs (Swagger): <http://127.0.0.1:8000/docs>
- Database health check: <http://127.0.0.1:8000/health/db>

## Working with the code (dev)

```powershell
uv run pytest tests/unit -q     # unit tests
uv run ruff check .             # code quality checks
uv run ruff format .            # formatting
uv run mypy backend/            # type checking
```

## Configuration

The application is driven by environment variables prefixed with `SPENDSCAN_`.
The full list of settings and their defaults lives in the
`spendscan.config.Settings` class. The defaults are safe for a development
environment; before a production deployment you should set your own JWT secret,
enable secure cookies, and add HTTPS and file-size limits.
"""

from __future__ import annotations

__version__ = "0.1.0"
