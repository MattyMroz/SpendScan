# Receipt Pipeline Runbook

Krótka instrukcja odpalenia lokalnego OCR + LLM na testowych paragonach.

## Co jest w repo

- `workspace/input/receipt_001.png`
- `workspace/input/receipt_002.png`
- `workspace/input/receipt_003.png`

To są testowe paragony do demo i smoke testów. Wyniki runtime dalej zostają lokalne i ignorowane:

- `workspace/output/*.json`
- `workspace/output/debug/*.png`
- `external/`
- `.env`

## Modele LLM

Kolejność prób w `GeminiReceiptClient`:

1. `gemini-3.1-flash-lite-preview`
2. `gemini-flash-lite-latest`
3. `gemma-4-31b-it`

Gemma jest ostatnim fallbackiem. Kod ją wywoła, jeśli oba modele Flash Lite nie oddadzą poprawnego JSON-a. To zadziała pod warunkiem, że `gemma-4-31b-it` jest dostępny dla użytego klucza w Google GenAI API. Jeśli API zwróci `model not found` albo brak uprawnień, trzeba podmienić `SPENDSCAN_GEMINI_GEMMA_FALLBACK_MODEL` w `.env` na nazwę modelu widoczną w Google AI Studio.

## Kategorie

LLM ma używać tylko tych kategorii:

| Kategoria | Kiedy używać |
|-----------|--------------|
| `food` | żywność, produkty spożywcze |
| `drinks` | napoje, alkohol, kawa/herbata jako napój |
| `household` | chemia, torby, papier, środki domowe |
| `cosmetics` | kosmetyki, higiena osobista |
| `electronics` | elektronika i akcesoria |
| `clothing` | ubrania, tekstylia |
| `health` | apteka, leki, suplementy |
| `transport` | paliwo, bilety, parking |
| `services` | usługi |
| `other` | brak pewnej kategorii |

## Kroki odpalenia

1. Skopiuj env:

```powershell
Copy-Item .env.example .env
```

2. Uzupełnij w `.env`:

```text
SPENDSCAN_GEMINI_API_KEY=
```

Klucz wklej po znaku `=` tylko w lokalnym `.env`.

3. Przygotuj OCR runtime i modele:

```powershell
uv run python scripts/prepare_ocr_runtime.py
```

4. Uruchom pełny pipeline na trzech testowych paragonach:

```powershell
uv run python scripts/run_receipt_e2e.py
```

5. Wygeneruj debug PNG:

```powershell
uv run python scripts/render_receipt_debug.py
```

6. Wyniki lokalne:

```text
workspace/output/receipt_001.json
workspace/output/receipt_002.json
workspace/output/receipt_003.json
workspace/output/debug/receipt_001_debug.png
workspace/output/debug/receipt_002_debug.png
workspace/output/debug/receipt_003_debug.png
```

## Szybka walidacja

```powershell
uv run ruff check .
uv run mypy backend/ tests/
uv run pytest
```

Realny test integracyjny, z OCR + Gemini:

```powershell
$env:SPENDSCAN_RUN_E2E="1"; uv run pytest tests/integration/test_receipt_e2e.py -m integration
```
