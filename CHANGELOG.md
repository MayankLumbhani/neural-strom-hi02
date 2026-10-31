# Changelog

All notable changes to this project will be documented in this file.

## [Unreleased]

### Added
- Backend package layout, FastAPI application factory, and initial app test.
- Python project tooling, Make targets, pre-commit hooks, and environment example.
- Dockerfile and Docker Compose services for the API and PostgreSQL.
- Backend local setup instructions.
- Liveness and readiness endpoints, plus GitHub Actions backend CI.
- Validated environment settings, request-ID middleware, JSON request logs, and
  consistent API error responses.
- SQLModel tables, initial Alembic migration, and request-scoped database sessions.
- Idempotent synthetic seed data for nine multilingual departments and environment-configured demo accounts with bcrypt password hashes.

### Changed
- Documentation: added tiered multilingual scope (Tier 1 verified: English, Hindi, Gujarati, Hinglish; Tier 2 experimental: Marathi, Bengali, Tamil, Telugu, Kannada, Malayalam, Punjabi) across the PRD, architecture, tasks, agent rules, design guide and decisions log.