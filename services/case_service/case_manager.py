"""Fallerkennung, Statusschreibung und PATCH-Anwendung.

Der Status wird hier nur GESCHRIEBEN, nie hergeleitet: die Fachservices
schicken ihn explizit im PATCH mit. Siehe CLAUDE.md 9.1, Festlegung zur
Statusableitung."""

from datetime import datetime

from services.case_service.case_repository import CaseRepository
from shared.logging_config import ServiceLogger
from shared.models import (
    CanonicalMessage,
    Case,
    CasePatch,
    CaseStatus,
    InboundMessage,
)


class CaseManager:
    """Bündelt alles, was über reinen Dateizugriff hinausgeht."""

    def __init__(self, repository: CaseRepository, logger: ServiceLogger) -> None:
        self.repository = repository
        self.logger = logger

    def find_open_case(self, sender_id: str) -> Case | None:
        """Neuester Fall des Absenders, dessen Status nicht terminal ist.
        Ein Kunde kann mehrere abgeschlossene Fälle gehabt haben."""
        offene = [
            fall
            for fall in self.repository.load_all()
            if fall.sender_id == sender_id and fall.is_open()
        ]
        if not offene:
            return None
        return max(offene, key=lambda fall: fall.case_id)

    def create_case(self, message: CanonicalMessage) -> Case:
        """Neuen Fall anlegen, status = new, erste Nachricht drin."""
        jetzt = datetime.now()
        case = Case(
            case_id=self.repository.next_case_id(),
            sender_id=message.sender_id,
            channel=message.channel,
            created_at=jetzt,
            updated_at=jetzt,
            status=CaseStatus.NEW,
            messages=[self._to_inbound(message)],
        )
        self.repository.save(case)
        self.logger.step(case.case_id, f"Neuer Fall angelegt fuer {case.sender_id}")
        return case

    def append_message(self, case: Case, message: CanonicalMessage) -> Case:
        """Nachricht an einen bestehenden offenen Fall anhängen."""
        case.messages.append(self._to_inbound(message))
        case.updated_at = datetime.now()
        self.repository.save(case)
        self.logger.step(
            case.case_id,
            f"Nachricht angehaengt (Status {case.status.value}, "
            f"{len(case.messages)} Nachrichten)",
        )
        return case

    def apply_patch(self, case_id: str, patch: CasePatch) -> Case:
        """set überschreibt Felder, append hängt an eine Liste an.
        Verschachtelte Blöcke werden KOMPLETT ersetzt - es gibt bewusst
        keinen Deep-Merge."""
        daten = self.repository.load(case_id).model_dump(mode="json")

        if patch.set:
            daten.update(patch.set)
        if patch.append:
            for liste, eintrag in patch.append.items():
                daten[liste].append(eintrag)

        daten["updated_at"] = datetime.now().isoformat()
        case = Case.model_validate(daten)
        self.repository.save(case)

        self.logger.step(
            case_id,
            f"PATCH set={sorted(patch.set or {})} append={sorted(patch.append or {})}"
            f" -> Status {case.status.value}",
        )
        return case

    def _to_inbound(self, message: CanonicalMessage) -> InboundMessage:
        return InboundMessage(
            received_at=message.received_at,
            channel=message.channel,
            text=message.text,
        )
