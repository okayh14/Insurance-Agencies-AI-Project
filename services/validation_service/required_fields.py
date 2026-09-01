"""Pflichtangaben-Check per LLM."""

from typing import Any

from services.validation_service.prompts import (
    REQUIRED_FIELDS_SYSTEM,
    build_required_fields_prompt,
)
from shared.llm_client import LlmClient
from shared.logging_config import ServiceLogger
from shared.models import Case


class RequiredFieldsCheck:
    """Bekommt seine Werkzeuge von main.py geliefert."""

    def __init__(self, llm: LlmClient, logger: ServiceLogger) -> None:
        self.llm = llm
        self.logger = logger

    def check(self, case: Case, required: dict[str, str]) -> dict[str, Any]:
        """{"collected": {...}, "missing": [...]}"""
        self.logger.llm(f"Pflichtangaben-Check ({self.llm.model})")
        ergebnis = self.llm.complete_json(
            REQUIRED_FIELDS_SYSTEM, build_required_fields_prompt(case, required)
        )
        fehlend = ergebnis["missing"]
        if fehlend:
            self.logger.step(
                case.case_id,
                f"Pflichtangaben-Check -> unvollstaendig: {', '.join(fehlend)}",
            )
        else:
            self.logger.step(case.case_id, "Pflichtangaben-Check -> vollstaendig")
        return ergebnis
