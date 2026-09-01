"""Zeigt einen Fall lesbar, inklusive Dialogprotokoll in beide Richtungen.

    python tools/show_case.py 1

Laeuft auf dem HOST. Den Kundennamen liest das Tool direkt aus
data/customers.json - im Fall steht nur die Kundennummer."""

import json
import sys
import textwrap
from datetime import datetime
from pathlib import Path

import httpx

BASE_URL = "http://localhost:8000"
CUSTOMERS_FILE = Path(__file__).resolve().parent.parent / "data" / "customers.json"

RAHMEN = "=" * 60
TRENNER = "-" * 60
LABEL = 12
FELD = 17
DIALOG_LABEL = 27
DIALOG_INDENT = 38
DIALOG_WIDTH = 70


def kundenname(customer_number: str) -> str:
    """Klartextname aus dem simulierten Bestandssystem."""
    for kunde in json.loads(CUSTOMERS_FILE.read_text(encoding="utf-8")):
        if kunde["customer_number"] == customer_number:
            return kunde["name"]
    return ""


def kopfzeile(label: str, wert: str) -> str:
    return " " + label.ljust(LABEL) + wert


def dialog_zeile(zeitpunkt: datetime, label: str, text: str) -> str:
    """Zeit, Richtung, Text - Folgezeilen unter dem Text eingerueckt."""
    einzeilig = " ".join(text.split())
    return textwrap.fill(
        f" {zeitpunkt.strftime('%H:%M:%S')}  {label.ljust(DIALOG_LABEL)}{einzeilig}",
        width=DIALOG_WIDTH,
        subsequent_indent=" " * DIALOG_INDENT,
    )


argument = sys.argv[1]
case_id = f"case_{int(argument):04d}" if argument.isdigit() else argument

antwort = httpx.get(f"{BASE_URL}/cases/{case_id}")
antwort.raise_for_status()
fall = antwort.json()

# --- Kopfblock ---
print(RAHMEN)
print(f" Fall {fall['case_id']}".ljust(41) + f"Status: {fall['status']}")
print(RAHMEN)
print(kopfzeile("Absender:", f"{fall['sender_id']} ({fall['channel']})"))

if fall["category"]:
    print(kopfzeile("Kategorie:", f"{fall['category']} / {fall['case_type']}"))

if fall["customer_number"]:
    print(
        kopfzeile(
            "Kunde:", f"{fall['customer_number']} {kundenname(fall['customer_number'])}"
        )
    )

if fall["contract"]:
    vertrag = fall["contract"]
    status = "aktiv" if vertrag["status"] == "active" else vertrag["status"]
    print(
        kopfzeile(
            "Vertrag:",
            f"{vertrag['contract_number']} {vertrag['product']} ({status}), "
            f"SB {vertrag['deductible']} EUR",
        )
    )

if fall["damage"]:
    print(kopfzeile("Severity:", fall["damage"]["severity"]))

# --- Pflichtangaben ---
print()
print(" Pflichtangaben:")
for name, wert in fall["fields"]["collected"].items():
    # Lange Werte umbrechen, damit der 60er-Rahmen haelt.
    print(
        textwrap.fill(
            "   " + name.ljust(FELD) + " ".join(wert.split()),
            width=len(RAHMEN),
            subsequent_indent=" " * (3 + FELD),
        )
    )
fehlend = fall["fields"]["missing"]
print("   " + "fehlend:".ljust(FELD) + (", ".join(fehlend) if fehlend else "-"))

# --- Dialog: eingehend und ausgehend chronologisch gemischt ---
print()
print(TRENNER)
print(" DIALOG")
print(TRENNER)

eintraege = [
    (
        datetime.fromisoformat(nachricht["received_at"]),
        f"<- Kunde ({nachricht['channel']})",
        nachricht["text"],
    )
    for nachricht in fall["messages"]
]

for nachricht in fall["outbound"]:
    if nachricht["recipient_type"] == "agent":
        # Nur der Betreff - der volle Mailtext steht im Terminal-Log.
        label, text = f"-> Sachbearbeiter ({nachricht['channel']})", nachricht["subject"]
    else:
        label, text = f"-> Kunde ({nachricht['channel']})", nachricht["text"]
    eintraege.append((datetime.fromisoformat(nachricht["sent_at"]), label, text))

for zeitpunkt, label, text in sorted(eintraege, key=lambda eintrag: eintrag[0]):
    print(dialog_zeile(zeitpunkt, label, text))

print(RAHMEN)
