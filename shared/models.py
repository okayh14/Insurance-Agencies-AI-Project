"""Zentrale Datenmodelle. Von allen fünf Services genutzt."""

from datetime import datetime
from enum import Enum
from typing import Any, Literal

from pydantic import BaseModel, Field


# ---------- Enums ----------

class Channel(str, Enum):
    WHATSAPP = "whatsapp"
    EMAIL = "email"


class Category(str, Enum):
    SCHADEN = "schaden"
    BETREUUNG = "betreuung"


class CaseStatus(str, Enum):
    NEW = "new"
    CLASSIFIED = "classified"
    AWAITING_CUSTOMER_REPLY = "awaiting_customer_reply"
    READY_FOR_ASSIGNMENT = "ready_for_assignment"
    ASSIGNED = "assigned"
    MANUAL_REVIEW = "manual_review"
    CLOSED = "closed"


TERMINAL_STATUSES = {
    CaseStatus.ASSIGNED,
    CaseStatus.MANUAL_REVIEW,
    CaseStatus.CLOSED,
}


class Severity(str, Enum):
    NIEDRIG = "niedrig"
    MITTEL = "mittel"
    HOCH = "hoch"


# ---------- Eingang ----------

class CanonicalMessage(BaseModel):
    """Einheitliches internes Format. Ergebnis jedes Kanal-Adapters.
    Ab hier kennt das System den Kanal nur noch als Feld."""
    sender_id: str
    channel: Channel
    text: str
    received_at: datetime
    raw: dict[str, Any]


# ---------- Bausteine des Falls ----------

class InboundMessage(BaseModel):
    received_at: datetime
    channel: Channel
    text: str


class OutboundMessage(BaseModel):
    sent_at: datetime
    recipient_type: Literal["customer", "agent"]
    channel: Channel
    address: str
    subject: str | None = None
    text: str


class ContractInfo(BaseModel):
    """Vom Validation-Service aus dem CRM übernommen."""
    contract_number: str
    product: str
    status: str
    deductible: int


class FieldsBlock(BaseModel):
    """Ergebnis des Pflichtangaben-Checks."""
    collected: dict[str, str] = Field(default_factory=dict)
    missing: list[str] = Field(default_factory=list)


class DamageBlock(BaseModel):
    """Nur bei category == schaden."""
    severity: Severity
    severity_reason: str
    summary: str


class SupportBlock(BaseModel):
    """Nur bei category == betreuung. Je nach case_type sind
    unterschiedliche Felder gefüllt. KEIN Feld support_kind."""
    answer: str | None = None
    change_type: str | None = None
    change_values: dict[str, str] | None = None


# ---------- Der Fall ----------

class Case(BaseModel):
    """Die Akte. Einziges Gedächtnis des Systems."""

    case_id: str
    sender_id: str
    channel: Channel
    created_at: datetime
    updated_at: datetime

    status: CaseStatus = CaseStatus.NEW
    awaiting_by: str | None = None

    category: Category | None = None
    case_type: str | None = None

    customer_number: str | None = None
    contract: ContractInfo | None = None

    fields: FieldsBlock = Field(default_factory=FieldsBlock)
    damage: DamageBlock | None = None
    support: SupportBlock | None = None

    messages: list[InboundMessage] = Field(default_factory=list)
    outbound: list[OutboundMessage] = Field(default_factory=list)

    def is_open(self) -> bool:
        """True, solange der Status nicht terminal ist."""
        return self.status not in TERMINAL_STATUSES


# ---------- Verträge zwischen Services ----------

class CasePatch(BaseModel):
    """Body für PATCH /cases/{case_id}. Beide Schlüssel optional."""
    set: dict[str, Any] | None = None
    append: dict[str, Any] | None = None


class ServiceResult(BaseModel):
    """Rein informativ - der Zustand steht im Fall, nicht hier.
    outcome z.B.: incomplete, no_contract, assigned, closed."""
    case_id: str
    service: str
    outcome: str
    next_service: str | None = None
