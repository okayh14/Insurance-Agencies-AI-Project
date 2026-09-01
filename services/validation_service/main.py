"""Validation-Service: Bestandsabgleich, Pflichtangaben-Check, ggf. Rueckfrage.

Tür: Endpoint plus Verzweigung. Die Arbeit steht in contract_check.py und
required_fields.py."""

from typing import Any

import httpx
from fastapi import FastAPI

from services.validation_service.contract_check import ContractCheck
from services.validation_service.field_catalog import get_required_fields
from services.validation_service.required_fields import RequiredFieldsCheck
from shared.case_client import CaseClient
from shared.channel_sender import ChannelSender
from shared.config import (
    CASE_SERVICE_URL,
    DAMAGE_SERVICE_URL,
    SUPPORT_SERVICE_URL,
)
from shared.crm_client import CrmClient
from shared.llm_client import LlmClient
from shared.logging_config import get_logger
from shared.models import Category, ServiceResult
from shared.templates import escalation_no_contract, followup_missing_fields

app = FastAPI()

logger = get_logger("validation")
cases = CaseClient(CASE_SERVICE_URL)
crm = CrmClient()
llm = LlmClient()
sender = ChannelSender(cases, logger)

contract_check = ContractCheck(crm, logger)
field_check = RequiredFieldsCheck(llm, logger)


@app.post("/validate")
def validate(body: dict[str, str]) -> Any:
    """Gemeinsame Pruefung vor der Verzweigung in Schaden oder Betreuung."""
    case_id = body["case_id"]
    case = cases.get_case(case_id)

    # --- Vertragspruefung: regelbasiert, vor jedem LLM-Aufruf ---
    kunde, vertrag = contract_check.find(case)
    if kunde is None or vertrag is None:
        logger.decision(case_id, "kein aktiver Vertrag -> manuelle Pruefung")
        case = cases.set_fields(case_id, {"status": "manual_review"})
        sender.send_to_agent(case, f"Manuelle Pruefung {case_id}", _review_mail(case))
        sender.send_to_customer(case, escalation_no_contract())
        return ServiceResult(case_id=case_id, service="validation", outcome="no_contract")

    # --- Vertragsdaten in die Akte, bevor eine Rueckfrage rausgeht ---
    case = cases.set_fields(
        case_id,
        {
            "customer_number": kunde["customer_number"],
            "contract": {
                "contract_number": vertrag["contract_number"],
                "product": vertrag["product"],
                "status": vertrag["status"],
                "deductible": vertrag["deductible"],
            },
        },
    )

    # --- Pflichtangaben-Check ---
    katalog = get_required_fields(case.case_type)
    ergebnis = field_check.check(case, katalog)
    case = cases.set_fields(
        case_id,
        {"fields": {"collected": ergebnis["collected"], "missing": ergebnis["missing"]}},
    )

    if ergebnis["missing"]:
        fragen = [katalog[feld] for feld in ergebnis["missing"]]
        sender.send_to_customer(case, followup_missing_fields(fragen))
        cases.set_fields(
            case_id,
            {"status": "awaiting_customer_reply", "awaiting_by": "validation"},
        )
        logger.decision(case_id, "Rueckfrage gestellt -> warte auf Kundenantwort")
        return ServiceResult(case_id=case_id, service="validation", outcome="incomplete")

    cases.set_fields(case_id, {"status": "ready_for_assignment"})

    # --- Verzweigung nach Kategorie ---
    if case.category == Category.SCHADEN:
        ziel = "damage"
        url = DAMAGE_SERVICE_URL + "/handle-damage"
    else:
        ziel = "support"
        url = SUPPORT_SERVICE_URL + "/handle-support"

    logger.decision(case_id, f"{case.category.value} -> {ziel}")
    logger.next_service(url)
    antwort = httpx.post(url, json={"case_id": case_id}, timeout=None)
    antwort.raise_for_status()
    return antwort.json()


def _review_mail(case) -> str:
    """Kurze Mail an den Sachbearbeiter, wenn kein Vertrag gefunden wurde."""
    verlauf = "\n".join(
        f"[{nachricht.received_at.strftime('%d.%m.%Y %H:%M')}] Kunde: {nachricht.text}"
        for nachricht in case.messages
    )
    return (
        f"Fall-ID:  {case.case_id}\n"
        f"Absender: {case.sender_id} ({case.channel.value})\n"
        f"Grund:    Kein Kunde oder kein aktiver Vertrag im Bestand gefunden.\n\n"
        f"NACHRICHTENVERLAUF\n{verlauf}"
    )
