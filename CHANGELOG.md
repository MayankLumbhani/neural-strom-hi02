# Changelog

All notable changes to this project will be documented in this file.

## [Unreleased]

### Fixed
- Run the idempotent seed automatically from `backend/scripts/start.sh` after Alembic migrations. Departments are always seeded; demo officer/admin accounts are seeded only when `DEMO_MODE=true` and all `DEMO_*` values are present. Incomplete demo configuration logs missing setting names (never values) and skips accounts without blocking startup. On a fresh Compose database the logs showed `seed.completed departments=9 accounts=2`, and department/officer counts were 9 and 2.
- Clarification replies now always include all nine localized department buttons from the seed registry, so an empty or unseeded database cannot produce a question with no choices. Repeated failed clarifications keep the buttons instead of silently routing to `OTHER`, and free-text replies resolve department codes, localized names and aliases such as `water`, `paani`, `पानी` and `પાણી`.
- Recalibrated the chat acceptance rule from validation data. The old `0.75/0.45` policy accepted only 3 of 720 validation Tier 1 rows (0.42% coverage). The new `CLASSIFIER_ACCEPT_THRESHOLD=0.35`, `CLASSIFIER_MARGIN_THRESHOLD=0.12`, `CLASSIFIER_MARGIN_MIN_CONFIDENCE=0.25` rule accepted 466 of 720 (64.7% coverage) at 89.3% precision (416 correct, 50 incorrect); the held-out 100-row Tier 1 evaluation accepted 77 (77.0%) with all 77 correct. The evaluation set is small and AI-authored, so this is an observed tradeoff, not a general claim.
- Verified the complete flow from a fresh Compose database without manual seeding: 12 eval-derived complaints (3 each in English, Hindi, Gujarati and Hinglish) produced 5 direct tickets, 3 department clarifications with nine choices, and 4 location follow-ups, all ending in tickets. A repeated clarification kept nine buttons twice, then `water` created a ticket. Officer and admin logins both returned 200. The API used 223.1 MiB and was not OOM-killed.
- Fit the baseline classifier once during the Docker image build and load the resulting joblib artifact at startup instead of fitting on every start, with a CSV-fit fallback for local development and tests; run Uvicorn with one worker. Under a 512 MB container limit the API peaked at 284,132 kB VmRSS after English/Hindi/Gujarati chat flows, was not OOM-killed, and did not import PyTorch, Transformers or SentencePiece on the baseline path.
- Ship the committed synthetic baseline training split (`ml/data/processed/train.csv`) in the Docker image so the default baseline classifier initializes on Render instead of failing with `Baseline training CSV not found`; updated Compose to use the image copy rather than a host bind mount.

