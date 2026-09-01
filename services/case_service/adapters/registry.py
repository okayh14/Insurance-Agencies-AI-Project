"""Auswahl des Adapters über den Kanal. Eine der genau zwei Stellen,
an denen die Kanal-Unterscheidung überhaupt existiert."""

from services.case_service.adapters.base import ChannelAdapter
from services.case_service.adapters.email import EmailAdapter
from services.case_service.adapters.whatsapp import WhatsAppAdapter
from shared.models import Channel

ADAPTERS: dict[Channel, ChannelAdapter] = {
    Channel.WHATSAPP: WhatsAppAdapter(),
    Channel.EMAIL: EmailAdapter(),
}
