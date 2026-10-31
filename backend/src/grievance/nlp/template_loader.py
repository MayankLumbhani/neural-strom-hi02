"""Load and validate per-language message templates."""

import tomllib
from importlib.resources import files
from typing import Final

from pydantic import BaseModel, ConfigDict

from grievance.nlp.languages import LANGUAGES


class StatusLabels(BaseModel):
    """Localized labels for the supported ticket statuses."""

    model_config = ConfigDict(extra="forbid")

    filed: str
    assigned: str
    in_progress: str
    resolved: str
    escalated: str


class MessageTemplates(BaseModel):
    """Localized fixed messages used by the chatbot."""

    model_config = ConfigDict(extra="forbid")

    ticket_created: str
    ask_location: str
    ask_department: str
    status_reply: str
    status_labels: StatusLabels
    not_found: str
    help: str
    error_generic: str


REQUIRED_TEMPLATE_KEYS: Final[frozenset[str]] = frozenset(
    {
        "ticket_created",
        "ask_location",
        "ask_department",
        "status_reply",
        "status_labels.filed",
        "status_labels.assigned",
        "status_labels.in_progress",
        "status_labels.resolved",
        "status_labels.escalated",
        "not_found",
        "help",
        "error_generic",
    }
)


def load_templates(language_code: str) -> MessageTemplates:
    """Load a validated template set for a registered language code."""
    language = LANGUAGES.get(language_code)
    if language is None or not language.enabled:
        raise ValueError(f"Unsupported or disabled language code: {language_code}")
    resource = files("grievance.nlp.templates").joinpath(language.template_file)
    template_data = tomllib.loads(resource.read_text(encoding="utf-8"))
    return MessageTemplates.model_validate(template_data)


def template_keys(templates: MessageTemplates) -> frozenset[str]:
    """Return the flattened keys in a validated template set."""
    keys = {name for name, value in templates.model_dump().items() if isinstance(value, str)}
    keys.update(f"status_labels.{name}" for name in StatusLabels.model_fields)
    return frozenset(keys)
