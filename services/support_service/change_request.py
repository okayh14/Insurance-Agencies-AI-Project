"""Aenderungsmeldung: Extraktion per LLM plus die kurze Sachbearbeiter-Mail.

Bewusst ohne Vollstaendigkeitspruefung, ohne Rueckfrage, ohne sensible Daten.
Mailformat wörtlich nach CLAUDE.md Abschnitt 20 - keine Severity, keine
Zusammenfassung, das sind Schadenkonzepte."""

import textwrap
from typing import Any

from services.support_service.prompts import CHANGE_SYSTEM, build_change_prompt
from shared.llm_client import LlmClient
from shared.logging_config import ServiceLogger
from shared.models import Case

LINE = "-" * 60
WIDTH = 60
LABEL = 16
CHANNEL_LABELS = {"whatsapp": "WhatsApp", "email": "E-Mail"}

# Sprechende Beschriftungen fuer die haeufigen Adressfelder.
LABELS = {
    "neue_strasse": "Neue Strasse",
    "neue_plz": "Neue PLZ",
    "neuer_ort": "Neuer Ort",
    "gueltig_ab": "Gueltig ab",
}


class ChangeRequest:
    """Bekommt seine Werkzeuge von main.py geliefert."""

    def __init__(self, llm: LlmClient, logger: ServiceLogger) -> None:
        self.llm = llm
        self.logger = logger

    def extract(self, case: Case) -> dict[str, Any]:
        """{"change_type": ..., "change_values": {...}}"""
        self.logger.llm(f"Extraktion Aenderungsmeldung ({self.llm.model})")
        ergebnis = self.llm.complete_json(CHANGE_SYSTEM, build_change_prompt(case))
        self.logger.step(
            case.case_id,
            f"Aenderung -> {ergebnis['change_type']}: "
            f"{', '.join(ergebnis['change_values'])}",
        )
        return ergebnis

    def build_body(self, case: Case, customer: dict[str, Any]) -> str:
        """Deutlich kuerzer als die Schadenmail."""
        teile = [
            _abschnitt("FALLDATEN"),
            _zeile("Fall-ID:", case.case_id),
            _zeile("Eingang:", case.created_at.strftime("%d.%m.%Y, %H:%M")),
            _zeile("Kanal:", CHANNEL_LABELS[case.channel.value]),
            "",
            _abschnitt("KUNDE UND VERTRAG"),
            _zeile("Kundennummer:", case.customer_number),
            _zeile("Name:", customer["name"]),
            _zeile("Vertrag:", case.contract.contract_number),
            _zeile("Produkt:", case.contract.product),
            _zeile("Vertragsstatus:", _vertragsstatus(case.contract.status)),
            "",
            _abschnitt("AENDERUNG"),
            _zeile("Art:", case.support.change_type),
        ]

        for name, wert in (case.support.change_values or {}).items():
            teile.append(_zeile(f"{_beschriftung(name)}:", wert))

        teile += ["", _abschnitt("NACHRICHTENVERLAUF")]
        for nachricht in case.messages:
            zeitpunkt = nachricht.received_at.strftime("%d.%m.%Y %H:%M")
            teile.append(
                textwrap.fill(
                    f"[{zeitpunkt}] Kunde: {nachricht.text}",
                    width=WIDTH,
                    subsequent_indent=" " * 19,
                )
            )

        return "\n".join(teile)


def _abschnitt(titel: str) -> str:
    return f"{LINE}\n{titel}\n{LINE}"


def _zeile(label: str, wert: str) -> str:
    """Laengere Labels bekommen ein einzelnes Leerzeichen, damit der Wert
    nie am Doppelpunkt klebt."""
    if len(label) >= LABEL:
        return f"{label} {wert}"
    return label.ljust(LABEL) + wert


def _beschriftung(name: str) -> str:
    return LABELS.get(name, name.replace("_", " ").capitalize())


def _vertragsstatus(status: str) -> str:
    return "aktiv" if status == "active" else status
