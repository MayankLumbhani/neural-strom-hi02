"""Locust load test for the public chat and ticket-status endpoints.

Run from the repository root against a locally running API:

    python -m locust -f loadtests/locustfile.py --host http://localhost:8000 \
        --headless -u 20 -r 20 -t 60s --csv loadtests/results/locust

The chat task walks the clarification flow (department, then location) until a
ticket is created, then shares the ticket ID with the other simulated users so
the status endpoint is exercised with IDs produced during the run.
"""

from __future__ import annotations

import random
import threading

from locust import HttpUser, between, task

CHAT_PATH = "/api/v1/chat/messages"

# Complaint texts include a location so the happy path can create a ticket.
COMPLAINTS = [
    "There is no water supply in Shivaji Nagar since yesterday. The taps are dry.",
    "Gandhi Road has a large pothole that is damaging vehicles every day.",
    "Kasturba Colony mein kachra 4 din se nahi uthaya gaya hai.",
    "सुभाष नगर में पिछले तीन दिनों से पानी नहीं आ रहा है।",
    "અમદાવાદ રોડ પર સ્ટ્રીટ લાઇટ એક અઠવાડિયાથી બંધ છે.",
    "Sector 7 society mein bijli baar baar ja rahi hai, transformer kharab lagta hai.",
    "The drain near Nehru Chowk is blocked and sewage is overflowing on the road.",
    "मेरे मोहल्ले में नाली बंद है और गंदा पानी सड़क पर आ रहा है।",
    "સરદાર વસાહતમાં કચરાનો ડબ્બો ભરાઈ ગયો છે અને ગંધ આવે છે.",
]

DEPARTMENT_ANSWERS = [
    "Water Supply",
    "Roads",
    "Sanitation",
    "Electricity",
    "Street Lights",
    "Drainage",
    "Public Health",
    "Property Tax",
    "Other",
]

LOCATIONS = [
    "Shivaji Nagar",
    "Gandhi Road",
    "Kasturba Colony",
    "Sector 7",
    "Nehru Chowk",
    "Subhash Nagar",
]

_ticket_ids: list[str] = []
_ticket_lock = threading.Lock()


def _remember_ticket(ticket_id: str) -> None:
    """Store a created ticket ID for later status lookups."""
    with _ticket_lock:
        if ticket_id not in _ticket_ids:
            _ticket_ids.append(ticket_id)


def _random_ticket() -> str | None:
    """Return a ticket ID created during this run, if any."""
    with _ticket_lock:
        if not _ticket_ids:
            return None
        return random.choice(_ticket_ids)


class GrievanceUser(HttpUser):
    """Citizen workload mixing chat filing and status lookups."""

    wait_time = between(0.2, 1.0)

    def _send_chat(
        self,
        text: str,
        conversation_id: str | None = None,
    ) -> dict[str, object] | None:
        """Send one chat message and return the JSON response if successful."""
        payload: dict[str, object] = {"text": text}
        if conversation_id is not None:
            payload["conversation_id"] = conversation_id
        with self.client.post(
            CHAT_PATH,
            json=payload,
            name="POST /api/v1/chat/messages",
            catch_response=True,
        ) as response:
            if response.status_code != 200:
                response.failure(f"chat returned {response.status_code}")
                return None
            try:
                data = response.json()
            except ValueError:
                response.failure("chat response was not JSON")
                return None
            response.success()
            return data

    def _follow_ups(
        self,
        data: dict[str, object],
        conversation_id: str,
    ) -> None:
        """Send follow-up texts that advance the clarification state machine."""
        for _ in range(3):
            ticket = data.get("ticket")
            if isinstance(ticket, dict) and ticket.get("ticket_id"):
                _remember_ticket(str(ticket["ticket_id"]))
                return
            state = str(data.get("state", ""))
            if state == "AWAITING_DEPARTMENT":
                text = random.choice(DEPARTMENT_ANSWERS)
            elif state == "AWAITING_LOCATION":
                text = random.choice(LOCATIONS)
            else:
                return
            data = self._send_chat(text, conversation_id) or {}
            if not data:
                return
        ticket = data.get("ticket")
        if isinstance(ticket, dict) and ticket.get("ticket_id"):
            _remember_ticket(str(ticket["ticket_id"]))

    @task(4)
    def file_complaint(self) -> None:
        """File a complaint in one of the Tier 1 languages and follow up."""
        data = self._send_chat(random.choice(COMPLAINTS))
        if not data:
            return
        conversation_id = str(data.get("conversation_id", ""))
        if not conversation_id:
            return
        self._follow_ups(data, conversation_id)

    @task(3)
    def check_ticket_status(self) -> None:
        """Look up a ticket ID created earlier in the run."""
        ticket_id = _random_ticket()
        if ticket_id is None:
            return
        with self.client.get(
            f"/api/v1/tickets/{ticket_id}",
            name="GET /api/v1/tickets/{public_id}",
            catch_response=True,
        ) as response:
            if response.status_code not in (200, 404):
                response.failure(f"status returned {response.status_code}")
            else:
                response.success()

    @task(1)
    def health(self) -> None:
        """Ping liveness to separate API availability from chat work."""
        self.client.get("/health", name="GET /health")
