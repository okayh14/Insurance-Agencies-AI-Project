"""Case-Service: Webhook, Kanal-Adapter, Datenhoheit.

Tür: nur Endpoint-Definitionen und die Weiterleitungsentscheidung.
Die Arbeit steht in case_repository.py und case_manager.py."""

from typing import Any

import httpx
from fastapi import FastAPI

from services.case_service.adapters.registry import ADAPTERS
from services.case_service.case_manager import CaseManager
from services.case_service.case_repository import CaseRepository
from shared.config import SERVICE_URLS
from shared.logging_config import get_logger
from shared.models import Case, CasePatch, CaseStatus, Channel

# Endpoint je Service. Steht hier und nicht in shared/config.py, weil nur
# der Case-Service weiterleitet - SERVICE_URLS liefert nur die Basis-URL.
SERVICE_ENDPOINTS: dict[str, str] = {
    "classifier": "/classify",
    "validation": "/validate",
    "damage": "/handle-damage",
    "support": "/handle-support",
}

app = FastAPI()

logger = get_logger("case")
repository = CaseRepository()
manager = CaseManager(repository, logger)


@app.post("/inbound/{channel}")
def inbound(channel: Channel, raw: dict[str, Any]) -> Any:
    """Webhook. Antwortet erst, wenn die ganze Kette durchgelaufen ist."""
    logger.separator(f"Neue Nachricht ueber {channel.value.upper()}")

    message = ADAPTERS[channel].to_canonical(raw)

    repository.append_inbox(raw)
    logger.step(message.sender_id, "Rohnachricht in inbox.jsonl protokolliert")

    case = manager.find_open_case(message.sender_id)
    if case is None:
        case = manager.create_case(message)
        is_new = True
    else:
        case = manager.append_message(case, message)
        is_new = False

    if is_new:
        ziel = "classifier"
        grund = "neuer Fall"
    elif case.status == CaseStatus.AWAITING_CUSTOMER_REPLY:
        ziel = case.awaiting_by # -> aktuell nur validation
        grund = f"Kundenantwort erwartet von {case.awaiting_by}"
    else:
        ziel = "validation"
        grund = f"bestehender Fall im Status {case.status.value}"

    url = SERVICE_URLS[ziel] + SERVICE_ENDPOINTS[ziel]
    logger.decision(case.case_id, f"{grund} -> {ziel}")
    logger.next_service(url)

    # timeout=None: die Kette laeuft bewusst synchron durch mehrere LLM-Aufrufe,
    # httpx wuerde sonst nach seinen 5 Sekunden Standardwert abbrechen.
    antwort = httpx.post(url, json={"case_id": case.case_id}, timeout=None)
    antwort.raise_for_status()
    return antwort.json()


@app.get("/cases")
def list_cases() -> list[dict[str, Any]]:
    """Kurzübersicht aller Fälle."""
    return [
        {
            "case_id": fall.case_id,
            "sender_id": fall.sender_id,
            "category": fall.category.value if fall.category else None,
            "case_type": fall.case_type,
            "status": fall.status.value,
            "updated_at": fall.updated_at.isoformat(),
        }
        for fall in repository.load_all()
    ]


@app.get("/cases/{case_id}")
def get_case(case_id: str) -> Case:
    return repository.load(case_id)


@app.patch("/cases/{case_id}")
def patch_case(case_id: str, patch: CasePatch) -> Case:
    return manager.apply_patch(case_id, patch)
