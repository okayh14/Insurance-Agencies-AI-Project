"""Sachbearbeiter-Mail beim Schadenfall. Reine Formatierung, kein LLM.
Format wörtlich nach CLAUDE.md Abschnitt 20."""

import textwrap
from typing import Any

from shared.config import CURRENCY
from shared.models import Case, Severity

LINE = "-" * 60
WIDTH = 60
LABEL = 16
FIELD_LABEL = 18
CHANNEL_LABELS = {"whatsapp": "WhatsApp", "email": "E-Mail"}


def build_body(case: Case, customer: dict[str, Any]) -> str:
    """Vollstaendige Mail. Status ist zum Bauzeitpunkt ready_for_assignment."""
    teile = [
        _abschnitt("FALLDATEN"),
        _zeile("Fall-ID:", case.case_id),
        _zeile("Eingang:", case.created_at.strftime("%d.%m.%Y, %H:%M")),
        _zeile("Kanal:", CHANNEL_LABELS[case.channel.value]),
        _zeile("Status:", case.status.value),
        "",
        _abschnitt("KUNDE UND VERTRAG"),
        _zeile("Kundennummer:", case.customer_number),
        _zeile("Name:", customer["name"]),
        _zeile("Vertrag:", case.contract.contract_number),
        _zeile("Produkt:", case.contract.product),
        _zeile("Vertragsstatus:", _vertragsstatus(case.contract.status)),
        _zeile("Selbstbehalt:", f"{case.contract.deductible} {CURRENCY}"),
        "",
        _abschnitt("PFLICHTANGABEN"),
    ]

    for name, wert in case.fields.collected.items():
        teile.append(f"{_feldname(name)}:".ljust(FIELD_LABEL) + wert)

    teile += [
        "",
        _abschnitt("EINSCHAETZUNG"),
        _zeile("Severity:", case.damage.severity.value),
        _umbruch("Begruendung:", case.damage.severity_reason),
    ]

    if case.damage.severity == Severity.HOCH:
        teile += [
            "",
            textwrap.fill(
                "HINWEIS: Aufgrund der hohen Schadenschwere Gutachter-Einsatz pruefen.",
                width=WIDTH,
                subsequent_indent=" " * 9,
            ),
        ]

    teile += [
        "",
        _abschnitt("ZUSAMMENFASSUNG"),
        textwrap.fill(case.damage.summary, width=WIDTH),
        "",
        _abschnitt("NACHRICHTENVERLAUF"),
    ]

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
    return label.ljust(LABEL) + wert


def _umbruch(label: str, text: str) -> str:
    """Label plus Fliesstext, Folgezeilen unter dem Wert eingerueckt."""
    return textwrap.fill(
        label.ljust(LABEL) + text, width=WIDTH, subsequent_indent=" " * LABEL
    )


def _feldname(name: str) -> str:
    return name.replace("_", " ").capitalize()


def _vertragsstatus(status: str) -> str:
    return "aktiv" if status == "active" else status
