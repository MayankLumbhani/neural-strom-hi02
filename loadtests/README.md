# Load tests

Locust script for the public citizen endpoints:

- `POST /api/v1/chat/messages` with English, Hindi, Gujarati and Hinglish
  complaints, following the clarification flow until a ticket is created.
- `GET /api/v1/tickets/{public_id}` using ticket IDs created earlier in the same
  run.
- `GET /health` as an availability baseline.

Each simulated user first files complaints, remembers the returned ticket IDs,
and then performs status lookups against those IDs.

## Prerequisites

- Docker Desktop with the Compose plugin.
- Python 3.11+ with Locust installed: `python -m pip install locust`.

## Run

From the repository root:

```powershell
# 1. Build and start the stack. The override file raises the public rate limits
#    for this run only; it must not be used in production.
docker compose -f docker-compose.yml -f loadtests/docker-compose.loadtest.yml up -d --build

# 2. Wait until GET http://localhost:8000/ready returns status "ready".

# 3. Seed the nine synthetic departments (required for ticket routing).
docker compose -f docker-compose.yml -f loadtests/docker-compose.loadtest.yml exec -T api python -m grievance.seed

# 4. Run 20 users for 60 seconds and write raw CSV results.
python -m locust -f loadtests/locustfile.py --host http://localhost:8000 `
    --headless -u 20 -r 5 -t 60s --csv loadtests/results/locust --only-summary

# 5. Stop the stack.
docker compose -f docker-compose.yml -f loadtests/docker-compose.loadtest.yml down
```

Useful `docker compose` commands for this setup:

```powershell
docker compose -f docker-compose.yml -f loadtests/docker-compose.loadtest.yml logs -f api
docker compose -f docker-compose.yml -f loadtests/docker-compose.loadtest.yml ps
```

## Output

Locust writes these files under `loadtests/results/`:

| File | Contents |
|---|---|
| `locust_stats.csv` | Aggregate and per-endpoint request counts, failures, throughput and percentile latencies |
| `locust_stats_history.csv` | Time-series snapshots during the run |
| `locust_failures.csv` | Failed requests (header only when there are none) |
| `locust_exceptions.csv` | Uncaught exceptions (header only when there are none) |

`loadtests/results/SUMMARY.md` records the measured run and its conditions.

## Changing the load

```powershell
python -m locust -f loadtests/locustfile.py --host http://localhost:8000 `
    --headless -u 50 -r 10 -t 120s --csv loadtests/results/locust-50u
```

Keep rate limits high in `docker-compose.loadtest.yml` while measuring
application throughput. With the default `.env` limits, the per-IP quota would
produce HTTP 429 responses instead of measuring the application.
