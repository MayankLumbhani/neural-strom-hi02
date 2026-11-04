# API reference

Everything below is implemented in the FastAPI application. The versioned
routes live under `/api/v1`; health and readiness are unversioned. All
responses include an `X-Request-ID` header.

Quick start for the local stack:

```bash
export BASE_URL=http://localhost:8000
curl -s "$BASE_URL/ready"
```

## Endpoint summary

| Method | Path | Auth | Purpose |
|---|---|---|---|
| `GET` | `/health` | None | Liveness |
| `GET` | `/ready` | None | Classifier readiness |
| `POST` | `/api/v1/chat/messages` | None | Send a citizen message |
| `GET` | `/api/v1/tickets/{public_id}` | None | Public ticket status |
| `POST` | `/api/v1/auth/login` | None | Officer or admin login |
| `GET` | `/api/v1/admin/tickets` | Bearer token | Scoped ticket queue |
| `GET` | `/api/v1/admin/tickets/{public_id}` | Bearer token | Scoped ticket detail |
| `PATCH` | `/api/v1/admin/tickets/{public_id}/status` | Bearer token | Update ticket status |
| `GET` | `/api/v1/admin/analytics/summary` | Bearer token | Scoped analytics |

There is no `/api/v1/admin/departments` route in the current application.

## Health

### `GET /health`

Liveness only. No authentication.

```bash
curl -s "$BASE_URL/health"
```

```json
{ "status": "ok" }
```

### `GET /ready`

Reports whether the classifier finished loading. Database readiness is not
probed and is reported as `"unknown"`. No authentication.

Success, HTTP 200:

```bash
curl -s "$BASE_URL/ready"
```

```json
{
  "status": "ready",
  "db": "unknown",
  "model": "ready",
  "model_error": null
}
```

Failure, HTTP 503:

```json
{
  "status": "not_ready",
  "db": "unknown",
  "model": "unavailable",
  "model_error": "MODEL_NAME_OR_PATH must be configured for the MuRIL backend"
}
```

## Chat

### `POST /api/v1/chat/messages`

Sends one citizen message. No authentication. Public requests are rate-limited
per client IP by `RATE_LIMIT_CHAT`; exceeding the limit returns HTTP 429 with a
`Retry-After` header. The reply language is detected from the message text, not
from `Accept-Language`.

Request:

```json
{
  "text": "There is no water supply in Shivaji Nagar since yesterday.",
  "conversation_id": null
}
```

- `text` is required, non-empty and limited by `MAX_MESSAGE_LENGTH`.
- `conversation_id` is omitted or `null` for the first message and sent on
  every follow-up.
- Unknown request fields are rejected with HTTP 422.

First response, HTTP 200 (clarification requested):

```json
{
  "conversation_id": "8a7b62f0-6eef-44f5-8d59-8134c1ffac37",
  "state": "AWAITING_DEPARTMENT",
  "language": "en",
  "language_tier": 1,
  "reply": {
    "text": "Which department should handle this complaint? Please choose or clarify.",
    "quick_replies": ["Water Supply", "Public Health"]
  },
  "ticket": null
}
```

Follow-up request:

```json
{
  "text": "Water Supply",
  "conversation_id": "8a7b62f0-6eef-44f5-8d59-8134c1ffac37"
}
```

Ticket created, HTTP 200:

```json
{
  "conversation_id": "8a7b62f0-6eef-44f5-8d59-8134c1ffac37",
  "state": "TICKET_CREATED",
  "language": "en",
  "language_tier": 1,
  "reply": {
    "text": "Your complaint has been filed. Ticket ID: FMC-261104-858I. Department: Water Supply.",
    "quick_replies": []
  },
  "ticket": {
    "ticket_id": "FMC-261104-858I",
    "department": "Water Supply",
    "status": "Filed"
  }
}
```

`state` is one of `IDLE`, `AWAITING_DEPARTMENT`, `AWAITING_LOCATION` or
`TICKET_CREATED`. `language_tier` is `1` for verified languages and `2` for
experimental ones.

