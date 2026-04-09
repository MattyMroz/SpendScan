# Contributing

Zasady współpracy w projekcie SpendScan.

---

## Git Workflow

Używamy **GitHub Flow** — prosta, PR-centric strategia.

```
main (chroniony, zawsze deployowalny)
  └── feature/<owner>-<opis>   ← twój branch
```

### Lifecycle feature

```bash
# 1. Aktualny main
git checkout main && git pull

# 2. Nowy branch
git checkout -b feature/<twoj-nick>-<opis>

# 3. Koduj + commituj (Conventional Commits!)
git add . && git commit -m "feat(ocr): add grayscale preprocessing"

# 4. Push
git push -u origin feature/<twoj-nick>-<opis>

# 5. Otwórz PR na GitHubie
#    → Tytuł PR = Conventional Commit format
#    → Opisz: co, dlaczego, jak testować

# 6. CI musi przejść ✅ + min 1 approval ✅

# 7. Squash merge → branch auto-deleted
```

---

## Branch Naming

**Format:** `<type>/<owner>-<description>`

- Lowercase, kebab-case, max 50 znaków
- Owner = twój nick (piotr, jakub, mateusz, igor, mslon)

| Type | Kiedy |
|------|-------|
| `feature/` | Nowa funkcjonalność |
| `bugfix/` | Fix buga |
| `hotfix/` | Urgent production fix |
| `chore/` | Maintenance, deps, config |
| `docs/` | Dokumentacja |
| `test/` | Testy |
| `ci/` | CI/CD changes |

**Przykłady:**
- `feature/jakub-ocr-preprocess`
- `bugfix/piotr-db-null-price`
- `chore/mateusz-ci-cache`
- `docs/igor-readme-setup`

---

## Conventional Commits

**Format:** `<type>[scope]: <description>`

```bash
# ✅ Dobrze
feat(ocr): add grayscale preprocessing for receipts
fix(api): return 404 for missing receipt
chore(deps): add ocr dependency
test(analysis): add categorization unit tests
docs(readme): update setup instructions

# ❌ Źle
fix stuff
updated code
WIP
feat: Add New Feature.
```

### Reguły

- Type jest **obowiązkowy**: `feat`, `fix`, `docs`, `refactor`, `test`, `chore`, `ci`
- Tryb rozkazujący, **lowercase**, bez kropki na końcu
- Max **72 znaki** w pierwszej linii
- 1 commit = 1 logiczna zmiana

---

## Pull Requests

| Reguła | Wartość |
|--------|---------|
| Max rozmiar | 800 LOC (>1000 = split!) |
| Min approvals | 1 |
| Review time | < 24h (cel: same-day) |
| Merge strategy | **Squash merge** (jedyny dozwolony) |

### PR title

Musi być w formacie Conventional Commits — to będzie commit msg na `main`:
- `feat(ocr): add receipt text extraction`
- `fix(db): handle null prices in receipts`

### Opis PR

```markdown
## What
Co zmienia ten PR? 1-3 zdań.

## Why
Dlaczego ta zmiana? Link do issue: Closes #XX

## How to test
Kroki do przetestowania / automatyczne testy

## Checklist
- [ ] Code follows project conventions
- [ ] Tests added/updated
- [ ] Linter passes (ruff + mypy)
- [ ] No secrets or credentials committed
```

### Review etykieta

| Prefix | Znaczenie | Blocking? |
|--------|-----------|-----------|
| (brak) | Normalne sugestia | Must fix |
| `nit:` | Kosmetyka | Non-blocking |
| `question:` | Pytanie | Non-blocking |
| `blocker:` | Blocker | Must fix |
| `praise:` | Chwalę! | 😊 |

---

## Setup deweloperski

```bash
# Zainstaluj uv (jeśli nie masz)
# Windows: powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
# Linux/macOS: curl -LsSf https://astral.sh/uv/install.sh | sh

# Klonuj i setup
git clone https://github.com/MattyMroz/SpendScan.git
cd SpendScan
uv sync
uv run pre-commit install
```

### Codzienna pętla

```bash
# Lint + format + type check
uv run ruff check --fix .
uv format
uv run mypy backend/

# Testy
uv run pytest

# Commit (pre-commit zrobi lint/format automatycznie)
git commit -m "feat(scope): opis"
```

---

## Zasady kodu

- **Python ≥3.13**, `from __future__ import annotations` w każdym pliku
- **Type hints everywhere** — mypy strict mode
- **ruff** — linter + formatter (line-length 120)
- **pytest** — testy w `tests/`
- **Docstrings** — Google-style
- `uv add <pkg>` — **NIGDY** ręcznie edytuj dependencies w pyproject.toml
