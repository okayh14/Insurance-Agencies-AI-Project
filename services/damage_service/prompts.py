"""Zwei Prompts: Severity-Schaetzung und Fallzusammenfassung."""

from shared.config import CURRENCY
from shared.models import Case

SEVERITY_SYSTEM = """Du schaetzt die Schwere eines gemeldeten Versicherungsschadens ein.

Stufen:
  "niedrig" - kleiner Sachschaden, kein Personenschaden, keine Folgekosten
  "mittel"  - deutlicher Sachschaden, kein Personenschaden, Sache noch nutzbar
  "hoch"    - Personenschaden moeglich, Sache unbrauchbar oder sehr hoher Schaden

Die Begruendung ist ein einziger sachlicher Satz fuer den Sachbearbeiter.

Antworte ausschliesslich als json-Objekt in genau dieser Form:
{"severity": "niedrig|mittel|hoch", "severity_reason": "..."}"""

SUMMARY_SYSTEM = """Du schreibst die Fallzusammenfassung fuer den Sachbearbeiter
einer Versicherungsagentur.

Vier bis sechs Saetze, sachlich, keine Anrede, keine Aufzaehlung. Nenne den
Schadenhergang, den Zustand der beschaedigten Sache und die Vertragslage.
Beziehe die uebergebene Severity-Begruendung mit ein. Erfinde nichts."""


def build_severity_prompt(case: Case) -> str:
    """Pflichtangaben plus Nachrichtenverlauf."""
    verlauf = "\n".join(f"- {nachricht.text}" for nachricht in case.messages)
    angaben = "\n".join(f"- {name}: {wert}" for name, wert in case.fields.collected.items())
    return (
        f"Falltyp: {case.case_type}\n\n"
        f"Pflichtangaben:\n{angaben}\n\n"
        f"Nachrichten des Kunden:\n{verlauf}"
    )


def build_summary_prompt(case: Case, severity: str, severity_reason: str) -> str:
    """Wie oben, zusaetzlich Vertrag und die bereits ermittelte Severity."""
    verlauf = "\n".join(f"- {nachricht.text}" for nachricht in case.messages)
    angaben = "\n".join(f"- {name}: {wert}" for name, wert in case.fields.collected.items())
    return (
        f"Falltyp: {case.case_type}\n\n"
        f"Pflichtangaben:\n{angaben}\n\n"
        f"Vertrag: {case.contract.product} ({case.contract.status}), "
        f"Selbstbehalt {case.contract.deductible} {CURRENCY}\n\n"
        f"Severity: {severity} - {severity_reason}\n\n"
        f"Nachrichten des Kunden:\n{verlauf}"
    )