```bash
curl -s -X POST "$BASE_URL/api/v1/chat/messages" \
  -H "Content-Type: application/json" \
  -d '{"text":"There is no water supply in Shivaji Nagar since yesterday."}'
```

## Public ticket status

### `GET /api/v1/tickets/{public_id}`

Returns public fields and events explicitly marked public. No authentication.
Public requests are rate-limited per client IP by `RATE_LIMIT_STATUS`. Complaint
text, contact details and private notes are never returned.

```bash
curl -s "$BASE_URL/api/v1/tickets/FMC-261104-858I"
```

```json
{
  "public_id": "FMC-261104-858I",
  "language": "en",
  "status_code": "FILED",
  "status": "Filed",
  "department": "Water Supply",
  "location": "Shivaji Nagar",
  "created_at": "2026-11-04T11:36:55.629567Z",
  "updated_at": "2026-11-04T11:36:55.629539Z",
  "public_events": [
    {
      "from_status": null,
      "to_status": "Filed",
      "note": null,
      "created_at": "2026-11-04T11:36:55.640029Z"
    }
  ]
}
```

Unknown IDs return HTTP 404 with the standard error envelope.

## Authentication

### `POST /api/v1/auth/login`

Exchanges a seeded officer or admin username and password for a bearer token.
Credentials are configured through the `DEMO_*` environment variables at seed
time; they are not published in the repository.

```bash
curl -s -X POST "$BASE_URL/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"username":"<officer-username>","password":"<officer-password>"}'
```

Request:

```json
{
  "username": "<officer-username>",
  "password": "<officer-password>"
}
```

```json
{
  "access_token": "<signed-jwt>",
  "token_type": "bearer",
  "role": "DEPARTMENT_OFFICER",
  "department": "WATER"
}
```

`role` is `DEPARTMENT_OFFICER` or `ADMIN`; `department` is `null` for admins.
Invalid credentials return HTTP 401. The account is reloaded and checked as
active on each protected request.

Use the token in every staff request:

```bash
export TOKEN="<signed-jwt>"
curl -s "$BASE_URL/api/v1/admin/tickets" \
  -H "Authorization: Bearer $TOKEN"
```

## Staff ticket queue

### `GET /api/v1/admin/tickets`

Bearer token required (`DEPARTMENT_OFFICER` or `ADMIN`). Officers are scoped to
their own department by the repository query, even if another department is
requested.

Query parameters:

| Parameter | Type | Default | Notes |
|---|---|---|---|
| `status` | enum | none | `FILED`, `ASSIGNED`, `IN_PROGRESS`, `RESOLVED`, `ESCALATED` |
| `department` | string | none | Department code filter; ignored for officers by scope |
| `q` | string | none | Text search, 1 to 200 characters |
| `date_from` | date | none | Inclusive `YYYY-MM-DD` |
| `date_to` | date | none | Inclusive `YYYY-MM-DD`; must not be before `date_from` |
| `page` | integer | `1` | Minimum 1 |
| `page_size` | integer | `20` | 1 to 100 |

```bash
curl -s "$BASE_URL/api/v1/admin/tickets?status=FILED&page=1&page_size=20" \
  -H "Authorization: Bearer $TOKEN"
```

```json
{
  "items": [
    {
      "public_id": "FMC-261104-858I",
      "status": "FILED",
      "department": "WATER",
      "location": "Shivaji Nagar",
      "language": "en",
      "created_at": "2026-11-04T11:36:55.629567Z",
      "status_changed_at": "2026-11-04T11:36:55.629539Z",
      "escalation_level": 0
    }
  ],
  "total": 1,
  "page": 1,
  "page_size": 20
}
```

An invalid date range (`date_from > date_to`) returns HTTP 422.

## Staff ticket detail

### `GET /api/v1/admin/tickets/{public_id}`

Bearer token required. Officers receive HTTP 404 for tickets outside their
department, the same response as an unknown ticket.

```bash
curl -s "$BASE_URL/api/v1/admin/tickets/FMC-261104-858I" \
  -H "Authorization: Bearer $TOKEN"
```

