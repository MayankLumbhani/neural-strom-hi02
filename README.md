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

Run `make lint` and `make test` to check the backend. `make format` applies
Ruff formatting.

The API currently provides `GET /health` for liveness and `GET /ready` for
readiness. Database and model readiness are reported as `unknown` until those
components are implemented. GitHub Actions runs Ruff, mypy, and pytest on pushes
to `main` and pull requests targeting `main`; application features are tracked
in [docs/TASKS.md](docs/TASKS.md).