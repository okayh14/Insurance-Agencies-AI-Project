"""Severity-Schaetzung per LLM. Laeuft VOR der Zusammenfassung,
damit die Begruendung dort einfliessen kann."""

from typing import Any

from services.damage_service.prompts import SEVERITY_SYSTEM, build_severity_prompt
from shared.llm_client import LlmClient
from shared.logging_config import ServiceLogger
from shared.models import Case


class SeverityCheck:
    """Bekommt seine Werkzeuge von main.py geliefert."""

    def __init__(self, llm: LlmClient, logger: ServiceLogger) -> None:
        self.llm = llm
        self.logger = logger

    def estimate(self, case: Case) -> dict[str, Any]:
        """{"severity": ..., "severity_reason": ...}"""
        self.logger.llm(f"Severity-Schaetzung ({self.llm.model})")
        ergebnis = self.llm.complete_json(SEVERITY_SYSTEM, build_severity_prompt(case))
        self.logger.step(
            case.case_id,
            f"Severity -> {ergebnis['severity']}: {ergebnis['severity_reason']}",
        )
        return ergebnis
