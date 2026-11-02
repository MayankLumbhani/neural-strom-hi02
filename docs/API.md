# Public API

The backend exposes a versioned public API under `/api/v1`. All responses
include an `X-Request-ID` header. JSON errors use the standard error envelope
documented below.

## Send a chat message

`POST /api/v1/chat/messages`

Request:

```json
{
  "text": "Water leaks near Lotus Park for two days.",
  "conversation_id": null
}
```

`conversation_id` is optional for the first message and should be sent on
follow-up messages. The request rejects empty text and messages above
`MAX_MESSAGE_LENGTH`.

Response:

```json
{
  "conversation_id": "00000000-0000-0000-0000-000000000000",
  "state": "TICKET_CREATED",
  "language": "en",
  "reply": {
    "text": "Your complaint has been filed. Ticket ID: FMC-261102-AB12. Department: Water Supply.",
    "quick_replies": []
  },
  "ticket": {
    "ticket_id": "FMC-261102-AB12",
    "department": "Water Supply",
    "status": "Filed"
  }
}
```

During clarification, `state` is `AWAITING_DEPARTMENT` or
`AWAITING_LOCATION`; the response includes the localized prompt and optional
department `quick_replies`. No ticket is returned until filing or a ticket
status lookup.

## Look up ticket status

`GET /api/v1/tickets/{public_id}`

The response contains the public ticket ID, localized status and department,
location, creation/update timestamps, and events explicitly marked public.
Complaint text, contact details, and private event notes are never returned.
Unknown IDs return HTTP 404.

## Officer and administrator authentication

`POST /api/v1/auth/login`

Request:

```json
{
  "username": "demo-officer",
  "password": "configured-in-the-local-environment"
}
```

Successful login returns a signed bearer token, role, and assigned department
code (or `null` for an administrator):

```json
{
  "access_token": "<signed-jwt>",
  "token_type": "bearer",
  "role": "DEPARTMENT_OFFICER",
  "department": "WATER"
}
```

Invalid credentials return HTTP 401. `JWT_SECRET` must be configured to issue
or verify tokens. The API reloads the account for each protected request, so
inactive accounts cannot continue using existing tokens.

## Staff ticket queue and details

Send the token using the HTTP bearer authorization header.

- `GET /api/v1/admin/tickets` accepts optional `status`, `department`, and `q`
  filters, plus `page` (default 1) and `page_size` (default 20, maximum 100).
  Department officers can see only their assigned department, regardless of
  the requested department filter. Administrators can see all departments.
- `GET /api/v1/admin/tickets/{public_id}` returns ticket details and full
  event history. An officer receives HTTP 404 for a ticket outside their
  department, matching the response for an unknown ticket.
- `PATCH /api/v1/admin/tickets/{public_id}/status` accepts a valid lifecycle
  status, optional event note, and optional `is_public` flag:

```json
{
  "status": "ASSIGNED",
  "note": "Officer accepted the ticket",
  "is_public": false
}
```

Status transitions that violate the ticket lifecycle return HTTP 409. Every
successful transition creates an event with the authenticated officer as its
actor. Department scope is enforced by repository queries before reads and
updates.

## Errors

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

Request validation errors return HTTP 422, overlong chat messages return HTTP
413, unavailable classifier and department data return HTTP 503, missing
tickets return HTTP 404, invalid credentials or tokens return HTTP 401, and
disallowed roles return HTTP 403. Browser origins are restricted to
`CORS_ORIGINS`.

`GET /health` reports liveness; `GET /ready` reports classifier readiness.
