# AGENTS.md

Instructions for AI coding agents (Qoder, Cursor, Antigravity, or any other).
Read this file fully before every task. If a request conflicts with this file, say so before acting.

## Project

**neural-storm-hi02**: Multilingual Citizen Grievance Chatbot (Neural Storm 2026, problem statement HI-02).

Citizens file complaints in Gujarati, Hindi, Hinglish or English. The system detects the language, classifies the complaint into a municipal department, asks a clarifying question when unsure, creates a ticket, tracks its status and auto-escalates stale tickets. Department officers use a dashboard to update tickets and view analytics.

Solo project built with AI assistance. Hackathon rules apply: Python is the primary language for AI/ML parts, and the README must list the AI tools used.

## Scope

- Languages: Gujarati, Hindi, Hinglish (romanized Hindi), English
- Departments (9): Water Supply, Roads, Sanitation and Waste, Electricity, Street Lights, Drainage and Sewage, Public Health, Property Tax and Billing, Other
- Ticket statuses: Filed, Assigned, In Progress, Resolved, Escalated
- Stretch goals (only after the core is done): voice input, Telegram interface

Anything outside this scope needs an entry in `docs/DECISIONS.md` before it is built.

## Stack

- Backend: Python 3.11, FastAPI, SQLModel, PostgreSQL, Alembic, APScheduler
- ML: PyTorch, Hugging Face Transformers (MuRIL fine-tune), scikit-learn TF-IDF + Logistic Regression baseline, ONNX for inference optimization
- Frontend: React, Vite, TypeScript, Tailwind CSS, shadcn/ui, Recharts
- Tooling: ruff, mypy, pytest, pre-commit, Docker, docker-compose, GitHub Actions
- Deploy: Hugging Face Spaces (backend and model), Vercel (frontend), Neon (Postgres)

Do not introduce libraries outside this stack without an entry in `docs/DECISIONS.md`.

## Repository layout

```
backend/src/grievance/
  core/          config, logging, security, exceptions
  api/v1/        routers only
  schemas/       Pydantic request/response models
  models/        SQLModel tables
  repositories/  all database access
  services/      business logic
  nlp/           language detection, Classifier interface, extraction, templates
  jobs/          scheduled jobs (escalation)
backend/tests/{unit,integration}/
ml/              data, training, evaluation, reports
frontend/src/    features/, components/ui/, lib/, pages/
loadtests/       k6 or Locust scripts and results
docs/            PRD, ARCHITECTURE, DECISIONS, TASKS, MODEL_CARD, API, RUNBOOK, SCALING
```

## Architecture rules (never break these)

1. **Layering:** router -> service -> repository. Routers contain no business logic and no DB queries. Services never import FastAPI. Only repositories touch the database.
2. The classifier is used only through the `Classifier` interface in `nlp/`, so the MuRIL model, the baseline and an ONNX model are swappable.
3. All configuration comes from environment variables via pydantic-settings. No hardcoded secrets, URLs, thresholds or magic numbers. Every variable is listed in `.env.example`.
4. Every function has type hints. Every public function and class has a short docstring.
5. Fixed user-facing messages (confirmations, status labels, errors) come from per-language template files. Never generate them with an LLM. An LLM may be used only for dataset generation, detail extraction and clarifying questions.
6. The API is stateless. No in-process session state or local-disk persistence. Persistent data lives in Postgres.
7. Every endpoint validates input with Pydantic schemas and returns typed responses. Errors use a consistent error schema and proper HTTP status codes.
8. When classifier confidence is below the configured threshold, ask a clarifying question instead of guessing.
9. Database changes go through Alembic migrations only. Never edit the schema by hand.

## Code quality rules

- Small functions with a single responsibility. No duplicated logic.
- No dead code, no commented-out code, no `print` statements. Use the structured logger.
- Meaningful names. Constants in one place. Follow the ruff and mypy configuration without disabling rules inline unless justified in a comment.
- Handle errors explicitly. No bare `except`. Do not swallow exceptions silently.
- Never log personal data from complaints (phone numbers, addresses). Mask or omit it.
- Frontend: strict TypeScript, no `any`, feature-based folders, accessible components (labels, contrast, keyboard use), all UI text goes through the i18n layer.

## Quality gates (must pass before every commit)

- `make lint` is clean (ruff and mypy; ESLint and tsc for the frontend)
- `make test` passes, and new logic has tests
- The app starts without errors
- No secrets, datasets, model weights or caches in the staged files

If a gate fails, fix it. Do not skip, weaken or delete tests to make a task pass.

## Frontend design rules
- Read docs/DESIGN.md before every UI task and follow it exactly.
- All visual values come from frontend/src/styles/tokens.css. Never hardcode
  hex colors, pixel sizes, arbitrary Tailwind values or default palette classes.
- Use only the semantic token classes and the base components in components/ui/.
- No emoji as icons. No gradients or styles from the "Do not do" list.
- Test every UI change with Gujarati and Hindi text, not just English.

## Documentation rule

After every meaningful change, update docs in the same task:

- `docs/TASKS.md`: mark status, add follow-ups discovered
- `CHANGELOG.md`: what changed (Keep a Changelog format, newest first)
- `docs/ARCHITECTURE.md`: if structure, data flow or schema changed
- `docs/DECISIONS.md`: if a technology or design choice was made (what, why, alternatives)
- `docs/API.md`: if an endpoint changed
- `docs/MODEL_CARD.md`: if the dataset, model or metrics changed
- `README.md`: if setup, usage or features changed

Docs describe what actually exists. Never document planned work as done.

## Workflow for every task

1. Read `docs/TASKS.md` and `docs/ARCHITECTURE.md` first.
2. State a short plan, then implement only what the task asks.
3. Run `make lint` and `make test`; fix failures until both pass.
4. Update docs per the documentation rule.
5. Commit directly to `main` with a Conventional Commit message, push, then stop.

Do one task per prompt. If a task is too large, split it and say how.

## Git

- Work and commit only on `main`. Never create branches.
- One logical change per commit. Never bundle unrelated changes.
- Commit only when lint and tests pass. Never commit a broken build.
- Message format: `type(scope): short imperative summary`
  - types: feat, fix, docs, test, refactor, chore, ci, perf
  - example: `feat(nlp): add script-based language detection`
- Stage files explicitly with `git add <paths>`, never a blind `git add .`. Check `git status` first.
- Never force-push, rewrite history, or amend commits that are already pushed.
- Push to `origin main` after each commit.
- If CI fails after a push, fixing it is the next task.

## Security

- Secrets only in `.env` (git-ignored). Never commit them. Never print them.
- Rate limit public endpoints. Validate and size-limit all input.
- Admin endpoints require authentication and role checks.
- Use synthetic data only. No real citizen data anywhere in the repo.

## ML rules

- Training data is synthetic, so keep a separate hand-written evaluation set in `ml/data/eval_handwritten/` and never train on it.
- Report accuracy, per-class precision/recall/F1 and a confusion matrix for both the baseline and the MuRIL model on that hand-written set.
- Metrics files are generated by scripts in `ml/` and committed as reports. Never write numbers by hand.
- Model weights are not committed. They live on the Hugging Face Hub and are loaded by name via config.

## Never

- Never invent metrics, results, benchmarks, screenshots or user statistics.
- Never claim something is implemented, tested or deployed when it is not.
- Never refactor unrelated code during a task.
- Never add features beyond the current task.
- Never commit `.env`, keys, datasets or model weights.
- Never skip or weaken tests to make a task pass.