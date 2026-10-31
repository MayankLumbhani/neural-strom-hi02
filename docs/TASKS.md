# Tasks

Ordered checklist for neural-storm-hi02. Work top to bottom. One task per IDE prompt, one commit per task (or per logical piece of it).

**Deadline:** submissions close Nov 4, 2026, 8:00 PM IST. Personal target: submit by 6:00 PM on Nov 4 at the latest.

## How to use this file

Universal prompt for the IDE (change only the task ID):

```
Read AGENTS.md fully, then docs/TASKS.md and docs/ARCHITECTURE.md.
Do task T-XX only. Follow the Workflow and Git sections of AGENTS.md:
run lint and tests, update the docs, commit to main, push, and stop.
```

Rules:
- Tick the box (`[x]`) only when the "Done when" line is true.
- If a task turns out too big, split it into T-XXa, T-XXb and say so here.
- Tasks marked **(human)** are done by you outside the IDE (Colab, deployment, recording). Tick them yourself.
- The agent updates this file as part of every task.

Language tiers used in this file:
- Tier 1 (verified): English, Hindi, Gujarati, Hinglish.
- Tier 2 (experimental): Marathi, Bengali, Tamil, Telugu, Kannada, Malayalam, Punjabi.

## Phase 0: Repository setup

- [x] **T-00** Repo initialized, `AGENTS.md`, `docs/PRD.md`, `docs/ARCHITECTURE.md` committed. City renamed to Furfuri Nagar (FMC).

## Phase 1: Backend foundation (target: Oct 30 to 31)

- [x] **T-01** Backend scaffold
  - Create the folder structure from AGENTS.md, `pyproject.toml`, FastAPI app factory, `Makefile` (dev, test, lint, format), `.env.example`, `.pre-commit-config.yaml`, `Dockerfile`, `docker-compose.yml` (api and postgres).
  - Done when: `make lint` and `make test` pass, and the app starts.
  - Commit: `chore(backend): scaffold backend structure and tooling`

- [ ] **T-02** Health endpoints and CI
  - `GET /health` and `GET /ready` (ready can report db and model as "unknown" until they exist), one test, GitHub Actions workflow running ruff, mypy and pytest.
  - Done when: CI is green on GitHub.
  - Commit: `ci: add health endpoints and GitHub Actions workflow`

- [ ] **T-03** Core: config, logging, errors
  - pydantic-settings config with every variable from ARCHITECTURE section 11, structured JSON logging with request ID middleware (no complaint text), domain exceptions mapped to the standard error JSON format.
  - Done when: tests cover error format and request ID header.
  - Commit: `feat(core): add settings, structured logging and error handling`

- [ ] **T-04** Database models and migrations
  - SQLModel tables from ARCHITECTURE section 8 (departments, officers, conversations, messages, tickets, ticket_events), indexes, first Alembic migration, DB session dependency.
  - Done when: `alembic upgrade head` works on the docker-compose Postgres and a repository test passes.
  - Commit: `feat(db): add models, indexes and initial migration`

- [ ] **T-05** Seed data
  - Script to seed the 9 departments (names in en, hi, gu and SLA hours) and demo officer and admin accounts (passwords from env, hashed). All synthetic.
  - Done when: `make seed` is idempotent (safe to run twice).
  - Commit: `feat(db): add idempotent seed script for departments and demo users`

- [ ] **T-06** Language registry, detection and templates
  - `nlp/languages.py` registry (code, names, script, tier, font, template file, verified flag), `nlp/language.py` (script detection for all registry scripts, Hindi vs Marathi disambiguation, Hinglish heuristic, unknown script falls back to a reply in English plus Hindi), `nlp/templates/` with Tier 1 templates (en, hi, gu, hinglish) and Tier 2 templates (mr, bn, ta, te, kn, ml, pa) flagged as machine-translated in a header comment, all with the keys from ARCHITECTURE 6.4.
  - Done when: unit tests cover every registry language and the unknown-script fallback, and a test asserts identical template keys across all language files.
  - Commit: `feat(nlp): add language registry, detection and multilingual message templates`

## Phase 2: ML pipeline (target: Oct 31 to Nov 1)

