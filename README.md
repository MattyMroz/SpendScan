# SpendScan

> Local-first receipt scanner & expense tracker — paragon → OCR → strukturalne dane → analizy.

[![CI](https://github.com/MattyMroz/SpendScan/actions/workflows/ci.yml/badge.svg)](https://github.com/MattyMroz/SpendScan/actions/workflows/ci.yml)
[![Python 3.13+](https://img.shields.io/badge/python-3.13%2B-blue)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

## Co to robi

Robisz zdjęcie paragonu (możesz wielostronicowego), aplikacja:

1. **OCR** — PaddleOCR-VL 1.5 Q8 GGUF na llama.cpp (lokalnie na GPU, ~2s/strona).
2. **Strukturyzacja** — Gemini (Flash/Lite/Gemma chain) parsuje OCR + obraz → `merchant`, `items`, `prices`, `total`, `discount`, `category`.
3. **Persystencja** — PostgreSQL (Docker), pełen audit trail (raw OCR, surowa odpowiedź LLM, oryginalne pliki).
4. **Analizy** — dashboard miesięczny, top sklepy, agregacje per dzień/kategoria.

Multi-page = **jeden paragon** (zestaw zdjęć trafia jako jeden upload, jeden Gemini call, jeden wpis w DB).

## Tech stack

| Warstwa | Wybór |
|---|---|
| **Backend** | Python 3.13, FastAPI, SQLModel, Pydantic v2 |
| **OCR** | PaddleOCR-VL 1.5 Q8 GGUF + llama-server (b9271) |
| **LLM** | Google Gemini (Flash 3.1 → Flash Lite → Gemma 4 31B fallback chain) |
| **DB** | PostgreSQL 18 (Docker) |
| **Frontend** | Vanilla HTML + CSS + jQuery (rewrite w toku) |
| **Tooling** | uv, ruff, mypy, pytest |

## Wymagania

- **Windows / Linux / WSL2**, Python 3.13+
- **GPU NVIDIA** z CUDA (testowane RTX 5090, ~3 GB VRAM dla PaddleOCR-VL Q8)
- **Docker Desktop** (PostgreSQL container)
- **uv** ([install](https://docs.astral.sh/uv/getting-started/installation/))
- **Gemini API key** (env `SPENDSCAN_GEMINI_API_KEY`)

## Quickstart

```powershell
# 1. Dependencies
uv sync

# 2. Pobierz llama.cpp binary + PaddleOCR-VL model (~1.4 GB: 498 MB Q8 + 882 MB mmproj)
uv run python scripts/prepare_ocr_runtime.py

# 3. Postgres
docker compose up -d postgres

# 4. Skonfiguruj .env
copy .env.example .env
# wypełnij: SPENDSCAN_GEMINI_API_KEY, SPENDSCAN_JWT_SECRET, SPENDSCAN_DATABASE_URL

# 5. Migracje DB
uv run python -m spendscan.db.migrations

# 6. Start backend (PaddleOCR-VL preloaduje się w lifespan, ~3s)
uv run uvicorn spendscan.api.app:app --reload
```

API: <http://127.0.0.1:8000/docs>

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
              (oryginały)                (users, receipts, items, raw_ocr, raw_llm)
```

## Smoke test

Pełen end-to-end test na 3 paragonach (po 2 strony każdy):

```powershell
$env:PYTHONPATH="backend"
uv run python scripts/smoke_paddle.py
```

Output → `workspace/output/smoke/`:

- `_report.json` — timing per paragon, per stronę, średnie
- `_SUMMARY.md` — markdown tabelka
- `receipt_NNN_ocr.txt` — surowy tekst OCR
- `receipt_NNN_analysis.json` — Pydantic dump `ReceiptAnalysisResult`

Aktualne wyniki (RTX 5090, 3 paragony Biedronka):

| Metryka | Wartość |
|---|---|
| OCR preload (lifespan) | ~2.6s |
| OCR per strona | ~2.0s |
| Gemini per paragon | ~12s |
| Total per paragon | ~16s |

## Struktura

```
backend/spendscan/
  api/            FastAPI app, routers, dependencies
  ocr/            PaddleOCR-VL engine + llama_runtime manager
  llm/            Gemini client + prompt + validation
  db/             SQLModel + repositories + migrations
  pipeline/       Receipt pipeline (OCR → LLM → DB)
  analysis/       Dashboard aggregations
external/
  bin/llama/      llama-server binaries (auto-downloaded)
  models/ocr/     PaddleOCR-VL GGUF files (~1.4 GB)
frontend/         HTML/CSS/JS (rewrite w toku)
scripts/          OCR runtime prep, smoke tests, debug
tests/            unit + integration (pytest)
workspace/
  input/          input data (paired_receipts/ test set)
  output/         generated artifacts (smoke/, debug/)
  uploads/        production receipt uploads (per-user UUID dirs)
```

## Status

- ✅ Backend pipeline (OCR + LLM + DB) działa end-to-end
- ✅ PaddleOCR-VL migracja z Qianfan (Iteracja B brainstormu)
- ✅ Lifespan preload — model w VRAM od startu serwera
- 🚧 Frontend rewrite (Iteracja C-E)
- 🚧 Auth (JWT + bcrypt, Iteracja A)
- 🚧 CRUD edycji paragonu/itemów (Iteracja E)

Pełen plan: [BRAINSTORM_SPENDSCAN_FULL_REWRITE_SUMMARY.md](temp/brain_storm/2026-05-28-spendscan-full-rewrite/BRAINSTORM_SPENDSCAN_FULL_REWRITE_SUMMARY.md).

## Dev

```powershell
uv run pytest tests/unit -q          # 34 unit testy, ~25s
uv run pytest tests/integration -q   # integracyjne (wymagają PaddleOCR + Gemini)
uv run ruff check .
uv run mypy backend/spendscan
```

## License

MIT — patrz [LICENSE](LICENSE).
