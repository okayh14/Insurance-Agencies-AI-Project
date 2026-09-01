"""Basis für alle Kanal-Adapter."""

from abc import ABC, abstractmethod
from typing import Any

from shared.models import CanonicalMessage


class ChannelAdapter(ABC):
    """Ein Adapter pro Kanal. Übersetzt das kanalspezifische Rohformat
    in das einheitliche interne Format. Danach kennt das System den
    Kanal nur noch als Feld."""

    @abstractmethod
    def to_canonical(self, raw: dict[str, Any]) -> CanonicalMessage:
        """Rohformat -> CanonicalMessage."""