- [ ] **T-07** Synthetic dataset generator
  - `ml/src/generate_dataset.py`: generate complaints for 9 departments across all registry languages with variations (typos, slang, code-mixing, missing location, ambiguity): full size for Tier 1, smaller balanced sets for Tier 2. Save to `ml/data/processed/` with a train/validation split and a `tier` column. Document the generation prompt and settings in `docs/MODEL_CARD.md`.
  - Done when: datasets are roughly balanced and you have manually reviewed at least 50 rows per Tier 1 language. For each Tier 2 language, MODEL_CARD.md states whether a native speaker reviewed a sample or not.
  - Commit: `feat(ml): add synthetic dataset generator and splits`

- [ ] **T-08** Hand-written evaluation set **(human, with AI help for formatting)**
  - Write about 100 to 150 messages yourself (or with a friend) in the four Tier 1 languages, including ambiguous and messy ones. For each Tier 2 language, add about 20 messages drafted with LLM help. Save to `ml/data/eval_handwritten/eval.csv` with columns `text,label,language,verified`. Tier 1 rows are `verified=true`, Tier 2 rows are `verified=false` unless a native speaker checked them. Never train on it.
  - Done when: file exists with at least 100 Tier 1 rows, all 9 labels represented, and the `verified` column filled in.
  - Commit: `feat(ml): add hand-written evaluation set`

- [ ] **T-09** Baseline classifier and evaluation script
  - TF-IDF (char n-grams) plus Logistic Regression, `ml/src/evaluate.py` producing accuracy, per-class precision, recall, F1, macro-F1, per-language breakdown and a confusion matrix, saved to `ml/reports/`.
  - Done when: `make eval-baseline` writes `ml/reports/baseline_metrics.json`.
  - Commit: `feat(ml): add baseline classifier and evaluation script`

- [ ] **T-10** MuRIL fine-tuning **(human)**
  - Training script `ml/src/train_muril.py` plus `ml/notebooks/train_colab.ipynb`. Run it on Colab or Kaggle GPU, push the model to the Hugging Face Hub.
  - Done when: model is on the Hub and the model name is in `.env.example`.
  - Commit: `feat(ml): add MuRIL fine-tuning script and Colab notebook`

- [ ] **T-11** MuRIL evaluation report
  - Run `evaluate.py` for the MuRIL model on the evaluation set, write `ml/reports/muril_metrics.json` and the confusion matrix, and fill in `docs/MODEL_CARD.md` with the real numbers next to the baseline. Show a per-language table with the tier, Tier 1 and Tier 2 in separate tables, and label Tier 2 as unverified.
  - Done when: report files and model card are committed with real values only.
  - Commit: `docs(ml): add MuRIL evaluation results and model card`

- [ ] **T-12** Classifier interface and implementations
  - `Classifier` protocol, `Prediction` model, `BaselineClassifier`, `MurilClassifier`, a deterministic `FakeClassifier` for tests, factory chosen by `CLASSIFIER_BACKEND`, model loaded once at startup, `/ready` now reports model status.
  - Done when: unit tests pass using the fake, and a manual check loads the real model.
  - Commit: `feat(nlp): add classifier interface with baseline, MuRIL and fake implementations`

## Phase 3: Core features (target: Nov 1 to 2)

- [ ] **T-13** Ticket service
  - Repositories and `TicketService`: create ticket, public ID generator using `TICKET_ID_PREFIX` from config (default `FMC`) with collision retry, validated status transitions, ticket events.
  - Done when: unit tests cover every valid and invalid transition and ID format.
  - Commit: `feat(tickets): add ticket service with validated transitions and events`

- [ ] **T-14** Location extraction
  - `nlp/extraction.py`: LLM extraction with strict JSON schema and timeout, plus rule-based fallback in en, hi and gu (Tier 2 languages use the LLM path or ask the citizen), controlled by `LLM_ENABLED`.
  - Done when: tests cover the fallback without any network call.
  - Commit: `feat(nlp): add location extraction with rule-based fallback`

- [ ] **T-15** Chat service
  - Conversation state machine from ARCHITECTURE section 5: complaint, ask department (quick replies), ask location, create ticket, status lookup, greeting and help. Uses templates and the confidence policy from config.
  - Done when: integration tests pass for happy path, missing location, ambiguous complaint and status lookup (using `FakeClassifier`).
  - Commit: `feat(chat): add conversation state machine with clarification flow`

