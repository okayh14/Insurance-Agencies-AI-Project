"""Bestandsabgleich. Regelbasiert, kein LLM - die billige Pruefung laeuft zuerst."""

from typing import Any

from shared.crm_client import CrmClient
from shared.logging_config import ServiceLogger
from shared.models import Case


class ContractCheck:
    """Bekommt seine Werkzeuge von main.py geliefert."""

    def __init__(self, crm: CrmClient, logger: ServiceLogger) -> None:
        self.crm = crm
        self.logger = logger

    def find(self, case: Case) -> tuple[dict[str, Any] | None, dict[str, Any] | None]:
        """(Kunde, aktiver Vertrag). Beide None-faehig - der Aufrufer entscheidet."""
        kunde = self.crm.find_by_identifier(case.sender_id)
        if kunde is None:
            self.logger.crm(f"Kein Kunde zu {case.sender_id} gefunden")
            return None, None

        vertrag = self.crm.find_active_contract(kunde, case.case_type)
        if vertrag is None:
            self.logger.crm(
                f"Kunde {kunde['customer_number']} gefunden, "
                f"aber kein aktiver Vertrag fuer {case.case_type}"
            )
            return kunde, None

        self.logger.crm(
            f"Kunde {kunde['customer_number']} gefunden, "
            f"Vertrag {vertrag['contract_number']} aktiv"
        )
        return kunde, vertrag
