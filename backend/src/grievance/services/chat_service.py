"""Stateless chat orchestration over persisted conversations and tickets."""

import re
import unicodedata
from uuid import UUID

from sqlmodel import Session

from grievance.core.config import Settings
from grievance.core.exceptions import DomainError
from grievance.models import Conversation, Ticket
from grievance.nlp.classifier import Classifier, Prediction
from grievance.nlp.extraction import extract_location
from grievance.nlp.language import detect_language
from grievance.nlp.languages import LANGUAGES
from grievance.nlp.template_loader import load_templates
from grievance.repositories.conversation_repository import (
    add_message,
    create_conversation,
    get_conversation,
    update_conversation,
)
from grievance.repositories.department_repository import (
    get_department_by_code,
    get_department_by_id,
)
from grievance.repositories.ticket_repository import (
    get_ticket_by_public_id,
    get_ticket_for_conversation,
)
from grievance.schemas.chat import ChatReply, ChatResponse, ChatTicketSummary
from grievance.seed import DEPARTMENTS
from grievance.services.ticket_service import (
    TicketService,
    department_display_name,
    ticket_status_label,
)

GREETING_PHRASES: dict[str, frozenset[str]] = {
    "en": frozenset({"hi", "hello", "hey", "good morning", "good afternoon", "good evening"}),
    "hi": frozenset({"नमस्ते", "नमस्कार", "हैलो", "प्रणाम"}),
    "gu": frozenset({"નમસ્તે", "નમસ્કાર", "હેલો"}),
    "hinglish": frozenset({"namaste", "namaskar", "hello", "hi", "hey"}),
}
HELP_PHRASES: dict[str, frozenset[str]] = {
    "en": frozenset({"help", "/help"}),
    "hi": frozenset({"मदद", "सहायता", "/help"}),
    "gu": frozenset({"મદદ", "સહાય", "/help"}),
    "hinglish": frozenset({"madad", "help", "/help"}),
}
TICKET_ID_PATTERN = re.compile(r"^[A-Z0-9]+-\d{6}-[A-Z0-9]{4}$", re.IGNORECASE)


