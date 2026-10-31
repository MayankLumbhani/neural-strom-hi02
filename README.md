# Neural Storm HI-02

Multilingual citizen grievance chatbot for Furfuri Nagar. The backend scaffold
uses FastAPI and is organized to support the service and repository layers
described in [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md).

## Backend quick start

Requirements: Python 3.11 or newer; Docker Compose is optional for PostgreSQL.

1. Create and activate a virtual environment in PowerShell:

   ```powershell
   python -m venv .venv
   .\.venv\Scripts\Activate.ps1
   ```

2. Install the development tools and backend dependencies:

   ```powershell
   python -m pip install -e ".[dev]"
   ```

3. Copy `.env.example` to `.env`. Set a local PostgreSQL password in `.env`
   before starting Docker Compose.
4. Start the API and PostgreSQL with `docker compose up --build`, or start the
   API locally with `make dev` after PostgreSQL is available.
5. Apply database migrations with `make migrate`. Compose PostgreSQL is exposed
   on `POSTGRES_PORT` (5432 by default); the example `DATABASE_URL` credentials
   match the example PostgreSQL user and password.
6. Set `DEMO_OFFICER_USERNAME`, `DEMO_OFFICER_PASSWORD`, `DEMO_ADMIN_USERNAME`,
   and `DEMO_ADMIN_PASSWORD` in `.env`. Use passwords between 12 and 72 UTF-8
   bytes, then run `make seed` to create the synthetic departments and demo
   accounts. Running the seed command again is safe.

Run `make lint` and `make test` to check the backend. `make format` applies
Ruff formatting.

Application settings are loaded from `.env` through `pydantic-settings`; the
supported variables and local examples are listed in `.env.example`. API
responses include an `X-Request-ID` for correlation. Request logs are JSON and
include request metadata only, never request bodies.

The API currently provides `GET /health` for liveness and `GET /ready` for
readiness. Database and model readiness are reported as `unknown` until those
components are implemented. GitHub Actions runs Ruff, mypy, and pytest on pushes
to `main` and pull requests targeting `main`; application features are tracked
in [docs/TASKS.md](docs/TASKS.md).

## Language support

The backend registry detects English, Hindi, Gujarati, and romanized Hindi
(Hinglish), plus experimental Marathi, Bengali, Tamil, Telugu, Kannada,
Malayalam, and Punjabi. Unsupported or ambiguous scripts use English and Hindi
fallback reply languages. Tier 1 templates are hand-written; Tier 2 templates
are machine-translated and have not been verified by native speakers.

## Synthetic training data

After installing the project dependencies, run `make generate-dataset` to
create deterministic synthetic training and validation CSVs in
`ml/data/processed/`. The generator is configurable with a fixed seed and
keeps Tier 2 smaller and explicitly unverified. Generated datasets are not
committed; review requirements and generation details are in
[docs/MODEL_CARD.md](docs/MODEL_CARD.md).