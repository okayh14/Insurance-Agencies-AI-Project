"""Simuliert eine eingehende Kundennachricht.

Laeuft auf dem HOST, nicht im Container - deshalb localhost statt der
internen Docker-Adresse aus shared/config.py.

    python tools/send_message.py whatsapp 4917123456789 "Ich hatte einen Unfall"
    python tools/send_message.py email michael.bauer@gmx.de "Wasserschaden melden"

Bei E-Mail kann optional ein Betreff als viertes Argument folgen. Der
Adapter stellt ihn dem Text voran, weil er oft das Anliegen traegt:

    python tools/send_message.py email michael.bauer@gmx.de "Text" "Schadenmeldung"
"""

import sys
from datetime import datetime, timezone

import httpx

BASE_URL = "http://localhost:8000"


def build_raw(channel: str, absender: str, text: str, betreff: str) -> dict:
    """Kanalspezifisches Rohformat wie in CLAUDE.md Abschnitt 12.

    Beide Zeitangaben landen in Container-Zeit (UTC): der Unix-Timestamp
    rechnet der Adapter ohnehin dort um, das ISO-Datum bauen wir deshalb
    ebenfalls als naive UTC. Sonst stuenden eingehende und ausgehende
    Nachrichten im Dialog von show_case.py in falscher Reihenfolge."""
    jetzt = datetime.now(timezone.utc)
    if channel == "whatsapp":
        return {
            "from": absender,
            "text": {"body": text},
            "timestamp": str(int(jetzt.timestamp())),
        }
    return {
        "sender": absender,
        "subject": betreff,
        "body_plain": text,
        "date": jetzt.replace(tzinfo=None).isoformat(timespec="seconds"),
    }


channel, absender, text = sys.argv[1], sys.argv[2], sys.argv[3]
betreff = sys.argv[4] if len(sys.argv) > 4 else "Nachricht"

# timeout=None: der Webhook antwortet bewusst erst, wenn die ganze Kette
# mit allen LLM-Aufrufen durchgelaufen ist.
antwort = httpx.post(
    f"{BASE_URL}/inbound/{channel}",
    json=build_raw(channel, absender, text, betreff),
    timeout=None,
)
antwort.raise_for_status()

ergebnis = antwort.json()
print(f"{ergebnis['case_id']} -> {ergebnis['service']}: {ergebnis['outcome']}")
