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

The API provides `GET /health` for liveness and `GET /ready` for readiness.
The configured classifier loads once at startup; readiness reports
`model=ready` or returns HTTP 503 with `model=unavailable` and an initialization
error. Database readiness remains `unknown`. GitHub Actions runs Ruff, mypy,
and pytest on pushes to `main` and pull requests targeting `main`; application
features are tracked in [docs/TASKS.md](docs/TASKS.md).

## Language support

The backend registry detects English, Hindi, Gujarati, and romanized Hindi
(Hinglish), plus experimental Marathi, Bengali, Tamil, Telugu, Kannada,
Malayalam, and Punjabi. Unsupported or ambiguous scripts use English and Hindi
fallback reply languages. Tier 1 templates are hand-written; Tier 2 templates
are machine-translated and have not been verified by native speakers.

## Synthetic training data

After installing the project dependencies, set `GEMINI_API_KEY` and
`GEMINI_MODEL` in `.env` (replace the example placeholders), then run
`python -m ml.src.generate_dataset --check` to verify access. Run
`make generate-dataset` for a full generation or add `--limit N` to the Python
command for a small trial. The generator uses the official Google Gen AI
Python SDK; its model name is required and has no hardcoded default. Defaults
are 100 examples per department/language for Tier 1 and 30 for Tier 2, with
the seed and sizes configurable through the dataset settings in `.env`.
Generated CSVs and raw response batches are not committed; review requirements
and generation details are in
[docs/MODEL_CARD.md](docs/MODEL_CARD.md).

After generating the processed splits, run
`python -m ml.src.relabel_drainage` to apply the deterministic D-10 drainage
label normalization to train and validation data. The command creates
timestamped backups under `ml/data/processed/backup/` and a local audit at
`ml/data/review/relabel_changes.csv`; it leaves the evaluation set unchanged.

After generating the training split, run `make review-sample` to create a
seeded sample of 50 rows per Tier 1 language at
`ml/data/review/review_sample.csv`. Fill in the `verdict` and `notes` columns
during human review; the sample file is ignored by Git.

The Tier 1 evaluation set contains 100 short, parallel rows written by Claude
(an AI), not humans; accuracy measured on it is an optimistic estimate. Tier 2
evaluation set: 70 rows (10 per language for mr, bn, ta, te, kn, ml, pa),
written by Claude (an AI), NOT verified by native speakers, verified=false.
This is below the ~20 per language target in the task plan. Tier 2 metrics are
experimental and must always be reported separately from Tier 1. See
[docs/MODEL_CARD.md](docs/MODEL_CARD.md) for limitations.

After generating the training split, run `make eval-baseline` to train the
character n-gram TF-IDF plus Logistic Regression baseline. It reads
`ml/data/processed/train.csv` for training, evaluates only against the separate
evaluation set, and writes metrics and a confusion matrix to
`ml/reports/baseline_metrics.json`. The command does not generate or modify
either dataset.

## MuRIL fine-tuning

Install the training dependencies with
`python -m pip install -e ".[training]"`. The script trains from the ignored
`ml/data/processed/train.csv`, selects by validation macro-F1 using
`validation.csv`, evaluates the best checkpoint on the separate evaluation
set, and writes model files and metrics under `ml/artifacts/`. Defaults are
max length 128, 4 epochs, learning rate `3e-5`, batch size 32, and seed 42;
each can be overridden with a command-line option. The ordered Colab workflow,
including upload of ignored training files, is in
[ml/notebooks/train_colab.ipynb](ml/notebooks/train_colab.ipynb). The optional
fine-tuned MuRIL backend is published as
`MayankLumbhani/hi02-muril-grievance`, configured by `MODEL_NAME_OR_PATH` and
selected with `CLASSIFIER_BACKEND=muril`. The default backend is the TF-IDF
baseline. See [docs/MODEL_CARD.md](docs/MODEL_CARD.md) for the measured
results and limitations.

## AI tools

- GitHub Copilot was used for AI-assisted development.
- The optional offline training-data generator uses the Google Gemini API
  through the official Google Gen AI Python SDK. Generated examples are
  synthetic and require human review.