# Changelog

All notable changes to this project will be documented in this file.

## [Unreleased]

### Added
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
- Chat now detects the language of each incoming message and uses it for the reply, rather than retaining a stale language from an earlier turn.
- Recorded the Tier 1 dataset review results and removed the 25 specified bad rows from training data; remaining dataset rows are unreviewed.
- Gemini dataset generation now retries transport and timeout failures with exponential backoff, exits cleanly with resume guidance when retries are exhausted, and replays cached batches without delay; the configurable per-request timeout defaults to 60 seconds.
- Fixed Hindi combining-mark tokenization that falsely rejected adjacent words; cached raw batches are revalidated on every run, drop reasons are logged per stratum, and an environment-configured minimum stratum yield of 90% allows and reports small shortfalls.
- Tightened Gemini dataset prompts and validation for TAX-only billing complaints, English/Hinglish purity, native-script proportions, fictional Indian-style locations, and varied openings.
- Dataset generation now requires `GEMINI_API_KEY` and `GEMINI_MODEL`; defaults are 100 samples per Tier 1 department/language and 30 per Tier 2, with LLM provenance in CSV output.
- Documentation: added tiered multilingual scope (Tier 1 verified: English, Hindi, Gujarati, Hinglish; Tier 2 experimental: Marathi, Bengali, Tamil, Telugu, Kannada, Malayalam, Punjabi) across the PRD, architecture, tasks, agent rules, design guide and decisions log.