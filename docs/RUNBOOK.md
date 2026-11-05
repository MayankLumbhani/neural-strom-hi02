# Runbook

Operational steps for running, deploying and troubleshooting the grievance
chatbot. Never commit `.env` or any real secret. Use placeholders and set real
values only in the local environment, Space secrets or the Vercel dashboard.

## Local run with Docker Compose

Prerequisites: Docker Desktop with the Compose plugin.

```bash
cp .env.example .env
# Edit .env: set POSTGRES_PASSWORD, JWT_SECRET and the DEMO_* credentials.
docker compose up -d --build
curl http://localhost:8000/ready
```

The API container waits for PostgreSQL, runs `alembic upgrade head`, runs the
idempotent seed, and then serves on `PORT` (Compose defaults to 8000).
`API_PORT` controls the host port. The seed creates the nine departments and,
when `DEMO_MODE=true` and `DEMO_*` is complete, the demo officer/admin accounts.
It is safe to run again manually:

```bash
docker compose exec -T api python -m grievance.seed
```

Run the frontend against the local API:

```bash
cd frontend
npm ci
cp .env.example .env
# Set VITE_API_BASE_URL=http://localhost:8000
npm run dev
```

Stop the stack with `docker compose down`. Add `-v` only when you intend to
delete the local PostgreSQL volume.

### Without Docker

```bash
python -m venv .venv
# Activate the environment for your shell.
python -m pip install -e ".[dev]"
cp .env.example .env
python -m alembic -c backend/alembic.ini upgrade head
python -m grievance.seed
python -m uvicorn grievance.main:app --app-dir backend/src --reload
```

The default baseline classifier is fitted once when the Docker image is built
and saved to `ml/artifacts/baseline.joblib` inside the image. At startup it
loads that artifact and logs `classifier.baseline.loaded source=artifact`.
Without Docker, if the artifact is absent, it falls back to fitting from the
committed synthetic `ml/data/processed/train.csv` and logs `source=csv`. The
generated artifact is Git-ignored; rebuild the image after changing the CSV.

## Environment variables

Names only; values belong in `.env` or host secrets.

| Variable | Purpose |
|---|---|
| `APP_ENV` | `development`, `test` or `production` |
| `LOG_LEVEL` | Log verbosity |
| `DEMO_MODE` | Short SLA windows and demo behaviour |
| `DATABASE_URL` | PostgreSQL connection string |
| `POSTGRES_DB`, `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_PORT` | Local Compose database |
| `PORT` | Container listening port (default 7860 in the image) |
| `API_PORT` | Local Compose host port |
| `JWT_SECRET`, `JWT_EXPIRE_MINUTES` | Token signing and lifetime |
| `CORS_ORIGINS` | Comma-separated allowed frontend origins |
| `CLASSIFIER_BACKEND` | `baseline` (default) or `muril` |
| `MODEL_NAME_OR_PATH`, `HF_TOKEN` | MuRIL model path and optional Hub token |
| `CLASSIFIER_ACCEPT_THRESHOLD`, `CLASSIFIER_MARGIN_THRESHOLD`, `CLASSIFIER_MARGIN_MIN_CONFIDENCE` | Calibrated auto-accept and clarification policy |
| `TICKET_ID_PREFIX` | Public ticket ID prefix |
| `LLM_ENABLED`, `GEMINI_API_KEY`, `GEMINI_MODEL`, `LLM_TIMEOUT_SECONDS` | Optional location extraction and offline dataset generation |
| `DATASET_SEED`, `DATASET_TIER1_SAMPLES_PER_CLASS_LANGUAGE`, `DATASET_TIER2_SAMPLES_PER_CLASS_LANGUAGE`, `DATASET_MINIMUM_STRATUM_FRACTION` | Offline dataset generation |
| `ESCALATION_INTERVAL_SECONDS` | Scheduler cadence |
| `RATE_LIMIT_CHAT`, `RATE_LIMIT_STATUS` | Per-IP public limits (process-local) |
| `MAX_MESSAGE_LENGTH` | Chat input cap |
| `DEMO_OFFICER_USERNAME`, `DEMO_OFFICER_PASSWORD`, `DEMO_OFFICER_DEPARTMENT_CODE` | Seeded officer account |
| `DEMO_ADMIN_USERNAME`, `DEMO_ADMIN_PASSWORD` | Seeded administrator account |
| `VITE_API_BASE_URL` | Frontend build-time backend URL |

