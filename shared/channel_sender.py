"""Ausgehende Kommunikation. Kein echter Versand.
Jede Nachricht wird ins Terminal gedruckt UND im Fall protokolliert."""

from datetime import datetime

from shared.case_client import CaseClient
from shared.config import AGENTUR_EMAIL, SCHADENTEAM_EMAIL
from shared.logging_config import ServiceLogger
from shared.models import Case, Channel, OutboundMessage


class ChannelSender:
    """Wird von Validation-, Damage- und Support-Service genutzt.
    Braucht den CaseClient, weil jede Nachricht in outbound protokolliert wird."""

    def __init__(self, case_client: CaseClient, logger: ServiceLogger) -> None:
        self.cases = case_client
        self.logger = logger

    def send_to_customer(self, case: Case, text: str) -> None:
        """Antwort an den Kunden. Kanal und Adresse kommen aus dem Fall -
        der Aufrufer muss den Kanal nicht kennen.
        1. Terminal-Ausgabe  2. append an case.outbound"""
        self.logger.outbound(case.channel.value, case.sender_id, text)
        nachricht = OutboundMessage(
            sent_at=datetime.now(),
            recipient_type="customer",
            channel=case.channel,
            address=case.sender_id,
            subject=None,
            text=text,
        )
        self.cases.append_to(case.case_id, "outbound", nachricht.model_dump(mode="json"))

    def send_to_agent(self, case: Case, subject: str, body: str) -> None:
        """Mail an den Sachbearbeiter der Agentur. Immer E-Mail an AGENTUR_EMAIL.
        Validation (kein Vertrag) und Support (Änderungsmeldung).
        1. Terminal-Ausgabe  2. append an case.outbound"""
        self.logger.outbound(Channel.EMAIL.value, AGENTUR_EMAIL, subject)
        self.logger.mail_body(body)
        nachricht = OutboundMessage(
            sent_at=datetime.now(),
            recipient_type="agent",
            channel=Channel.EMAIL,
            address=AGENTUR_EMAIL,
            subject=subject,
            text=body,
        )
        self.cases.append_to(case.case_id, "outbound", nachricht.model_dump(mode="json"))

    def send_to_schadenteam(self, case: Case, subject: str, body: str) -> None:
        """Mail an das Schadenteam. Immer E-Mail an SCHADENTEAM_EMAIL.
        Nur Damage-Service.
        1. Terminal-Ausgabe  2. append an case.outbound"""
        self.logger.outbound(Channel.EMAIL.value, SCHADENTEAM_EMAIL, subject)
        self.logger.mail_body(body)
        nachricht = OutboundMessage(
            sent_at=datetime.now(),
            recipient_type="schadenteam",
            channel=Channel.EMAIL,
            address=SCHADENTEAM_EMAIL,
            subject=subject,
            text=body,
        )
        self.cases.append_to(case.case_id, "outbound", nachricht.model_dump(mode="json"))
