"""Damage-Service: Severity, Zusammenfassung, Sachbearbeiter-Mail.

Tür: Endpoint. Die Arbeit steht in severity.py, summary.py und agent_mail.py.
Endstation - hier wird kein weiterer Service gerufen."""

from fastapi import FastAPI

from services.damage_service.agent_mail import build_body
from services.damage_service.severity import SeverityCheck
from services.damage_service.summary import CaseSummary
from shared.case_client import CaseClient
from shared.channel_sender import ChannelSender
from shared.config import CASE_SERVICE_URL
from shared.crm_client import CrmClient
from shared.llm_client import LlmClient
from shared.logging_config import get_logger
from shared.models import ServiceResult
from shared.templates import agent_mail_subject, confirmation_damage_received

app = FastAPI()

logger = get_logger("damage")
cases = CaseClient(CASE_SERVICE_URL)
crm = CrmClient()
llm = LlmClient()
sender = ChannelSender(cases, logger)

severity_check = SeverityCheck(llm, logger)
case_summary = CaseSummary(llm, logger)


@app.post("/handle-damage")
def handle_damage(body: dict[str, str]) -> ServiceResult:
    """contract und customer_number sind da - Zusage aus dem Validation-Vertrag."""
    case_id = body["case_id"]
    case = cases.get_case(case_id)

    einschaetzung = severity_check.estimate(case)
    zusammenfassung = case_summary.build(
        case, einschaetzung["severity"], einschaetzung["severity_reason"]
    )

    # Der zurueckgegebene Fall traegt den damage-Block, den Betreff und Mail brauchen.
    case = cases.set_fields(
        case_id,
        {
            "damage": {
                "severity": einschaetzung["severity"],
                "severity_reason": einschaetzung["severity_reason"],
                "summary": zusammenfassung,
            }
        },
    )

    kunde = crm.find_by_identifier(case.sender_id)
    sender.send_to_agent(case, agent_mail_subject(case), build_body(case, kunde))
    sender.send_to_customer(case, confirmation_damage_received(case_id))

    cases.set_fields(case_id, {"status": "assigned"})
    logger.decision(case_id, "Schadenfall an Sachbearbeiter uebergeben -> assigned")

    return ServiceResult(
        case_id=case_id, service="damage", outcome="assigned", next_service=None
    )
