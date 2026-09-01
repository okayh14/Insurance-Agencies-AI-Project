"""Fallzusammenfassung per LLM. Prosa fuer den Sachbearbeiter."""

from services.damage_service.prompts import SUMMARY_SYSTEM, build_summary_prompt
from shared.llm_client import LlmClient
from shared.logging_config import ServiceLogger
from shared.models import Case


class CaseSummary:
    """Bekommt seine Werkzeuge von main.py geliefert."""

    def __init__(self, llm: LlmClient, logger: ServiceLogger) -> None:
        self.llm = llm
        self.logger = logger

    def build(self, case: Case, severity: str, severity_reason: str) -> str:
        """Die Severity-Begruendung geht bewusst mit in den Prompt."""
        self.logger.llm(f"Fallzusammenfassung ({self.llm.model})")
        text = self.llm.complete_text(
            SUMMARY_SYSTEM, build_summary_prompt(case, severity, severity_reason)
        )
        self.logger.step(case.case_id, "Fallzusammenfassung erstellt")
        return text
