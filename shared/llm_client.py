"""OpenAI-Zugriff. Kein Provider-Interface, kein Fallback, kein Retry."""

import json
from typing import Any

from openai import OpenAI

from shared.config import OPENAI_API_KEY, OPENAI_MODEL


class LlmClient:
    """Kapselt die Kommunikation mit OpenAI."""

    def __init__(self, api_key: str = OPENAI_API_KEY, model: str = OPENAI_MODEL) -> None:
        self.model = model
        self.client = OpenAI(api_key=api_key)

    def complete_json(self, system_prompt: str, user_prompt: str) -> dict[str, Any]:
        """Antwort als Dictionary. Nutzt response_format={"type": "json_object"}.
        Für Klassifikation, Pflichtangaben-Check, Severity, Extraktion."""
        antwort = self.client.chat.completions.create(
            model=self.model,
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
        )
        return json.loads(antwort.choices[0].message.content)

    def complete_text(self, system_prompt: str, user_prompt: str) -> str:
        """Antwort als Freitext.
        Für Fallzusammenfassung und Auskunft."""
        antwort = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
        )
        return antwort.choices[0].message.content
