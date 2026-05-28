# Postgres Docker Runbook

Krotka instrukcja dla lokalnego demo SpendScan z PostgreSQL w Dockerze.

## Wymagania

- Docker Desktop uruchomiony
- Port `5432` wolny
- Komendy odpalane z root projektu `SpendScan`

## Start bazy

```powershell
docker run --name spendscan-postgres `
  -e POSTGRES_USER=postgres `
  -e POSTGRES_PASSWORD=postgres `
  -e POSTGRES_DB=spendscan `
  -p 5432:5432 `
  -d postgres:18
```

Sprawdzenie gotowosci:

```powershell
docker exec spendscan-postgres pg_isready -U postgres -d spendscan
```

## Import schemy

Cala schema w jednym pliku — `backend/spendscan/db/schema.sql`:

```powershell
docker cp backend/spendscan/db/schema.sql spendscan-postgres:/tmp/schema.sql
docker exec spendscan-postgres psql -U postgres -d spendscan -v ON_ERROR_STOP=1 -f /tmp/schema.sql
```

Sprawdzenie tabel:

```powershell
docker exec spendscan-postgres psql -U postgres -d spendscan -c "\dt"
```

## Reset bazy

Gdy chcesz wyczyscic dane i zaladowac schema od zera:

```powershell
docker rm -f spendscan-postgres
docker run --name spendscan-postgres `
  -e POSTGRES_USER=postgres `
  -e POSTGRES_PASSWORD=postgres `
  -e POSTGRES_DB=spendscan `
  -p 5432:5432 `
  -d postgres:18
docker cp backend/spendscan/db/schema.sql spendscan-postgres:/tmp/schema.sql
docker exec spendscan-postgres psql -U postgres -d spendscan -v ON_ERROR_STOP=1 -f /tmp/schema.sql
```

## Demo z telefonu

1. Laptop i telefon w tej samej sieci Wi-Fi
2. Sprawdz IP laptopa: `ipconfig`
3. W telefonie: `http://<IP_LAPTOPA>:8000/`