## Migrations

Apply migrations before serving or after pulling schema changes:

```bash
python -m alembic -c backend/alembic.ini upgrade head
```

The production entrypoint already runs this on container start. Never edit the
schema by hand or change a migration that has already been applied; add a new
revision instead.

## Seeding demo accounts

The container entrypoint runs `python -m grievance.seed` after migrations and
before Uvicorn. The seed is idempotent: it always creates or updates the nine
departments, and creates the officer/admin accounts only when `DEMO_MODE=true`
and all `DEMO_*` values are present. If demo configuration is incomplete or
`DEMO_MODE=false`, it logs a skip reason and still seeds the departments, so
startup does not fail. Passwords must be 12 to 72 UTF-8 bytes. Re-running
updates seeded fields and keeps existing hashes when the password is unchanged.
Passwords and other secret values are never logged. Demo credentials are
deliberately not published in the repository.

Check startup logs for `seed.completed departments=9 accounts=2` (or
`accounts=0` when demo accounts are disabled).

## Deploy the backend to Hugging Face Spaces

1. Create a **Docker** Space.
2. Push this repository to the Space, or connect the Space to the GitHub repo.
   The root `Dockerfile` and `backend/scripts/start.sh` are the entrypoint.
3. Add Space **secrets**: `DATABASE_URL` (for example a Neon connection string),
   `JWT_SECRET`, `DEMO_OFFICER_PASSWORD`, `DEMO_ADMIN_PASSWORD`, and
   `HF_TOKEN` only if a private Hub model is used.
4. Add Space **variables**: `APP_ENV=production`, `DEMO_MODE`, `CORS_ORIGINS`
   (the Vercel origin), `CLASSIFIER_BACKEND` (`baseline` or `muril`),
   `MODEL_NAME_OR_PATH` when using MuRIL, and `LLM_ENABLED=false` unless
   location extraction is configured.
5. Port handling: Spaces sets `PORT` and expects the app on that port. The
   image defaults to `PORT=7860` and passes it to Uvicorn. Do not hardcode 8000
   in the Space.
6. The entrypoint applies migrations and runs the idempotent seed before
   serving. Check the startup logs for `seed.completed departments=9`; run
   `python -m grievance.seed` manually only to repair or refresh seeded data.
7. Check `GET /health` and `GET /ready` on the public Space URL, then send a
   chat message that should require a department clarification and confirm that
   localized department buttons appear.

## Deploy the frontend to Vercel

1. Import the repository in Vercel and set the project root to `frontend/`.
2. Build command `npm run build`, output directory `dist` (Vite default).
3. Add `VITE_API_BASE_URL` pointing to the backend origin. Vite bakes this in
   at build time, so redeploy after changing it.
4. Add the Vercel origin to the backend `CORS_ORIGINS`, for example
   `https://<project>.vercel.app`. Multiple origins are comma-separated.
5. Redeploy and check the citizen chat, status lookup and staff login.

## Waking a sleeping Space

Free Spaces sleep when idle. Before a demo, open the Space URL or call:

```bash
curl -s https://<space-subdomain>.hf.space/health
curl -s https://<space-subdomain>.hf.space/ready
```

The chat UI already retries `/ready` before the first message. A cold start can
take tens of seconds, especially if the MuRIL model is downloaded again. Wake
the Space a few minutes before judging.

## Rotating secrets

- **JWT secret:** generate a new random value, update `JWT_SECRET` in the Space
  secrets (and locally), and redeploy. All existing tokens become invalid and
  users must log in again.
