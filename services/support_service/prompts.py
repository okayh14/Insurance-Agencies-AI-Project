"""Zwei Prompts: Auskunft (Freitext) und Extraktion einer Aenderungsmeldung (json)."""

from shared.config import CURRENCY
from shared.models import Case

INQUIRY_SYSTEM = """Du beantwortest als Servicemitarbeiter einer Versicherungsagentur
die Frage eines Kunden.

Du bekommst die Frage und die Vertragsdaten des Kunden. Antworte hoeflich, in drei
bis fuenf Saetzen, mit direkter Anrede. Nutze ausschliesslich die uebergebenen
Vertragsdaten - erfinde keine Zahlen, keine Fristen, keine Bedingungen. Wenn die
Daten die Frage nicht beantworten, sage das und verweise auf einen Rueckruf."""

CHANGE_SYSTEM = """Du liest eine Aenderungsmeldung zu einem Versicherungsvertrag aus.

Erlaubte Werte fuer change_type: "adresse", "fahrzeugwechsel", "kuendigung".

In change_values stehen die genannten Angaben. Bei "adresse" nutze - soweit genannt -
die Schluessel neue_strasse, neue_plz, neuer_ort, gueltig_ab. Bei den anderen Typen
waehle sprechende Schluessel in derselben Schreibweise.

Nimm nur auf, was der Kunde wirklich geschrieben hat. Erfinde nichts und frage
nicht nach - fehlende Angaben bleiben einfach weg.

Antworte ausschliesslich als json-Objekt in genau dieser Form:
{"change_type": "adresse|fahrzeugwechsel|kuendigung", "change_values": {"schluessel": "wert"}}"""


def build_inquiry_prompt(case: Case) -> str:
    """Kundenfrage plus Vertragsdaten."""
    verlauf = "\n".join(f"- {nachricht.text}" for nachricht in case.messages)
    return (
        f"Vertrag: {case.contract.contract_number}, {case.contract.product}, "
        f"Status {case.contract.status}, "
        f"Selbstbehalt {case.contract.deductible} {CURRENCY}\n\n"
        f"Nachrichten des Kunden:\n{verlauf}"
    )


def build_change_prompt(case: Case) -> str:
    """Nur der Nachrichtenverlauf - keine Vollstaendigkeitspruefung."""
    verlauf = "\n".join(f"- {nachricht.text}" for nachricht in case.messages)
    return f"Nachrichten des Kunden:\n{verlauf}"
