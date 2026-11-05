# Scaling notes

This document separates what was measured from what is only a design idea.
Nothing in the second section is implemented, deployed or benchmarked.

## Current shape

- Stateless FastAPI API. Conversation state, tickets and events live in
  PostgreSQL, so any API replica can serve any request.
- One process serves the API, loads the classifier once at startup and runs the
  APScheduler escalation job in-process.
- The classifier is behind the `Classifier` interface. The default is the
  TF-IDF + Logistic Regression baseline; MuRIL is optional.
- Public rate limits are process-local sliding windows (D-15).
- The database is PostgreSQL; migrations run through Alembic.

## Measured

The only measured numbers come from the local load test recorded in
`loadtests/results/SUMMARY.md`. Raw Locust CSV files are next to that summary.

### Conditions

- Local Docker Desktop on a laptop, not a deployed environment.
- Host: ASUS Vivobook, Intel Core i5-13420H (8 cores, 12 logical processors),
  15.6 GB RAM. Docker Desktop VM: 12 CPUs, about 8 GB RAM.
- One API container and one PostgreSQL 16 container on the same laptop.
- Baseline TF-IDF + Logistic Regression classifier; LLM extraction disabled.
- 20 concurrent Locust users for 60 seconds, spawned at 5 users/second. The
  Locust generator ran on the same laptop as the system under test.
- Public rate limits were raised to `100000/minute` for this run only so the
  measurement reflects application capacity rather than the per-IP quota.
- Ticket-status requests used ticket IDs created during the same run.

### Results

| Metric | Measured value |
|---|---:|
| Total requests | 1,678 |
| Aggregate throughput | 29.04 requests/second |
| Failure rate | 0 of 1,678 (0.00%) |
| p50 latency | 360 ms |
| p95 latency | 650 ms |
| Average latency | 357 ms |

| Endpoint | Requests | Requests/s | p50 | p95 | Failures |
|---|---:|---:|---:|---:|---:|
| `POST /api/v1/chat/messages` | 1,257 | 21.76 | 410 ms | 680 ms | 0 |
| `GET /api/v1/tickets/{public_id}` | 306 | 5.30 | 220 ms | 370 ms | 0 |
| `GET /health` | 115 | 1.99 | 52 ms | 100 ms | 0 |

### What this does and does not show

- It shows that one local API process on this laptop sustained about 29
  requests/second with a p95 of 650 ms under this mixed workload.
- The chat endpoint dominates latency because each request performs language
  detection, classification and database work. Status lookups are cheaper.
- It does not measure the Render free tier, Neon, Vercel, a cold start, the
  MuRIL backend, a multi-replica deployment, or the default production rate
  limits. The load generator and the API shared CPU, so the numbers are a
  laptop-scale indication, not a capacity promise.

## Design-only ideas, not implemented or measured

The items below are a scale-out path. None of them is in the current build.

### Horizontal API replicas

The API is stateless, so several replicas can sit behind a load balancer. Two
current components are per process and need attention first:

- **Rate limiting is process-local.** Each worker or replica keeps its own
  per-IP sliding window. Aggregate limits across replicas are not enforced.
  Moving to a shared limiter is a prerequisite for trusting rate limits at more
  than one replica.
- **The escalation scheduler runs in-process.** Every API process starts its own
  APScheduler job. The escalation update is an eligibility-guarded
  `UPDATE ... WHERE`, so it is idempotent and safe to run concurrently, but
  running more replicas also means more schedulers. A single dedicated worker
  would be cleaner.

### Shared rate limiter

Replace the in-memory windows with a shared store such as Redis so all replicas
see one quota per client. This is not implemented; it would add infrastructure
and a dependency decision. A database-backed counter is a cheaper alternative
for small deployments but adds write load to PostgreSQL.

### Queue between intake and classification

During a traffic spike, a queue could accept complaints immediately and
classify them asynchronously. The citizen would get a "received" ticket ID
first, and department assignment would follow. This is not implemented. The
current stack intentionally avoids Redis and a task queue (D-03, D-06), so this
would require a new decision entry and an operational component.

### Model serving on GPU or ONNX

The default baseline is lightweight, and the optional MuRIL backend runs on CPU.
An ONNX export with quantization is a documented future optimization (T-31) but
is not implemented. Separating inference into its own service would let it
scale independently from the API and database. Neither is measured here.

### PostgreSQL read replicas and partitioning

Read replicas could serve analytics and ticket-list queries while the primary
handles writes. Large ticket tables could later be partitioned by region or
date. Neither is implemented; the current schema and queries are designed for a
single primary.

### Metrics, tracing and alerting

Structured JSON logs and health/readiness endpoints exist. Metrics, distributed
tracing and alerting are a documented future step and are not part of the
hackathon build.

### Suggested order

1. Shared rate limiter, so replicas enforce one quota.
2. Dedicated escalation worker or leader election, so schedulers do not multiply.
3. Horizontal API replicas behind a load balancer.
4. A queue for classification spikes if traffic justifies it.
5. Read replicas and partitioning when database load becomes the bottleneck.
6. Model-service split or ONNX when inference latency becomes the bottleneck.

Every step above is design-only until it is implemented and measured.