class ChatService:
    """Handle a citizen message and persist the updated conversation and transcript."""

    def __init__(
        self,
        session: Session,
        settings: Settings,
        classifier: Classifier,
    ) -> None:
        """Bind chat orchestration to request-scoped persistence and classifier dependencies."""
        self._session = session
        self._settings = settings
        self._classifier = classifier

    def handle_message(self, text: str, conversation_id: UUID | None = None) -> ChatResponse:
        """Process one citizen message through the complaint, clarification, or status flow."""
        normalized = " ".join(unicodedata.normalize("NFC", text).split())
        if not normalized:
            raise DomainError(
                code="EMPTY_MESSAGE",
                message="Message must not be empty",
                status_code=422,
            )
        if len(normalized) > self._settings.max_message_length:
            raise DomainError(
                code="MESSAGE_TOO_LONG",
                message="Message exceeds the configured maximum length",
                status_code=413,
            )

        conversation = (
            get_conversation(self._session, conversation_id)
            if conversation_id is not None
            else None
        )
        if conversation_id is not None and conversation is None:
            raise DomainError(
                code="CONVERSATION_NOT_FOUND",
                message="Conversation not found",
                status_code=404,
            )
        detection = detect_language(normalized)
        if conversation is None:
            language_code = detection.language.code if detection.language is not None else "en"
            conversation = create_conversation(self._session, language_code)
        else:
            language_code = (
                detection.language.code if detection.language is not None else conversation.language
            )
            conversation.language = language_code

        self._save_message(conversation, "citizen", normalized, language_code)

        if conversation.state == "AWAITING_LOCATION":
            response = self._accept_location(conversation, normalized)
        elif conversation.state == "AWAITING_DEPARTMENT":
            response = self._resolve_department(conversation, normalized)
        else:
            response = self._handle_new_message(conversation, normalized, language_code)

        self._save_message(conversation, "bot", response.reply.text, language_code)
        update_conversation(self._session, conversation)
        return response

    def _handle_new_message(
        self,
        conversation: Conversation,
        text: str,
        language_code: str,
    ) -> ChatResponse:
        """Handle greeting, help, status lookup, or a new complaint."""
        templates = load_templates(language_code)
        normalized = text.casefold()
        if normalized in GREETING_PHRASES.get(language_code, frozenset()):
            reply = templates.help
            return self._response(conversation, language_code, "IDLE", reply)
        if normalized in HELP_PHRASES.get(language_code, frozenset()):
            return self._response(conversation, language_code, "IDLE", templates.help)

        if TICKET_ID_PATTERN.fullmatch(text):
            ticket = get_ticket_by_public_id(self._session, text.upper())
            if ticket is None:
                return self._response(conversation, language_code, "IDLE", templates.not_found)
            department = get_department_by_id(self._session, ticket.department_id)
            if department is None:
                raise DomainError(
                    code="DEPARTMENT_NOT_FOUND",
                    message="Department data is not available",
                    status_code=503,
                )
            department_name = department_display_name(department, language_code)
            status_label = ticket_status_label(ticket.status, language_code)
            reply = templates.status_reply.format(
                ticket_id=ticket.public_id,
                status=status_label,
                department=department_name,
            )
            return self._response(
                conversation,
                language_code,
                "IDLE",
                reply,
                ticket=self._ticket_summary(ticket, department_name, status_label),
            )

        return self._classify_complaint(conversation, text, language_code, text)

    def _classify_complaint(
        self,
        conversation: Conversation,
        classification_text: str,
        language_code: str,
        complaint_text: str,
        department_code: str | None = None,
    ) -> ChatResponse:
        """Choose a department or ask a fixed-template clarification."""
        templates = load_templates(language_code)
        prediction = self._classifier.predict(classification_text)
        if (
            department_code is None
            and prediction.confidence < self._settings.classifier_low_threshold
        ):
            if conversation.state == "AWAITING_DEPARTMENT":
                department_code = "OTHER"
            else:
                conversation.state = "AWAITING_DEPARTMENT"
                conversation.pending_text = complaint_text
                conversation.pending_department = None
                choices = self._all_departments(language_code)
                return self._response(
                    conversation,
                    language_code,
                    "AWAITING_DEPARTMENT",
                    templates.ask_department,
                    choices,
                )
        elif (
            department_code is None
            and prediction.confidence < self._settings.classifier_high_threshold
        ):
            conversation.state = "AWAITING_DEPARTMENT"
            conversation.pending_text = complaint_text
            conversation.pending_department = None
            choices = self._prediction_departments(prediction, language_code)
            return self._response(
                conversation,
                language_code,
                "AWAITING_DEPARTMENT",
                templates.ask_department,
                choices,
            )

        selected_code = department_code or str(prediction.label)
        return self._collect_location(conversation, complaint_text, language_code, selected_code)

    def _resolve_department(
        self,
        conversation: Conversation,
        clarification: str,
    ) -> ChatResponse:
        """Use a quick-reply department or reclassify one clarification."""
        language_code = conversation.language
        selected = self._resolve_department_choice(clarification, language_code)
        pending_text = conversation.pending_text or clarification
        classification_text = (
            f"{pending_text} {clarification}" if selected is None else pending_text
        )
        return self._classify_complaint(
            conversation,
            classification_text,
            language_code,
            classification_text,
            department_code=selected,
        )

    def _collect_location(
        self,
        conversation: Conversation,
        complaint_text: str,
        language_code: str,
        department_code: str,
    ) -> ChatResponse:
        """Extract a location or persist the complaint pending citizen clarification."""
        location = extract_location(complaint_text, language_code, self._settings)
        if location is None:
            conversation.state = "AWAITING_LOCATION"
            conversation.pending_text = complaint_text
            conversation.pending_department = department_code
            templates = load_templates(language_code)
            return self._response(
                conversation,
                language_code,
                "AWAITING_LOCATION",
                templates.ask_location,
            )
        return self._create_ticket(
            conversation,
            complaint_text,
            language_code,
            department_code,
            location,
        )

    def _accept_location(self, conversation: Conversation, location: str) -> ChatResponse:
        """Use the citizen's location reply and create the pending ticket."""
        department_code = conversation.pending_department
        complaint_text = conversation.pending_text
        if not department_code or not complaint_text:
            raise RuntimeError("Conversation location state is missing its pending complaint")
        return self._create_ticket(
            conversation,
            complaint_text,
            conversation.language,
            department_code,
            location,
        )

    def _create_ticket(
        self,
        conversation: Conversation,
        complaint_text: str,
        language_code: str,
        department_code: str,
        location: str,
        predicted_confidence: float | None = None,
    ) -> ChatResponse:
        """Persist a ticket and return its localized confirmation."""
        existing_ticket = get_ticket_for_conversation(self._session, conversation.id)
        if existing_ticket is not None:
            raise DomainError(
                code="CONVERSATION_ALREADY_HAS_TICKET",
                message="This conversation already has a ticket",
                status_code=409,
            )
        department = get_department_by_code(self._session, department_code)
        if department is None or department.id is None:
            raise DomainError(
                code="DEPARTMENT_NOT_FOUND",
                message="Department data is not available",
                status_code=503,
            )
        ticket = TicketService(self._session, self._settings).create_ticket(
            conversation_id=conversation.id,
            department_id=department.id,
            complaint_text=complaint_text,
            language=language_code,
            location_text=location,
            predicted_confidence=predicted_confidence,
        )
        department_name = department_display_name(department, language_code)
        templates = load_templates(language_code)
        reply = templates.ticket_created.format(
            ticket_id=ticket.public_id,
            department=department_name,
        )
        conversation.state = "IDLE"
        conversation.pending_text = None
        conversation.pending_department = None
        conversation.pending_location = None
        return self._response(
            conversation,
            language_code,
            "TICKET_CREATED",
            reply,
            ticket=ChatTicketSummary(
                ticket_id=ticket.public_id,
                department=department_name,
                status=templates.status_labels.filed,
            ),
        )

    def _resolve_department_choice(self, choice: str, language_code: str) -> str | None:
        """Match a quick reply by code or the known localized department names."""
        normalized_choice = choice.casefold().strip()
        for seed in DEPARTMENTS:
            department = get_department_by_code(self._session, seed.code)
            if department is None:
                continue
            names = {
                seed.code.casefold(),
                seed.name_en.casefold(),
                seed.name_hi.casefold(),
                seed.name_gu.casefold(),
                department_display_name(department, language_code).casefold(),
            }
            if normalized_choice in names:
                return seed.code
        return None

    def _all_departments(self, language_code: str) -> list[str]:
        """Return translated choices for all configured departments."""
        choices = []
        for seed in DEPARTMENTS:
            department = get_department_by_code(self._session, seed.code)
            if department is not None:
                choices.append(department_display_name(department, language_code))
        return choices

    def _prediction_departments(
        self,
        prediction: Prediction,
        language_code: str,
    ) -> list[str]:
        """Return the classifier's ranked departments as translated quick replies."""
        choices = []
        for code, _ in prediction.top_k[:2]:
            department = get_department_by_code(self._session, str(code))
            if department is not None:
                choices.append(department_display_name(department, language_code))
        return choices

    @staticmethod
    def _ticket_summary(ticket: Ticket, department: str, status: str) -> ChatTicketSummary:
        """Build the public chat ticket summary without complaint or contact fields."""
        return ChatTicketSummary(
            ticket_id=ticket.public_id,
            department=department,
            status=status,
        )

    @staticmethod
    def _response(
        conversation: Conversation,
        language_code: str,
        state: str,
        text: str,
        quick_replies: list[str] | None = None,
        ticket: ChatTicketSummary | None = None,
    ) -> ChatResponse:
        """Build a typed response using the current conversation identifier."""
        return ChatResponse(
            conversation_id=conversation.id,
            state=state,
            language=language_code,
            language_tier=LANGUAGES[language_code].tier,
            reply=ChatReply(text=text, quick_replies=quick_replies or []),
            ticket=ticket,
        )

    def _save_message(
        self,
        conversation: Conversation,
        sender: str,
        text: str,
        language_code: str,
    ) -> None:
        """Persist one transcript entry without logging its personal text."""
        add_message(
            self._session,
            conversation.id,
            sender,
            text,
            language_code,
        )
