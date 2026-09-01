"""Feste Textbausteine für Kundennachrichten. Bewusst kein LLM:
reproduzierbar in der Demo und fachlich kontrolliert."""

from shared.models import Category


def followup_missing_fields(questions: list[str]) -> str:
    """Rückfrage bei unvollständigen Pflichtangaben (Validation-Service).
    Bekommt die fertigen Klartextfragen - die Übersetzung der technischen
    Feldnamen macht der Validation-Service über seinen field_catalog."""
    return (
        "Guten Tag, für die Bearbeitung fehlen uns noch: "
        + " ".join(questions)
        + " Bitte antworten Sie einfach auf diese Nachricht."
    )


def confirmation_damage_received(case_id: str) -> str:
    """Bestätigung, dass der Schaden aufgenommen und weitergeleitet wurde."""
    return (
        "Vielen Dank, Ihre Schadenmeldung ist bei uns eingegangen und wurde unter "
        f"der Vorgangsnummer {case_id} an unsere Schadenabteilung weitergeleitet. "
        "Ein Sachbearbeiter meldet sich bei Ihnen."
    )


def confirmation_change_request(change_type: str) -> str:
    """Bestätigung einer Änderungsmeldung (Support-Service)."""
    return (
        f"Vielen Dank, Ihre Änderungsmeldung ({change_type}) ist bei uns eingegangen "
        "und wird von einem Sachbearbeiter übernommen."
    )


def escalation_no_contract() -> str:
    """Hinweis an den Kunden, wenn kein gültiger Vertrag gefunden wurde."""
    return (
        "Guten Tag, zu Ihren Kontaktdaten konnten wir keinen aktiven Vertrag finden. "
        "Ihr Anliegen wurde zur manuellen Prüfung an einen Sachbearbeiter übergeben."
    )


def agent_mail_subject(case) -> str:
    """Betreff der Sachbearbeiter-Mail.
    z.B. 'Neuer Schadenfall case_0001 - kfz_kollision - Severity mittel'"""
    if case.category == Category.SCHADEN:
        return (
            f"Neuer Schadenfall {case.case_id} - {case.case_type}"
            f" - Severity {case.damage.severity.value}"
        )
    return f"Aenderungsmeldung {case.case_id} - {case.support.change_type}"
