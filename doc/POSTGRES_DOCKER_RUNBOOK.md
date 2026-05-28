# Postgres Docker Runbook

Krotka instrukcja dla lokalnego demo SpendScan z PostgreSQL w Dockerze.

## Wymagania

- Docker Desktop uruchomiony.
- Port `5432` wolny na laptopie.
- Komendy odpalane z root projektu `SpendScan`.

## Start bazy

```powershell
docker run --name spendscan-postgres `
  -e POSTGRES_USER=postgres `
  -e POSTGRES_PASSWORD=postgres `
  -e POSTGRES_DB=spendscan `
  -p 5432:5432 `
  -d postgres:18
```

Sprawdzenie:

```powershell
docker exec spendscan-postgres pg_isready -U postgres -d spendscan
```

## Import schemy

```powershell
docker cp backend/spendscan/db/migrations/001_initial_schema.sql spendscan-postgres:/tmp/001_initial_schema.sql
docker exec spendscan-postgres psql -U postgres -d spendscan -v ON_ERROR_STOP=1 -f /tmp/001_initial_schema.sql
docker cp backend/spendscan/db/migrations/002_receipt_persistence_extensions.sql spendscan-postgres:/tmp/002_receipt_persistence_extensions.sql
docker exec spendscan-postgres psql -U postgres -d spendscan -v ON_ERROR_STOP=1 -f /tmp/002_receipt_persistence_extensions.sql
```

Sprawdzenie tabel:

```powershell
docker exec spendscan-postgres psql -U postgres -d spendscan -c "\dt"
```

## Reset bazy

Uzyj resetu, gdy schema w migracji sie zmienila albo chcesz wyczyscic demo dane.

```powershell
docker rm -f spendscan-postgres
docker run --name spendscan-postgres `
  -e POSTGRES_USER=postgres `
  -e POSTGRES_PASSWORD=postgres `
  -e POSTGRES_DB=spendscan `
  -p 5432:5432 `
  -d postgres:18
docker cp backend/spendscan/db/migrations/001_initial_schema.sql spendscan-postgres:/tmp/001_initial_schema.sql
docker exec spendscan-postgres psql -U postgres -d spendscan -v ON_ERROR_STOP=1 -f /tmp/001_initial_schema.sql
docker cp backend/spendscan/db/migrations/002_receipt_persistence_extensions.sql spendscan-postgres:/tmp/002_receipt_persistence_extensions.sql
docker exec spendscan-postgres psql -U postgres -d spendscan -v ON_ERROR_STOP=1 -f /tmp/002_receipt_persistence_extensions.sql
```

## Uruchomienie API

```powershell
$env:PYTHONPATH="backend"
$env:SPENDSCAN_DATABASE_URL="postgresql+psycopg://postgres:postgres@localhost:5432/spendscan"
$env:SPENDSCAN_UPLOAD_DIR="workspace/uploads/receipts"
.\.venv\Scripts\python.exe -m uvicorn spendscan.api.app:app --host 0.0.0.0 --port 8000 --reload --reload-dir backend
```

Lokalnie:

```text
http://127.0.0.1:8000/docs
http://127.0.0.1:8000/health/db
```

## Demo z telefonu

1. Laptop i telefon musza byc w tej samej sieci Wi-Fi.
2. Sprawdz IP laptopa:

```powershell
ipconfig
```

3. W telefonie wejdz:

```text
http://<IP_LAPTOPA>:8000/docs
```

4. W Swagger UI uzyj:

- `POST /api/v1/receipts` dla jednego paragonu z jednym albo wieloma zdjeciami.
- `POST /api/v1/receipts/batch` dla kilku osobnych paragonow.
- `GET /api/v1/analytics/dashboard` dla statystyk.

Jesli telefon nie widzi API, sprawdz zapore Windows i czy `uvicorn` dziala z `--host 0.0.0.0`.

## Stop / start istniejacego kontenera

```powershell
docker stop spendscan-postgres
docker start spendscan-postgres
```
