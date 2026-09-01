"""WhatsApp-Adapter. Rohformat siehe CLAUDE.md Abschnitt 12."""

from datetime import datetime
from typing import Any

from services.case_service.adapters.base import ChannelAdapter
from shared.models import CanonicalMessage, Channel


class WhatsAppAdapter(ChannelAdapter):
    """{"from": "4917123456789",
        "text": {"body": "..."},
        "timestamp": "1788181323"}"""

    def to_canonical(self, raw: dict[str, Any]) -> CanonicalMessage:
        return CanonicalMessage(
            sender_id=raw["from"],
            channel=Channel.WHATSAPP,
            text=raw["text"]["body"],
            received_at=datetime.fromtimestamp(int(raw["timestamp"])),
            raw=raw,
        )
