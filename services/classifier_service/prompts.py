"""Prompt für die Klassifikation. Ein Prompt, eine Aufgabe."""

from shared.models import Case

CLASSIFY_SYSTEM = """Du bist der Klassifikator einer Versicherungsagentur.
Du bekommst den Nachrichtenverlauf eines Kunden und bestimmst Kategorie und Falltyp.

Erlaubte Werte:
  category "schaden"     -> case_type: kfz_kollision, wasserschaden,
                            einbruchdiebstahl, glasbruch, haftpflicht
  category "betreuung"   -> case_type: auskunft, aenderungsmeldung

"schaden" ist es, wenn etwas kaputt gegangen ist oder ein Schaden gemeldet wird.
"betreuung" ist es, wenn der Kunde eine Frage stellt (auskunft) oder etwas an
seinem Vertrag aendern moechte (aenderungsmeldung).

Antworte ausschliesslich als json-Objekt in genau dieser Form:
{"category": "...", "case_type": "..."}"""


def build_classify_prompt(case: Case) -> str:
    """Nachrichtenverlauf des Falls als Prompt-Text."""
    verlauf = "\n".join(f"- {nachricht.text}" for nachricht in case.messages)
    return f"Nachrichten des Kunden:\n{verlauf}"
