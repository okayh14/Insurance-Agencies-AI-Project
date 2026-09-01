"""E-Mail-Adapter. Rohformat siehe CLAUDE.md Abschnitt 12."""

from datetime import datetime
from typing import Any

from services.case_service.adapters.base import ChannelAdapter
from shared.models import CanonicalMessage, Channel


class EmailAdapter(ChannelAdapter):
    """{"sender": "michael.bauer@gmx.de",
        "subject": "Schadenmeldung",
        "body_plain": "Guten Tag, ...",
        "date": "2026-08-31T14:22:03"}

    Der Betreff wandert mit in den Text - er trägt oft das Anliegen.
    Das Rohformat bleibt in raw und in inbox.jsonl erhalten."""

    def to_canonical(self, raw: dict[str, Any]) -> CanonicalMessage:
        return CanonicalMessage(
            sender_id=raw["sender"],
            channel=Channel.EMAIL,
            text=f"{raw['subject']}\n\n{raw['body_plain']}",
            received_at=datetime.fromisoformat(raw["date"]),
            raw=raw,
        )
