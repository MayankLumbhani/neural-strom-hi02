# Load test summary

Measured run on 2026-11-04. Raw Locust CSV files are in this directory
(`locust_stats.csv`, `locust_stats_history.csv`, `locust_failures.csv`,
`locust_exceptions.csv`).

## Test conditions

- Local Docker Desktop on a laptop, not the deployed environment.
- Host: ASUS Vivobook X1605VA, Intel Core i5-13420H (8 cores, 12 logical
  processors), 15.6 GB host RAM, Windows.
- Docker Desktop Linux VM: 12 CPUs, about 8 GB RAM.
- Single API container and single PostgreSQL 16 container, both on the same
  laptop, connected over the Docker Compose network.
- Classifier: TF-IDF character n-gram + Logistic Regression baseline.
- LLM extraction disabled (`LLM_ENABLED=false`).
- Database migrated with Alembic and seeded with the nine demo departments.
- Rate limits raised for this run only through
  `loadtests/docker-compose.loadtest.yml`:
  `RATE_LIMIT_CHAT=100000/minute` and `RATE_LIMIT_STATUS=100000/minute`.
  Production defaults are much lower, so these numbers measure application
  capacity without the per-IP quota.
- Load profile: 20 concurrent Locust users, spawned at 5 users/second, for
  60 seconds of user activity. One Locust process on the same host generated
  the load, so the generator and the system under test shared the laptop CPU.
- Ticket IDs used by the status endpoint were created during the same run.

## Aggregate results

| Metric | Value |
|---|---:|
| Total requests | 1,678 |
| Throughput | 29.04 requests/second |
| Failure rate | 0 of 1,678 (0.00%) |
| p50 latency | 360 ms |
| p95 latency | 650 ms |
| Average latency | 357 ms |

## Per endpoint

| Endpoint | Requests | Requests/s | p50 | p95 | Failures |
|---|---:|---:|---:|---:|---:|
| `POST /api/v1/chat/messages` | 1,257 | 21.76 | 410 ms | 680 ms | 0 |
| `GET /api/v1/tickets/{public_id}` | 306 | 5.30 | 220 ms | 370 ms | 0 |
| `GET /health` | 115 | 1.99 | 52 ms | 100 ms | 0 |

## Notes

- An earlier attempt of the same script failed 50% of chat requests with HTTP
  404 on follow-up turns. It exposed that the request-scoped database session
  was never committed, so conversations created in one request were not visible
  in the next. `get_session` now commits on success and rolls back on error, and
  the run above was recorded after that fix. The fix is included in the same
  commit as this load test.
- The chat endpoint dominates latency because each request runs language
  detection, classification and database work. Status lookups are cheaper.
- These results are from one process and one laptop. They do not represent the
  free-tier Hugging Face Space, Neon, or a multi-replica deployment.
