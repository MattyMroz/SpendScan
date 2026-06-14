# SpendScan

> Local-first receipt scanner & expense tracker — paragon → OCR → dane → analizy.

[![CI](https://github.com/MattyMroz/SpendScan/actions/workflows/ci.yml/badge.svg)](https://github.com/MattyMroz/SpendScan/actions/workflows/ci.yml)
[![Python 3.13+](https://img.shields.io/badge/python-3.13%2B-blue)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

## Co to robi

Robisz zdjecie paragonu (mozesz wielostronicowego), aplikacja:

1. **OCR** — PaddleOCR-VL 1.5 Q8 GGUF na llama.cpp (lokalnie na GPU, ~2s/strona)
2. **Strukturyzacja** — Gemini parsuje OCR + obraz: `merchant`, `items`, `prices`, `total`, `discount`, `category`
3. **Persystencja** — PostgreSQL w Dockerze
4. **Analizy** — dashboard miesieczny, top sklepy, kategorie, kalendarz

Multi-page = **jeden paragon** (zestaw zdjec idzie jako jeden upload, jeden Gemini call, jeden wpis w DB).

## Tech stack

| Warstwa | Wybor |
|---|---|
| **Backend** | Python 3.13, FastAPI, SQLModel, Pydantic v2 |
| **OCR** | PaddleOCR-VL 1.5 Q8 GGUF + llama-server (b9271) |
| **LLM** | Google Gemini (Flash → Flash Lite chain) |
| **DB** | PostgreSQL 18 (Docker) |
| **Frontend** | Vanilla HTML + CSS + JS (Chart.js + Lucide) |
| **Tooling** | uv, ruff, pytest |

## Wymagania

- **Windows / Linux**, Python 3.13+
- **GPU NVIDIA** z CUDA (PaddleOCR-VL Q8 = ~3 GB VRAM)
- **Docker Desktop** (PostgreSQL container)
- **uv** ([install](https://docs.astral.sh/uv/getting-started/installation/))
- **Gemini API key** (`SPENDSCAN_GEMINI_API_KEY`)

## Jak uruchomic (krok po kroku)

### 1. Zainstaluj zaleznosci

```powershell
uv sync
```

### 2. Pobierz llama.cpp + model OCR (~1.4 GB)

```powershell
uv run python scripts/prepare_ocr_runtime.py
```

Pobiera do `external/bin/llama/` oraz `external/models/ocr/paddle-ocr/`.

### 3. Wystartuj Postgres w Dockerze

```powershell
docker run --name spendscan-postgres `
  -e POSTGRES_USER=postgres `
  -e POSTGRES_PASSWORD=postgres `
  -e POSTGRES_DB=spendscan `
  -p 5432:5432 `
  -d postgres:18
```

### 4. Zaladuj schema (1 plik)

```powershell
docker cp backend/spendscan/db/migrations spendscan-postgres:/tmp/migrations
docker exec spendscan-postgres bash -lc "set -e; for f in /tmp/migrations/*.sql; do echo Running `$f; psql -U postgres -d spendscan -v ON_ERROR_STOP=1 -f `"`$f`"; done"\
```

### 5. Skonfiguruj `.env`

```powershell
copy .env.example .env
```

Wypelnij:

- `SPENDSCAN_GEMINI_API_KEY=...` — klucz z [aistudio.google.com](https://aistudio.google.com/apikey)
- `SPENDSCAN_JWT_SECRET=...` — dowolny dlugi losowy string (podpis tokenow JWT)
- `SPENDSCAN_DATABASE_URL=postgresql+psycopg://postgres:postgres@localhost:5432/spendscan`

### 6. Wystartuj backend

```powershell
$env:PYTHONPATH="backend"
uv run uvicorn spendscan.api.app:app --reload
```

Pierwszy start: ~3s na preload modelu OCR do VRAM.

### 7. Otworz aplikacje

- **Frontend** (login, scan, kalendarz, statystyki): <http://127.0.0.1:8000/>
- **API docs** (Swagger): <http://127.0.0.1:8000/docs>
- **Health**: <http://127.0.0.1:8000/health/db>

Z telefonu w tej samej sieci Wi-Fi: `http://<IP_LAPTOPA>:8000/` (sprawdz `ipconfig`).

### Dlaczego frontend leci przez FastAPI a nie Live Server?

FastAPI mountuje `frontend/public/` jako `StaticFiles` pod `/`. Powody:

- **Jeden origin** — `/api/v1/...` i `/static/...` na tym samym hoscie → zero CORS, naglowki `Authorization` dzialaja od reki
- **Jeden proces do uruchomienia** — `uvicorn` daje frontend + API + OCR + DB client jednoczesnie
- **Auth** — token JWT w `localStorage`, frontend dodaje `Authorization: Bearer ...` do kazdego calla

## Endpointy API (skrot)

Pelna lista interaktywna na `/docs`. Najwazniejsze:

| Metoda | Sciezka | Co robi |
|---|---|---|
| POST | `/api/v1/auth/register` | Rejestracja uzytkownika, zwraca JWT |
| POST | `/api/v1/auth/login` | Logowanie, zwraca JWT |
| GET  | `/api/v1/auth/me` | Profil zalogowanego uzytkownika |
| POST | `/api/v1/receipts` | Upload zdjec paragonu → OCR → LLM → zapis w DB |
| POST | `/api/v1/receipts/batch` | Upload wielu paragonow naraz (kazdy = grupa stron) |
| GET  | `/api/v1/receipts` | Lista paragonow zalogowanego uzytkownika |
| GET  | `/api/v1/receipts/{id}` | Szczegoly paragonu (items, discounts, raw OCR) |
| PATCH | `/api/v1/receipts/{id}` | Edycja paragonu (merchant, total, items, importance) |
| DELETE | `/api/v1/receipts/{id}` | Usuwa paragon + zdjecia z dysku |
| GET  | `/api/v1/receipts/{id}/images/{img_id}` | Zwraca plik zdjecia (auth-checked) |
| GET  | `/api/v1/analytics/dashboard` | Agregacje: total, kategorie, top sklepy, kalendarz |
| GET  | `/health/live` | Liveness probe |
| GET  | `/health/ready` | Readiness (model OCR + Gemini key) |
| GET  | `/health/db` | Sprawdza polaczenie z Postgres |

## Architektura

```
            ┌─────────────────────────────────────────────┐
  upload    │ FastAPI (lifespan: preload OcrService)      │
  ───────►  │   POST /api/v1/receipts                     │
            │     ├── OcrService.recognize(page_1..N)     │
            │     │     └── llama-server (PaddleOCR-VL)   │
            │     ├── GeminiReceiptClient.analyze(...)    │
            │     ├── ReceiptRepository.save(...)         │
            │     └── return ReceiptAnalysisResult        │
            └─────────────────────────────────────────────┘
                    │                            │
                    ▼                            ▼
              workspace/uploads/         PostgreSQL
              (oryginaly + strony)       (users, receipts, items, raw_ocr)
```

## Struktura katalogow

```
backend/spendscan/
  api/            FastAPI app + routery + dependencies
  ocr/            PaddleOCR-VL engine + llama_runtime
  llm/            Gemini client + prompt + walidacja
  db/             SQLModel + repositories + schema.sql
  pipeline/       Pipeline (OCR → LLM → DB)
  analysis/       Agregacje do dashboardu
  auth/           JWT + bcrypt
external/
  bin/llama/      llama-server binaries
  models/ocr/     PaddleOCR-VL GGUF (~1.4 GB)
frontend/
  public/         HTML (login, register, scan, calendar, edit, statistics)
  css/            base.css + app.css
  js/             api.js + icons.js
scripts/          OCR runtime prep, smoke test, reset DB
tests/unit/       pytest (unit tests)
workspace/
  input/          dane testowe
  output/         artefakty (smoke testy)
  uploads/        produkcyjne uploady (per-user UUID)
```

## Smoke test (opcjonalnie)

```powershell
$env:PYTHONPATH="backend"
uv run python scripts/smoke_paddle.py
```

Output w `workspace/output/smoke/`: `_report.json`, `_SUMMARY.md`, per-paragon OCR + JSON.

## Dev

```powershell
uv run pytest tests/unit -q
uv run ruff check .
uv run ruff format .
```

Reset bazy (drop + create_all z SQLModel metadata):

```powershell
$env:PYTHONPATH="backend"
uv run python scripts/reset_db.py
```

## License

MIT — patrz [LICENSE](LICENSE).