### Added
- Added `ml/src/calibrate.py`, the `make calibrate-baseline` target and the generated `ml/reports/confidence_calibration.json`, which compares candidate accept/margin rules on validation and the handwritten evaluation set; recorded the chosen rule in D-17.
- Rewrote `README.md` with the problem, architecture, features, setup, measured Tier 1 and Tier 2 metrics, load-test summary, limitations, AI tools, early-start disclosure, documentation links and marked placeholders; completed T-34.
- Rewrote `docs/API.md` with every implemented endpoint, auth requirements, JSON examples and curl calls, and added `docs/RUNBOOK.md` for local runs, deployment, secret rotation and troubleshooting; completed T-33.
- Added `docs/SCALING.md` with the measured local load test and a clearly separated list of design-only scale-out ideas; completed T-32.
- Added the Locust load test script, a load-test-only rate-limit override, exact run instructions, and recorded 60-second/20-user results under `loadtests/`; completed T-30.
- Added the Hugging Face Spaces production Docker image with non-root execution, configurable port, pre-start Alembic migrations, and CPU MuRIL runtime dependencies; updated local Compose and setup instructions.
- Completed T-26 with English/Hindi/Gujarati UI translations and a shared, accessible language switcher across citizen, status, staff, officer, and analytics screens; unsupported browser locales continue to use English.
- Added the admin-only `/analytics` view with ticket summary cards, token-colored Recharts breakdowns, accessible chart data tables, an escalated ticket queue, and English/Hindi/Gujarati copy.
- Added the English/Hindi/Gujarati staff login and protected officer dashboard with department-scoped status, text, and inclusive date filters, ticket history, and public/internal status updates; verified that public updates appear in the citizen status API.
- Added the localized `/status` ticket lookup page with ticket details, public status timeline, and a friendly missing-ticket state; public status responses now identify ticket language and canonical status.
- Added the multilingual citizen chat UI with API-backed conversation handling, quick-reply clarification, readiness retries, tier-aware replies, and ticket confirmation; chat responses now include language tier metadata.
- Added the token-backed civic design system, accessible base components, development-only multilingual `/design` preview, and CI token enforcement; updated border tokens to meet UI contrast guidance and completed T-21b.
- Added the React/Vite/TypeScript/Tailwind frontend scaffold, routing, typed API client, script-aware font loading, ESLint, and frontend CI checks; completed T-21.
- Added configurable per-IP sliding-window limits for public chat/status routes, standard 429 responses, and browser security headers; documented the process-local quota scope in D-15 and completed T-20.
- Added authenticated `/api/v1/admin/analytics/summary` with department-, status-, and language-based counts and scoped average resolution time; completed T-19.
- Added an APScheduler SLA escalation job with demo-mode minute windows, atomic idempotent ticket updates, transactional system events, and lifecycle-managed startup/shutdown; completed T-18.
- Added officer/admin login with expiring HS256 bearer tokens and department-scoped ticket listing, details, and status updates; completed T-17.
- Added `POST /api/v1/chat/messages` and `GET /api/v1/tickets/{public_id}`, typed public responses, configured CORS, API documentation, and HTTP integration tests; completed T-16.
- Added persisted chat orchestration for complaints, department clarification, location follow-up, greetings/help, and ticket status lookup; completed T-15.
- Added Gemini-backed strict JSON location extraction with a configured timeout, offline English/Hindi/Gujarati fallback rules, and tests using a fake client; completed T-14.
- Added the ticket repository and service with configurable collision-retried public IDs, ticket events, and validated lifecycle transitions; completed T-13.
- Added the classifier protocol, validated prediction model, TF-IDF and MuRIL backends, deterministic fake, startup factory, and classifier-aware readiness reporting.
- Published the existing MuRIL evaluation metrics and overall confusion matrix under `ml/reports/`, documented tiered/per-language results, and completed T-11.
- Recorded D-14: use the TF-IDF baseline as the default classifier backend and keep the published MuRIL model optional.
- Recorded fine-tuned MuRIL evaluation metrics and baseline comparison, configured the published Hub model, and completed T-10; documented the HEALTH recall limitation.
- Added deterministic drainage-label normalization with disease-keyword exclusions, timestamped dataset backups, an ignored change audit, and offline rule tests.
- Added the MuRIL fine-tuning script and ordered Colab notebook with offline data and metrics tests; the model has since been trained and published, with results recorded in the model card.
- Added a TF-IDF character n-gram plus Logistic Regression baseline evaluator and `make eval-baseline`; its generated report separates Tier 1 and Tier 2 metrics.
- Added 70 Claude-authored, unverified Tier 2 evaluation rows (10 per language) and completed T-08; documentation records that Tier 2 results are experimental and reported separately.
- Added a 100-row Tier 1 evaluation set, with its AI-written provenance and optimistic-estimate limitations documented; Tier 2 evaluation rows remain pending.
- Gemini-backed synthetic complaint generation with strict output validation, cached batches, seeded stratified splits, and offline fake-client tests.
- Backend package layout, FastAPI application factory, and initial app test.
- Python project tooling, Make targets, pre-commit hooks, and environment example.
- Dockerfile and Docker Compose services for the API and PostgreSQL.
- Backend local setup instructions.
- Liveness and readiness endpoints, plus GitHub Actions backend CI.
- Validated environment settings, request-ID middleware, JSON request logs, and
  consistent API error responses.
- SQLModel tables, initial Alembic migration, and request-scoped database sessions.
- Idempotent synthetic seed data for nine multilingual departments and environment-configured demo accounts with bcrypt password hashes.
- Registry-driven language detection for all supported scripts, typed TOML reply templates for all 11 languages, and tests for fallback behavior and template parity.
- Deterministic synthetic complaint dataset generator with stratified train/validation splits, tier metadata, and documented review status.
- Seeded Tier 1 training-data review sample generator with blank verdict and notes columns.

### Changed
- Replaced `CLASSIFIER_HIGH_THRESHOLD` and `CLASSIFIER_LOW_THRESHOLD` with `CLASSIFIER_ACCEPT_THRESHOLD` (0.35), `CLASSIFIER_MARGIN_THRESHOLD` (0.12) and `CLASSIFIER_MARGIN_MIN_CONFIDENCE` (0.25); settings validation rejects a margin floor at or above the accept threshold. Updated `.env.example`, tests and docs.
- Request-scoped database sessions now commit on success and roll back on error, so conversations and tickets created in one request are visible to later requests; added unit coverage.
- Chat now detects the language of each incoming message and uses it for the reply, rather than retaining a stale language from an earlier turn.
- Recorded the Tier 1 dataset review results and removed the 25 specified bad rows from training data; remaining dataset rows are unreviewed.
- Gemini dataset generation now retries transport and timeout failures with exponential backoff, exits cleanly with resume guidance when retries are exhausted, and replays cached batches without delay; the configurable per-request timeout defaults to 60 seconds.
- Fixed Hindi combining-mark tokenization that falsely rejected adjacent words; cached raw batches are revalidated on every run, drop reasons are logged per stratum, and an environment-configured minimum stratum yield of 90% allows and reports small shortfalls.
- Tightened Gemini dataset prompts and validation for TAX-only billing complaints, English/Hinglish purity, native-script proportions, fictional Indian-style locations, and varied openings.
- Dataset generation now requires `GEMINI_API_KEY` and `GEMINI_MODEL`; defaults are 100 samples per Tier 1 department/language and 30 per Tier 2, with LLM provenance in CSV output.
- Documentation: added tiered multilingual scope (Tier 1 verified: English, Hindi, Gujarati, Hinglish; Tier 2 experimental: Marathi, Bengali, Tamil, Telugu, Kannada, Malayalam, Punjabi) across the PRD, architecture, tasks, agent rules, design guide and decisions log.