# SpendScan

> Aplikacja analizująca wydatki na podstawie zdjęć paragonów.

[![CI](https://github.com/MattyMroz/SpendScan/actions/workflows/ci.yml/badge.svg)](https://github.com/MattyMroz/SpendScan/actions/workflows/ci.yml)
[![Python 3.13+](https://img.shields.io/badge/python-3.13%2B-blue)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

## Opis

SpendScan automatyzuje kontrolę wydatków — robisz zdjęcie paragonu, a aplikacja:

1. **Rozpoznaje tekst** (OCR — Tesseract)
2. **Wyodrębnia produkty i ceny**
3. **Przypisuje kategorie** (Żywność, Chemia, Elektronika itp.)
4. **Generuje analizy** — dashboard miesięczny, trendy, alerty budżetowe

## Tech Stack

| Warstwa | Technologia |
|---------|-------------|
| **Backend** | Python 3.13+, FastAPI, Tesseract OCR |
| **Mobile** | React Native (Expo) |
| **Baza danych** | SQLite (dev) |
| **Tooling** | uv, ruff, mypy, pytest, pre-commit |
| **CI/CD** | GitHub Actions |

## Struktura projektu

```
SpendScan/
├── backend/spendscan/    # Backend Python (FastAPI + OCR)
│   ├── api/              # FastAPI endpoints
│   ├── ocr/              # Przetwarzanie obrazu + OCR
│   ├── analysis/         # Analityka wydatków
│   ├── models/           # Pydantic models + DB schema
│   └── db/               # Database layer
├── frontend/             # Expo React Native (thin client)
├── tests/                # Testy (unit + integration)
├── assets/               # Brand assets (logo, ikona)
├── doc/                  # Dokumentacja projektu
└── scripts/              # Pomocnicze skrypty
```

## Quick Start

### Wymagania

- Python ≥3.13
- [uv](https://docs.astral.sh/uv/getting-started/installation/)
- Tesseract OCR (`apt install tesseract-ocr tesseract-ocr-pol` / `brew install tesseract`)

### Setup

```bash
# 1. Klonuj repo
git clone https://github.com/MattyMroz/SpendScan.git
cd SpendScan

# 2. Zainstaluj zależności
uv sync

# 3. Zainstaluj pre-commit hooks
uv run pre-commit install

# 4. Sprawdź że tooling działa
uv run ruff check .
uv run mypy backend/
uv run pytest
```

## Workflow

Szczegóły w [CONTRIBUTING.md](CONTRIBUTING.md).

**TL;DR:**
1. Stwórz branch: `git checkout -b feature/<twoj-nick>-<opis>`
2. Commituj: `feat(scope): opis` (Conventional Commits)
3. Push + PR → min 1 review → squash merge

## Zespół

| Osoba | Specjalizacja | Obszar |
|-------|--------------|--------|
| Piotr Marczak | EAIBD | DB + analityka |
| Jakub Bryła | EAIBD | OCR pipeline |
| Mateusz Mróz | EAIBD | API + infra/CI |
| Igor Typiński | Inżynieria Oprogramowania | Testy + QA |
| Mateusz Słoń | Technologie Internetowe | Mobile (Expo) |

## Licencja

[MIT](LICENSE)
