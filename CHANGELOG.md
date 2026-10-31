# Changelog

All notable changes to this project will be documented in this file.

## [Unreleased]

### Added
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
- Dataset generation now requires `GEMINI_API_KEY` and `GEMINI_MODEL`; defaults are 100 samples per Tier 1 department/language and 30 per Tier 2, with LLM provenance in CSV output.
- Documentation: added tiered multilingual scope (Tier 1 verified: English, Hindi, Gujarati, Hinglish; Tier 2 experimental: Marathi, Bengali, Tamil, Telugu, Kannada, Malayalam, Punjabi) across the PRD, architecture, tasks, agent rules, design guide and decisions log.