- [ ] **T-16** Public API
  - `POST /api/v1/chat/messages` and `GET /api/v1/tickets/{public_id}` with schemas, CORS from config, `docs/API.md` started.
  - Done when: API tests pass and the flow works in Swagger UI.
  - Commit: `feat(api): add chat and public ticket status endpoints`

- [ ] **T-17** Auth and officer endpoints
  - Login with JWT, role dependency, `/admin/tickets` (filters, pagination, department restriction enforced in the repository), ticket detail, `PATCH` status with note.
  - Done when: tests prove an officer cannot see or change another department's tickets.
  - Commit: `feat(admin): add authentication and officer ticket endpoints`

- [ ] **T-18** Escalation job
  - APScheduler job calling `EscalationService`, idempotent update, `DEMO_MODE` short SLAs.
  - Done when: a test creates an old ticket and proves it is escalated exactly once.
  - Commit: `feat(escalation): add scheduled SLA escalation job`

- [ ] **T-19** Analytics endpoint
  - `GET /admin/analytics/summary` with counts by department, status, language and average resolution time.
  - Done when: tests pass on seeded data.
  - Commit: `feat(admin): add analytics summary endpoint`

- [ ] **T-20** Rate limiting and hardening
  - Per-IP limits on public endpoints from config, input length limits, security headers.
  - Done when: a test shows the 429 response.
  - Commit: `feat(security): add rate limiting and input limits`

## Phase 4: Frontend (target: Nov 2 to 3)

- [ ] **T-21** Frontend scaffold
  - Vite, React, TypeScript, Tailwind, shadcn/ui, ESLint, routing, typed API client, `.env.example`, Noto Sans fonts for every registry script (Tier 2 fonts loaded on demand). CI also runs frontend lint and build.
  - Done when: `npm run lint` and `npm run build` pass.
  - Commit: `chore(frontend): scaffold React app with tooling`

- [ ] **T-21b** Design tokens and base components
  - Create `tokens.css` from DESIGN.md section 3, map it into Tailwind and remap the shadcn variables, load the fonts, build the base components from section 4 (Button, Input, Card, StatusBadge, ChatBubble, QuickReply, TicketCard, Table, Drawer, EmptyState, ErrorState, Skeleton), add a dev-only `/design` preview page showing every component with English, Hindi and Gujarati text, and add `check-design-tokens.sh` to CI.
  - Done when: the preview page renders correctly in all three scripts and the token check passes in CI.
  - Commit: `feat(frontend): add design tokens and base component library`

- [ ] **T-22** Chat UI
  - Chat window, message list, quick-reply buttons, ticket confirmation card, language-aware rendering, "waking up the server" state, error handling.
  - Done when: you can file a Gujarati, a Hinglish and an ambiguous complaint end to end locally.
  - Commit: `feat(frontend): add chat interface`

- [ ] **T-23** Status page
  - `/status` page with ticket ID input, status timeline and public notes.
  - Done when: lookup works for an existing and a missing ticket.
  - Commit: `feat(frontend): add ticket status page`

- [ ] **T-24** Login and officer dashboard
  - Login form, protected routes, ticket table with filters, detail drawer, status update with note.
  - Done when: an officer updates a ticket and the status page shows the change.
  - Commit: `feat(frontend): add officer login and ticket dashboard`

- [ ] **T-25** Admin analytics view
  - Charts (Recharts) for tickets per department, status breakdown, language mix, average resolution time, plus an escalated tickets list.
  - Done when: charts render from the analytics endpoint.
  - Commit: `feat(frontend): add admin analytics view`

- [ ] **T-26** UI translations
  - i18n for UI strings (buttons, labels, headings) in the Tier 1 languages English, Hindi and Gujarati with a language switcher. The chat itself already works in every registry language, and Tier 2 users see the English UI.
  - Done when: all visible UI text is translatable and the switcher works.
  - Commit: `feat(frontend): add UI internationalization`

## Phase 5: Deployment and performance (target: Nov 3)

- [ ] **T-27** Production Dockerfile
  - Backend image for Hugging Face Spaces (Docker SDK), non-root user, port from env, model loaded from the Hub at startup, Alembic migration on start.
  - Done when: image builds and runs locally against Neon or local Postgres.
  - Commit: `chore(deploy): add production Dockerfile for Hugging Face Spaces`

