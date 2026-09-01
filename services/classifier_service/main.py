"""Klassifikator-Service: nur bei neuem Fall.

Tür: Endpoint plus Weiterleitung. Die Arbeit steht in classifier.py."""

from typing import Any

import httpx
from fastapi import FastAPI

from services.classifier_service.classifier import Classifier
from shared.case_client import CaseClient
from shared.config import CASE_SERVICE_URL, VALIDATION_SERVICE_URL
from shared.llm_client import LlmClient
from shared.logging_config import get_logger

app = FastAPI()

logger = get_logger("classifier")
cases = CaseClient(CASE_SERVICE_URL)
llm = LlmClient()

classifier = Classifier(llm, logger)


@app.post("/classify")
def classify(body: dict[str, str]) -> Any:
    """Setzt category und case_type. Keine Verzweigung, kein Abbruch."""
    case_id = body["case_id"]
    case = cases.get_case(case_id)

    ergebnis = classifier.classify(case)

    cases.set_fields(
        case_id,
        {
            "category": ergebnis["category"],
            "case_type": ergebnis["case_type"],
            "status": "classified",
        },
    )

    url = VALIDATION_SERVICE_URL + "/validate"
    logger.next_service(url)
    # timeout=None: die Kette laeuft bewusst synchron durch mehrere LLM-Aufrufe,
    # httpx wuerde sonst nach seinen 5 Sekunden Standardwert abbrechen.
    antwort = httpx.post(url, json={"case_id": case_id}, timeout=None)
    antwort.raise_for_status()
    return antwort.json()
