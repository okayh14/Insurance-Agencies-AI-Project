"""Fachlogik des Klassifikators: LLM bestimmt Kategorie und Falltyp."""

from typing import Any

from services.classifier_service.prompts import CLASSIFY_SYSTEM, build_classify_prompt
from shared.llm_client import LlmClient
from shared.logging_config import ServiceLogger
from shared.models import Case


class Classifier:
    """Bekommt seine Werkzeuge von main.py geliefert."""

    def __init__(self, llm: LlmClient, logger: ServiceLogger) -> None:
        self.llm = llm
        self.logger = logger

    def classify(self, case: Case) -> dict[str, Any]:
        """{"category": ..., "case_type": ...}"""
        self.logger.llm(f"Klassifikation ({self.llm.model})")
        ergebnis = self.llm.complete_json(CLASSIFY_SYSTEM, build_classify_prompt(case))
        self.logger.step(
            case.case_id,
            f"Klassifikation -> {ergebnis['category']} / {ergebnis['case_type']}",
        )
        return ergebnis
