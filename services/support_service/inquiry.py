"""Auskunft per LLM. Vollautomatisch - hier wird kein Sachbearbeiter beschaeftigt."""

from services.support_service.prompts import INQUIRY_SYSTEM, build_inquiry_prompt
from shared.llm_client import LlmClient
from shared.logging_config import ServiceLogger
from shared.models import Case


class Inquiry:
    """Bekommt seine Werkzeuge von main.py geliefert."""

    def __init__(self, llm: LlmClient, logger: ServiceLogger) -> None:
        self.llm = llm
        self.logger = logger

    def answer(self, case: Case) -> str:
        """Antworttext fuer den Kunden."""
        self.logger.llm(f"Auskunft ({self.llm.model})")
        text = self.llm.complete_text(INQUIRY_SYSTEM, build_inquiry_prompt(case))
        self.logger.step(case.case_id, "Auskunft erstellt")
        return text