- **Database password:** change it in the database provider, then update
  `DATABASE_URL` (and the local `POSTGRES_PASSWORD` if applicable) and
  redeploy. Verify `/ready` and staff login.
- **Demo passwords:** change `DEMO_OFFICER_PASSWORD` and/or
  `DEMO_ADMIN_PASSWORD`, then rerun `python -m grievance.seed` against the
  target database. Because the seed rehashes changed passwords, old tokens
  still expire normally but old passwords stop working immediately.
- Never paste a secret into a commit, issue, chat log or screenshot.

## DEMO_MODE

`DEMO_MODE=true` interprets department `sla_hours` as **minutes** instead of
hours, so escalation can be shown quickly in a demo. Since the startup seed
also uses it, demo officer/admin accounts are created only when it is `true`
and the `DEMO_*` values are complete. It does not change the department list,
classification, templates or authentication. Set it to `false` for normal SLA
behaviour and no demo-account seeding.

## Troubleshooting

### CORS errors in the browser

- The exact frontend origin (scheme, host and port, no trailing slash) must be
  in `CORS_ORIGINS`.
- After changing `CORS_ORIGINS`, restart or redeploy the backend.
- `http://localhost:5173` and `https://<project>.vercel.app` are different
  origins; list every origin you use.

### `no password supplied`

This is a PostgreSQL authentication error, usually from a missing or empty
`POSTGRES_PASSWORD` or a `DATABASE_URL` whose credentials do not match the
database. Check `.env` or the Space secrets and the connection string. Do not
print the value in logs or issues.

### Space cold start or `503` readiness

- A sleeping Space returns timeouts or HTTP 503 until the container starts.
- Check `/ready`: `model=unavailable` means classifier initialization failed.
  For the MuRIL backend, confirm `MODEL_NAME_OR_PATH` and, if required,
  `HF_TOKEN`.
- The production image fits the baseline from `ml/data/processed/train.csv`
  during the build and loads `ml/artifacts/baseline.joblib` at startup. Confirm
  both files exist with
  `docker compose exec -T api ls -l /app/ml/data/processed/train.csv /app/ml/artifacts/baseline.joblib`.
  Startup logs should show `classifier.baseline.loaded source=artifact`. A
  `source=csv` line means the artifact was absent and the loader fitted from the
  CSV; rebuild the image to regenerate it.

### Clarification shows no department buttons or `water` repeats the question

- Confirm the API startup logs include `seed.completed departments=9`. If the
  departments table is empty, the seed did not run or the API points at a
  different database.
- Department buttons are generated from the seed registry, not from the request
  language, so a non-empty locale list should always return nine labels.
- A free-text reply such as `water`, `paani`, `पानी` or `પાણી` is matched
  against department codes, names and aliases. If it still repeats, check the
  API logs for the classifier label and confidence, and confirm the configured
  `CLASSIFIER_ACCEPT_THRESHOLD`, `CLASSIFIER_MARGIN_THRESHOLD` and
  `CLASSIFIER_MARGIN_MIN_CONFIDENCE` values.
- `seed.demo_accounts.skipped` lists the missing setting names, never their
  values. Staff login requires `DEMO_MODE=true` plus a complete `DEMO_*` set.

### Status lookup returns 404 for a new ticket

- Confirm the ticket ID is uppercase and complete.
- Confirm the API and the database you seeded are the same deployment.
- Public lookups return only public fields; this is expected.

### Load test shows HTTP 429

The defaults (`RATE_LIMIT_CHAT=10/minute`, `RATE_LIMIT_STATUS=30/minute`) are
per client IP and process-local. Raise them only for a load-test environment;
see `loadtests/README.md`.

## Related docs

- `docs/API.md` for endpoint contracts.
- `docs/ARCHITECTURE.md` for components and data flow.
- `docs/SCALING.md` for measured performance and design-only scale-out ideas.
