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
413, unavailable classifier and department data return HTTP 503, and missing
tickets return HTTP 404. Browser origins are restricted to `CORS_ORIGINS`.

`GET /health` reports liveness; `GET /ready` reports classifier readiness.
