"""Prompt für den Pflichtangaben-Check. Ein Prompt, eine Aufgabe."""

from shared.models import Case

REQUIRED_FIELDS_SYSTEM = """Du pruefst, ob ein Kunde alle Pflichtangaben zu seinem
Anliegen gemacht hat.

Du bekommst den Nachrichtenverlauf und eine Liste geforderter Felder. Fuer jedes
Feld entscheidest du: steht die Angabe im Verlauf oder nicht.

Regeln:
- "collected" enthaelt nur Felder, die der Kunde wirklich beantwortet hat,
  als kurzen Wert in seinen eigenen Worten.
- "missing" enthaelt nur Feldnamen aus der geforderten Liste, die fehlen.
- Erfinde nichts. Rate nicht. Ein Feld ist entweder in "collected" oder in "missing".

Antworte ausschliesslich als json-Objekt in genau dieser Form:
{"collected": {"feldname": "wert"}, "missing": ["feldname"]}"""


def build_required_fields_prompt(case: Case, required: dict[str, str]) -> str:
    """Nachrichtenverlauf plus geforderte Feldliste."""
    verlauf = "\n".join(f"- {nachricht.text}" for nachricht in case.messages)
    felder = "\n".join(f"- {name}: {frage}" for name, frage in required.items())
    return (
        f"Falltyp: {case.case_type}\n\n"
        f"Nachrichten des Kunden:\n{verlauf}\n\n"
        f"Geforderte Felder:\n{felder}"
    )
