"""Support-Service: Auskunft ODER Aenderungsmeldung.

Tür: Endpoint plus die Weiche nach case_type. Die Arbeit steht in inquiry.py
und change_request.py. Endstation - beide Pfade rufen keinen weiteren Service.

Der entscheidende Unterschied: eine Auskunft beantwortet das System selbst und
endet auf closed. Eine Aenderungsmeldung geht an einen Menschen und endet auf
assigned."""

from fastapi import FastAPI

from services.support_service.change_request import ChangeRequest
from services.support_service.inquiry import Inquiry
from shared.case_client import CaseClient
from shared.channel_sender import ChannelSender
from shared.config import CASE_SERVICE_URL
from shared.crm_client import CrmClient
from shared.llm_client import LlmClient
from shared.logging_config import get_logger
from shared.models import ServiceResult
from shared.templates import agent_mail_subject, confirmation_change_request

app = FastAPI()

logger = get_logger("support")
cases = CaseClient(CASE_SERVICE_URL)
crm = CrmClient()
llm = LlmClient()
sender = ChannelSender(cases, logger)

inquiry = Inquiry(llm, logger)
change_request = ChangeRequest(llm, logger)


@app.post("/handle-support")
def handle_support(body: dict[str, str]) -> ServiceResult:
    case_id = body["case_id"]
    case = cases.get_case(case_id)

    if case.case_type == "auskunft":
        # Vollautomatisch: kein Sachbearbeiter beteiligt.
        antwort = inquiry.answer(case)
        case = cases.set_fields(case_id, {"support": {"answer": antwort}})
        sender.send_to_customer(case, antwort)
        cases.set_fields(case_id, {"status": "closed"})
        logger.decision(case_id, "Auskunft direkt beantwortet -> closed")
        return ServiceResult(
            case_id=case_id, service="support", outcome="closed", next_service=None
        )

    ergebnis = change_request.extract(case)
    case = cases.set_fields(
        case_id,
        {
            "support": {
                "change_type": ergebnis["change_type"],
                "change_values": ergebnis["change_values"],
            }
        },
    )

    kunde = crm.find_by_identifier(case.sender_id)
    sender.send_to_agent(
        case, agent_mail_subject(case), change_request.build_body(case, kunde)
    )
    sender.send_to_customer(case, confirmation_change_request(case.support.change_type))

    cases.set_fields(case_id, {"status": "assigned"})
    logger.decision(case_id, "Aenderungsmeldung an Sachbearbeiter uebergeben -> assigned")

    return ServiceResult(
        case_id=case_id, service="support", outcome="assigned", next_service=None
    )