- [ ] **T-28** Deploy backend **(human)**
  - Create the Space, set secrets (`DATABASE_URL`, `JWT_SECRET`, keys), run migrations and seed, check `/ready`.
  - Done when: the public backend URL answers `/health` and `/ready`.

- [ ] **T-29** Deploy frontend **(human)**
  - Vercel project, set the backend URL env var, set `CORS_ORIGINS` on the backend.
  - Done when: the full citizen and officer flow works on the live URLs.
  - Commit (config notes only): `docs: record deployment URLs and setup`

- [ ] **T-30** Load test
  - k6 or Locust scripts in `loadtests/` for `/chat/messages` and `/tickets/{id}`. Run against one instance, save the raw results and a short summary.
  - Done when: requests per second and p95 latency are recorded from a real run (state the hardware and conditions honestly).
  - Commit: `test(load): add load test scripts and recorded results`

- [ ] **T-31** ONNX quantization (optional, skip if short on time)
  - Export and quantize MuRIL, compare accuracy and latency with PyTorch on the same set.
  - Done when: measured comparison is saved in `ml/reports/`. Only switch the deployed backend if accuracy holds.
  - Commit: `perf(ml): add ONNX export and latency comparison`

## Phase 6: Documentation and submission (target: Nov 3 to 4)

- [ ] **T-32** SCALING.md
  - Written from ARCHITECTURE section 14 plus the real load test numbers. Clearly separate measured results from design-only ideas.
  - Commit: `docs: add scaling notes with measured load test results`

- [ ] **T-33** API.md and RUNBOOK.md
  - Full endpoint examples; runbook for deploy, migrations, seeding, waking the Space, rotating secrets.
  - Commit: `docs: complete API reference and runbook`

- [ ] **T-34** README
  - All items required by the hackathon: title and problem statement number HI-02, team (solo) and name, problem and approach, tech stack, setup and local run steps, screenshots or demo GIF, real metrics from the reports (Tier 1 and Tier 2 in separate tables, Tier 2 labelled experimental), AI tools used (Qoder, Cursor, Antigravity, GitHub Copilot, Claude), live links, note that development started Oct 30 with organiser permission, CI badge.
  - Commit: `docs: write project README`

- [ ] **T-35** Screenshots and GIF **(human)**
  - Capture chat in three languages, ticket confirmation, status page, officer dashboard, analytics, escalation. Save to `docs/images/`.
  - Commit: `docs: add screenshots and demo gif`

- [ ] **T-36** Demo video script and recording **(human)**
  - Follow the demo plan in PRD section 11. Use `DEMO_MODE` so escalation is visible. Mention the stack and that AI tools built the code.
  - Done when: video is uploaded and the link is in the README.

- [ ] **T-37** Final check and release
  - Fresh clone test (follow the README on a clean folder), CI green, no secrets in history, live demo works, wake the Space. Tag `v1.0.0`.
  - Commit: `chore: prepare v1.0.0 release` then `git tag v1.0.0 && git push --tags`

- [ ] **T-38** Submit **(human)**
  - Submit from the Dashboard Submit tab: public GitHub repo link plus deployment link. Do it by 6:00 PM on Nov 4. Open the submission afterward to confirm it saved.

## Stretch (only after T-37)

- [ ] **S-01** Voice input via the browser Web Speech API
- [ ] **S-02** Telegram bot interface

## If time runs short: cut in this order

1. S-01, S-02
2. T-31 (ONNX)
3. T-26 (UI translations): keep English only plus the chat in all languages
4. T-25 (analytics charts): keep a simple summary table
5. T-20 (rate limiting): keep input limits only
6. Tier 2 languages: disable them in the registry and keep Tier 1 only

Never cut: T-09 to T-11 (real metrics), T-15 (clarification flow), T-18 (escalation), T-28 and T-29 (live demo), T-34 (README), T-36 (video).

## Log

Add one line per day: what was finished, what is blocked.

- 2026-10-30: repo, AGENTS.md, PRD and architecture committed.
- 2026-10-30: completed T-01 backend scaffold, tooling and local Docker setup.
- 2026-10-31: added tiered multilingual scope (Tier 1 verified, Tier 2 experimental) to the planning docs.
- 2026-10-31: implemented T-02 health endpoints and CI workflow; awaiting the first GitHub Actions run.