```json
{
  "public_id": "FMC-261104-858I",
  "status": "FILED",
  "department": "WATER",
  "location": "Shivaji Nagar",
  "language": "en",
  "created_at": "2026-11-04T11:36:55.629567Z",
  "status_changed_at": "2026-11-04T11:36:55.629539Z",
  "escalation_level": 0,
  "complaint_text": "There is no water supply in Shivaji Nagar since yesterday.",
  "contact_phone": null,
  "resolved_at": null,
  "events": [
    {
      "id": "5f0f4a2e-1b7e-4c61-9f0b-7b1b0a8f9b1e",
      "from_status": null,
      "to_status": "FILED",
      "actor_type": "citizen",
      "note": null,
      "is_public": true,
      "created_at": "2026-11-04T11:36:55.640029Z"
    }
  ]
}
```

## Update ticket status

### `PATCH /api/v1/admin/tickets/{public_id}/status`

Bearer token required. Applies a valid lifecycle transition and appends an
auditable event.

Request:

```json
{
  "status": "ASSIGNED",
  "note": "Officer accepted the ticket",
  "is_public": false
}
```

- `status` is required and must be a valid target from the current status.
- `note` is optional, up to 2000 characters.
- `is_public` defaults to `false`; public notes appear on the citizen status
  endpoint.

```bash
curl -s -X PATCH "$BASE_URL/api/v1/admin/tickets/FMC-261104-858I/status" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"status":"ASSIGNED","note":"Officer accepted the ticket","is_public":false}'
```

The response is the same detail shape as `GET /api/v1/admin/tickets/{public_id}`.
An invalid transition returns HTTP 409 with code `INVALID_TRANSITION`.

Allowed transitions:

| From | To |
|---|---|
| `FILED` | `ASSIGNED`, `ESCALATED` |
| `ASSIGNED` | `IN_PROGRESS`, `ESCALATED` |
| `IN_PROGRESS` | `RESOLVED`, `ESCALATED` |
| `ESCALATED` | `IN_PROGRESS`, `RESOLVED` |
| `RESOLVED` | terminal |

## Analytics

### `GET /api/v1/admin/analytics/summary`

Bearer token required. Officers receive counts for their department only;
administrators receive all departments. `average_resolution_time_hours` is
`null` when no ticket has been resolved.

```bash
curl -s "$BASE_URL/api/v1/admin/analytics/summary" \
  -H "Authorization: Bearer $TOKEN"
```

```json
{
  "total_tickets": 12,
  "by_department": [
    { "department_code": "WATER", "department_name": "Water Supply", "count": 7 }
  ],
  "by_status": [
    { "value": "FILED", "count": 8 },
    { "value": "RESOLVED", "count": 4 }
  ],
  "by_language": [
    { "value": "en", "count": 6 },
    { "value": "hi", "count": 6 }
  ],
  "average_resolution_time_hours": 3.5
}
```

## Error format

Every error uses this envelope:

```json
{
  "error": {
    "code": "TICKET_NOT_FOUND",
    "message": "Ticket not found",
    "details": {}
  },
  "request_id": "00000000-0000-0000-0000-000000000000"
}
```

| Status | Meaning |
|---|---|
| 400 | Bad request |
| 401 | Missing, invalid or expired credentials |
| 403 | Authenticated account lacks the required role |
| 404 | Ticket, route or conversation not found |
| 409 | Invalid ticket state transition |
| 413 | Message exceeds `MAX_MESSAGE_LENGTH` |
| 422 | Schema validation error or invalid date range |
| 429 | Public rate limit exceeded (`Retry-After` header set) |
| 500 | Unexpected server error (generic message) |
| 503 | Classifier or department data unavailable |

CORS allows only the origins listed in `CORS_ORIGINS`. Responses include
`X-Content-Type-Options`, `X-Frame-Options`, `Referrer-Policy`,
`Content-Security-Policy` and `Permissions-Policy`; HTTPS responses also carry
HSTS.
