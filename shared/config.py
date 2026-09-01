"""Einzige Stelle, die Umgebungsvariablen liest."""

import os
from pathlib import Path

# --- LLM ---
OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
OPENAI_MODEL: str = os.getenv("OPENAI_MODEL", "gpt-5.6-terra")

# --- Service-Adressen (Container-Namen aus docker-compose) ---
CASE_SERVICE_URL: str = os.getenv("CASE_SERVICE_URL", "http://case-service:8000")
CLASSIFIER_SERVICE_URL: str = os.getenv("CLASSIFIER_SERVICE_URL", "http://classifier-service:8000")
VALIDATION_SERVICE_URL: str = os.getenv("VALIDATION_SERVICE_URL", "http://validation-service:8000")
DAMAGE_SERVICE_URL: str = os.getenv("DAMAGE_SERVICE_URL", "http://damage-service:8000")
SUPPORT_SERVICE_URL: str = os.getenv("SUPPORT_SERVICE_URL", "http://support-service:8000")

# Lookup für awaiting_by -> URL (Rückfrage-Kreislauf)
SERVICE_URLS: dict[str, str] = {
    "classifier": CLASSIFIER_SERVICE_URL,
    "validation": VALIDATION_SERVICE_URL,
    "damage": DAMAGE_SERVICE_URL,
    "support": SUPPORT_SERVICE_URL,
}

# --- Pfade ---
DATA_DIR: Path = Path(os.getenv("DATA_DIR", "/app/data"))
CASES_DIR: Path = DATA_DIR / "cases"
CUSTOMERS_FILE: Path = DATA_DIR / "customers.json"
INBOX_FILE: Path = DATA_DIR / "inbox.jsonl"

# --- Fachliche Konstanten ---
AGENT_EMAIL: str = "schadenteam@axa.de"
CURRENCY: str = "EUR"
