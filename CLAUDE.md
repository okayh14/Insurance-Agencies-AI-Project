# CLAUDE.md -

## 0. Grundregeln für dich (Claude Code)
- Dies ist ein Uni-MVP für eine Terminal-Demo. KEIN Produktivsystem.
- DIESES DOKUMENT (Teil 1 und Teil 2) IST DIE EINZIGE QUELLE DER WAHRHEIT. Der Ordner docs/ enthält Diagramme nur zur Dokumentation und Abgabe. Sie sind NICHT verbindlich und enthalten veraltete Elemente (Ingress Layer, Terminvorschläge für Gutachter, zentraler Orchestrator), die bewusst gestrichen wurden.
- KEIN Defensive Coding: kein try/except, kein Retry, keine Timeouts, keine Validierungsfestungen. Fehler sollen sichtbar brechen.
- KEIN Frontend. Ausgabe ausschliesslich über Terminal-Prints.
- Halte dich EXAKT an die Ordnerstruktur. Erfinde keine zusätzlichen Dateien, Klassen oder Abstraktionsebenen.
- Deutsche Fachbegriffe im Code beibehalten: Schaden, Betreuung, Sachbearbeiter, Pflichtangaben, Severity, Änderungsmeldung.
- Frag nach, statt zu raten.
- Arbeite phasenweise. Baue nur, was in der aktuellen Phase beauftragt ist.
- Python 3.12, FastAPI, uvicorn, pydantic v2, httpx, openai.

## 1. Was das Projekt ist
Ein System, das eingehende Kundennachrichten (Schadenmeldungen und Serviceanfragen) automatisiert vorverarbeitet und aufbereitet an einen Sachbearbeiter übergibt. Alles von Scratch: kein echtes Bestandssystem, keine echte Datenbank, keine echten Kommunikationskanäle. Simulation über JSON-Dateien und CLI-Skripte.

## 2. Architekturprinzipien (nicht verhandelbar)
1. Choreografie statt Orchestrator: jeder Service entscheidet am Ende selbst per if/else, welcher Service als Nächstes gerufen wird. Keine zentrale Ablaufsteuerung.
2. Datenhoheit ausschliesslich beim Case-Service. Die vier Fachservices sind zustandslos, holen den Fall per HTTP und schreiben per PATCH zurück. In Fachservices existiert KEIN Dateizugriffs-Code. Merksatz: Datenhoheit ist nicht Ablaufsteuerung.
3. Ein Container pro Service, fünf Services. shared/ ist KEIN Container.
4. Merksatz: CRM = nur lesen, direkter Dateizugriff. Cases = schreiben, nur über den Case-Service.
5. Service-Aufrufe geben nur die case_id weiter. Kein Zustand in Request-Bodies.
6. Tür und Arbeit getrennt: main.py = FastAPI-Endpoint plus Weiterleitungsentscheidung. Fachlogik in eigenen Dateien daneben.
7. KI gezielt, nicht dekorativ: LLM nur für Klassifikation, Pflichtangaben-Check, Severity, Zusammenfassung, Auskunft, Extraktion. Kundennachrichten kommen aus festen Templates.
8. Der Fall ist das einzige Gedächtnis des Systems. Weil die Fachservices zustandslos sind, muss alles, was ein späterer Service braucht, vorher in den Fall geschrieben worden sein.
9. Bewusst synchron: der Webhook antwortet erst, wenn die ganze Kette durchgelaufen ist. Gewollt, damit alle Prints in korrekter Reihenfolge erscheinen.
10. Faustregel für Felder: Ein Feld gehört in den Fall, wenn ein SPÄTERER Service es braucht oder wenn es in der Präsentation sichtbar sein soll. Alles andere ist lokale Variable.

## 3. Die fünf Services
| Service | Container | Endpoints | Kernaufgabe |
|---|---|---|---|
| Case-Service | case-service | POST /inbound/{channel}, GET /cases, GET /cases/{id}, PATCH /cases/{id} | Webhook, Kanal-Adapter, Rohnachricht persistieren, Fallerkennung, Datenhoheit |
| Klassifikator | classifier-service | POST /classify | Nur bei neuem Fall: LLM bestimmt Kategorie und Typ |
| Validation | validation-service | POST /validate | Bestandsabgleich regelbasiert, Pflichtangaben-Check LLM, ggf. Rückfrage |
| Damage | damage-service | POST /handle-damage | Severity plus Begründung, Fallzusammenfassung, Mail an Sachbearbeiter |
| Support | support-service | POST /handle-support | Auskunft ODER Änderungsmeldung, Mail plus Kundenbestätigung |

## 4. Kontrollfluss
```text
send_message.py -> POST /inbound/{channel} -> Case-Service (Adapter, inbox.jsonl, Fallerkennung)
  -> neu -> /classify (Klassifikator, setzt category und case_type)
  -> wartet -> SERVICE_URLS[awaiting_by] (Pause-Symbol)
  -> bestehend -> /validate

/validate (Validation) -> kein Vertrag -> manual_review (Quadrat-Symbol)
                        -> unvollständig -> awaiting_customer_reply (Pause-Symbol)
                        -> sonst -> Verzweigung:
                           schaden -> /handle-damage -> assigned (Quadrat-Symbol)
                           betreuung -> /handle-support -> auskunft -> closed (Quadrat-Symbol)
                                                       -> aenderungsmeldung -> assigned (Quadrat-Symbol)
```
Drei Endzustände (assigned, manual_review, closed), ein Wartezustand (awaiting_customer_reply).

## 5. Vollständige Ordnerstruktur
```text
schadenmelde-service/ (docker-compose.yml, requirements.txt, .env, .env.example, .gitignore, CLAUDE.md, README.md)
shared/ (__init__.py, models.py, config.py, logging_config.py, case_client.py, crm_client.py, llm_client.py, channel_sender.py, templates.py)
services/case_service/ (__init__.py, main.py, adapters/(__init__.py, base.py, whatsapp.py, email.py, registry.py), case_repository.py, case_manager.py, Dockerfile)
services/classifier_service/ (__init__.py, main.py, classifier.py, prompts.py, Dockerfile)
services/validation_service/ (__init__.py, main.py, contract_check.py, required_fields.py, field_catalog.py, prompts.py, Dockerfile)
services/damage_service/ (__init__.py, main.py, severity.py, summary.py, agent_mail.py, prompts.py, Dockerfile)
services/support_service/ (__init__.py, main.py, inquiry.py, change_request.py, prompts.py, Dockerfile)
data/ (customers.json, inbox.jsonl, cases/.gitkeep)
docs/ (Dokumentation)
tools/ (send_message.py, show_case.py, list_cases.py)
tests/ (test_adapters.py, test_case_repository.py, test_case_manager.py, test_field_catalog.py)
```
- prompts.py pro Service: ein Prompt gehört zu genau einer Aufgabe.
- templates.py in shared: Validation-Service und Support-Service brauchen beide Kundennachrichten.
- field_catalog.py als eigene Datei: reine Fachkonfiguration, änderbar ohne Code.
- case_client.py in shared: erzwingt strukturell, dass Fachservices keinen Dateizugriff haben.
- case_manager.py: bündelt Fallerkennung, Statusschreibung und PATCH-Anwendung in EINER Datei.
- Ordnernamen mit Unterstrich, Containernamen mit Bindestrich.
- data/ als Volume: Fälle überleben docker compose down.
- inbox.jsonl: line-delimited und append-only.

## 6. shared/models.py - vollständiger Code-Skeleton
# shared/models.py
"""Zentrale Datenmodelle. Von allen fünf Services genutzt."""

from datetime import datetime
from enum import Enum
from typing import Any, Literal

from pydantic import BaseModel, Field


# ---------- Enums ----------

class Channel(str, Enum):
    WHATSAPP = "whatsapp"
    EMAIL = "email"


class Category(str, Enum):
    SCHADEN = "schaden"
    BETREUUNG = "betreuung"


class CaseStatus(str, Enum):
    NEW = "new"
    CLASSIFIED = "classified"
    AWAITING_CUSTOMER_REPLY = "awaiting_customer_reply"
    READY_FOR_ASSIGNMENT = "ready_for_assignment"
    ASSIGNED = "assigned"
    MANUAL_REVIEW = "manual_review"
    CLOSED = "closed"


TERMINAL_STATUSES = {
    CaseStatus.ASSIGNED,
    CaseStatus.MANUAL_REVIEW,
    CaseStatus.CLOSED,
}


class Severity(str, Enum):
    NIEDRIG = "niedrig"
    MITTEL = "mittel"
    HOCH = "hoch"


# ---------- Eingang ----------

class CanonicalMessage(BaseModel):
    """Einheitliches internes Format. Ergebnis jedes Kanal-Adapters.
    Ab hier kennt das System den Kanal nur noch als Feld."""
    sender_id: str
    channel: Channel
    text: str
    received_at: datetime
    raw: dict[str, Any]


# ---------- Bausteine des Falls ----------

class InboundMessage(BaseModel):
    received_at: datetime
    channel: Channel
    text: str


class OutboundMessage(BaseModel):
    sent_at: datetime
    recipient_type: Literal["customer", "agent"]
    channel: Channel
    address: str
    subject: str | None = None
    text: str


class ContractInfo(BaseModel):
    """Vom Validation-Service aus dem CRM übernommen."""
    contract_number: str
    product: str
    status: str
    deductible: int


class FieldsBlock(BaseModel):
    """Ergebnis des Pflichtangaben-Checks."""
    collected: dict[str, str] = Field(default_factory=dict)
    missing: list[str] = Field(default_factory=list)


class DamageBlock(BaseModel):
    """Nur bei category == schaden."""
    severity: Severity
    severity_reason: str
    summary: str


class SupportBlock(BaseModel):
    """Nur bei category == betreuung. Je nach case_type sind
    unterschiedliche Felder gefüllt. KEIN Feld support_kind."""
    answer: str | None = None
    change_type: str | None = None
    change_values: dict[str, str] | None = None


# ---------- Der Fall ----------

class Case(BaseModel):
    """Die Akte. Einziges Gedächtnis des Systems."""

    case_id: str
    sender_id: str
    channel: Channel
    created_at: datetime
    updated_at: datetime

    status: CaseStatus = CaseStatus.NEW
    awaiting_by: str | None = None

    category: Category | None = None
    case_type: str | None = None

    customer_number: str | None = None
    contract: ContractInfo | None = None

    fields: FieldsBlock = Field(default_factory=FieldsBlock)
    damage: DamageBlock | None = None
    support: SupportBlock | None = None

    messages: list[InboundMessage] = Field(default_factory=list)
    outbound: list[OutboundMessage] = Field(default_factory=list)

    def is_open(self) -> bool:
        """True, solange der Status nicht terminal ist."""
        ...


# ---------- Verträge zwischen Services ----------

class CasePatch(BaseModel):
    """Body für PATCH /cases/{case_id}. Beide Schlüssel optional."""
    set: dict[str, Any] | None = None
    append: dict[str, Any] | None = None


class ServiceResult(BaseModel):
    """Rein informativ - der Zustand steht im Fall, nicht hier.
    outcome z.B.: incomplete, no_contract, assigned, closed."""
    case_id: str
    service: str
    outcome: str
    next_service: str | None = None

- case_type ist ein FREIER STRING. FIELD_CATALOG ist die einzige Referenzliste.
- awaiting_by ist ein String.
- case_type leistet DOPPELTE ARBEIT: bei Schaden Pflichtangaben, bei Betreuung Methodenwahl.
- Fachergebnisse sind in Unterobjekte (fields, damage, support) gruppiert.

## 7. Beispiel einer fertigen Fall-Akte
```json
{"case_id": "case_0001", "sender_id": "4917123456789", "channel": "whatsapp", "created_at": "2026-08-31T14:22:03", "updated_at": "2026-08-31T14:26:41", "status": "assigned", "awaiting_by": null, "category": "schaden", "case_type": "kfz_kollision", "customer_number": "K-1001", "contract": {"contract_number": "V-001", "product": "KFZ Vollkasko", "status": "active", "deductible": 500}, "fields": {"collected": {"schadensdatum": "2026-08-30", "schadensort": "Kreuzung Hauptstr./Bahnhofstr., Köln", "schadenshergang": "Auffahrunfall an roter Ampel", "kennzeichen": "K-AB 1234"}, "missing": []}, "damage": {"severity": "mittel", "severity_reason": "Sachschaden am Heck, keine Personenschäden, Fahrzeug fahrbereit.", "summary": "Der Kunde meldet einen Auffahrunfall..."}, "support": null, "messages": [{"received_at": "2026-08-31T14:22:03", "channel": "whatsapp", "text": "Hallo, ich hatte gestern einen Unfall mit meinem Auto."}, {"received_at": "2026-08-31T14:26:12", "channel": "whatsapp", "text": "Das war am 30.08. an der Kreuzung..."}], "outbound": [{"sent_at": "2026-08-31T14:22:09", "recipient_type": "customer", "channel": "whatsapp", "address": "4917123456789", "subject": null, "text": "Guten Tag, für die Bearbeitung..."}, {"sent_at": "2026-08-31T14:26:41", "recipient_type": "agent", "channel": "email", "address": "schadenteam@axa.de", "subject": "Neuer Schadenfall case_0001 - kfz_kollision - Severity mittel", "text": "..."}]}
```

## 8. Die sieben shared/-Werkzeuge - Code-Skeletons
Diese Dateien enthalten keine Fachlogik. Sie beantworten vier Fragen: Woher kommen Einstellungen? Wie sieht Ausgabe aus? Wie rede ich mit etwas außerhalb meines Containers? Welche fertigen Texte gibt es?

Regel: Sobald ein zweiter Service etwas braucht, wandert es nach shared/. Vorher nicht.

8.1 config.py
python

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
Einzige Stelle, die Umgebungsvariablen liest — jeder Name steht genau einmal. DATA_DIR mit Fallback, weil die tools/ auf dem Host laufen, wo ein relativer Pfad gilt. SERVICE_URLS macht den Rücksprung bei einer Kundenantwort zu einer Zeile statt zu einem if/else über alle Services.

8.2 logging_config.py
python

"""Einheitliche Terminal-Ausgabe. Ersetzt print() im ganzen Projekt."""

from datetime import datetime


class ServiceLogger:
    """Ein Logger pro Service. Kennt seinen Namen, damit der
    Aufrufer ihn nicht bei jedem Aufruf mitgeben muss."""

    def __init__(self, service_name: str) -> None:
        self.service_name = service_name

    def _emit(self, tag: str, message: str) -> None:
        """Baut [zeit] [service] [tag] message und printet mit flush=True."""
        ...

    # --- normale Schritte ---
    def step(self, case_id: str, message: str) -> None:
        """Ein fachlicher Schritt innerhalb eines Falls."""
        ...

    def decision(self, case_id: str, message: str) -> None:
        """Eine Weiche/Entscheidung. Optisch hervorgehoben."""
        ...

    # --- Systemgrenzen ---
    def crm(self, message: str) -> None:
        """Zugriff auf das Bestandssystem."""
        ...

    def llm(self, message: str) -> None:
        """LLM-Aufruf."""
        ...

    def outbound(self, channel: str, address: str, text: str) -> None:
        """Ausgehende Nachricht."""
        ...

    def next_service(self, target: str) -> None:
        """Weiterleitung an den nächsten Service (Choreografie sichtbar machen)."""
        ...

    def separator(self, message: str = "") -> None:
        """Trennlinie bei neuer eingehender Nachricht."""
        ...


def get_logger(service_name: str) -> ServiceLogger:
    """Wird in jeder main.py einmal aufgerufen."""
    ...
Ausgabeformat, vier Blöcke, immer gleich lang — dadurch entstehen Spalten:

[14:22:07] [validation] [case_0001] Pflichtangaben-Check -> unvollstaendig: schadensdatum
[14:22:04] [validation] [CRM] Kunde K-1001 gefunden, Vertrag V-001 aktiv
[14:22:06] [validation] [LLM] Pflichtangaben-Check (gpt-5.6-terra)
[14:22:09] [validation] [-> WHATSAPP an 4917123456789] Guten Tag, fuer die Bearbeitung...
[14:22:09] [validation] [-> NEXT] damage-service
Die Sonderformen [CRM], [LLM], [-> KANAL] und [-> NEXT] heben sich absichtlich ab, weil sie Systemgrenzen markieren. separator() wird bei jeder neuen eingehenden Nachricht gerufen.

WICHTIG: In Docker print(..., flush=True) und PYTHONUNBUFFERED=1 setzen. Sonst erscheint in der Demo nichts, obwohl alles funktioniert.

8.3 case_client.py
python

"""HTTP-Zugriff auf den Case-Service. Genutzt von allen vier Fachservices.
Die Fachservices greifen NIE selbst auf Dateien zu."""

import httpx

from shared.models import Case


class CaseClient:
    """Kapselt den HTTP-Zugriff auf den Case-Service."""

    def __init__(self, base_url: str) -> None:
        self.base_url = base_url

    def get_case(self, case_id: str) -> Case:
        """GET /cases/{case_id} -> Case-Objekt."""
        ...

    def set_fields(self, case_id: str, values: dict) -> Case:
        """PATCH mit {"set": values}. Überschreibt Felder."""
        ...

    def append_to(self, case_id: str, list_name: str, item: dict) -> Case:
        """PATCH mit {"append": {list_name: item}}. Hängt an eine Liste an."""
        ...
Wichtigste Datei in shared/ — erzwingt die Regel Datenhoheit strukturell. set_fields und append_to sind getrennt statt einer generischen patch()-Methode, damit der Aufrufer nicht über die JSON-Struktur nachdenken muss und append nicht versehentlich als set geschickt wird. Verschachtelte Felder werden als ganzer Block geschickt (z.B. das komplette fields-Objekt) — kein Pfad-Parsing im Case-Service.

8.4 crm_client.py
python

"""Simuliertes Bestandssystem. Liest data/customers.json, read-only."""

import json
from typing import Any

from shared.config import CUSTOMERS_FILE


class CrmClient:
    """Kapselt den Dateizugriff auf die Kundendaten."""

    def __init__(self, customers_file=CUSTOMERS_FILE) -> None:
        self.customers_file = customers_file

    def _load(self) -> list[dict[str, Any]]:
        """Liest die JSON-Datei bei jedem Zugriff neu.
        Kein Caching - dann kannst du in der Demo live editieren."""
        ...

    def find_by_identifier(self, identifier: str) -> dict[str, Any] | None:
        """Sucht Kunden über Telefonnummer oder E-Mail.
        Unterscheidung über das Vorhandensein von '@'."""
        ...

    def find_active_contract(
        self, customer: dict[str, Any], case_type: str | None = None
    ) -> dict[str, Any] | None:
        """Gibt den passenden aktiven Vertrag zurück.
        Zuordnung Falltyp -> Produkt siehe Teil 2, Abschnitt 11."""
        ...
Bewusst kein Container, weil read-only — nichts zu schützen, keine Reihenfolge, kein Zustand. Bewusst kein Caching, damit customers.json bei laufenden Containern live editierbar ist. Arbeitet mit rohen Dictionaries, nicht mit pydantic-Modellen — bei vier read-only-Feldern ausreichend. Erfinde hier keine Datenklassen.

8.5 llm_client.py
python

"""OpenAI-Zugriff. Kein Provider-Interface, kein Fallback, kein Retry."""

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
        ...

    def complete_text(self, system_prompt: str, user_prompt: str) -> str:
        """Antwort als Freitext.
        Für Fallzusammenfassung und Auskunft."""
        ...
Zwei Methoden, weil es zwei fachlich verschiedene Fälle gibt. complete_json für alles mit Struktur — ohne JSON-Mode kämpft man in der Live-Demo mit Antworten wie „Natürlich! Hier ist die Klassifikation: …". complete_text für Prosa.

Bewusst nicht drin: Provider-Interface, FakeLlmClient, Retry, Fallback, Token-Zählung, Kostenlogging, Streaming.

8.6 channel_sender.py
python

"""Ausgehende Kommunikation. Kein echter Versand.
Jede Nachricht wird ins Terminal gedruckt UND im Fall protokolliert."""

from shared.case_client import CaseClient
from shared.logging_config import ServiceLogger
from shared.models import Case


class ChannelSender:
    """Wird von Validation-Service und Support-Service genutzt.
    Braucht den CaseClient, weil jede Nachricht in outbound protokolliert wird."""

    def __init__(self, case_client: CaseClient, logger: ServiceLogger) -> None:
        self.cases = case_client
        self.logger = logger

    def send_to_customer(self, case: Case, text: str) -> None:
        """Antwort an den Kunden. Kanal und Adresse kommen aus dem Fall -
        der Aufrufer muss den Kanal nicht kennen.
        1. Terminal-Ausgabe  2. append an case.outbound"""
        ...

    def send_to_agent(self, case: Case, subject: str, body: str) -> None:
        """Mail an den Sachbearbeiter. Immer E-Mail an AGENT_EMAIL.
        1. Terminal-Ausgabe  2. append an case.outbound"""
        ...
Beide Methoden machen immer zwei Dinge in dieser Reihenfolge: Terminal-Ausgabe und append an case.outbound.


Merksatz: Der Print ist für das Publikum, der outbound-Eintrag ist für den Fall.


Ohne Protokollierung wäre nach dem Durchlauf nur Terminal-Scrollback da. Zwei Methoden statt einer mit Empfänger-Parameter, weil sich die Semantik unterscheidet: beim Kunden ist der Kanal variabel und es gibt keinen Betreff, beim Sachbearbeiter ist der Kanal fest und der Betreff Pflicht. Der ChannelSender bekommt den CaseClient genau deshalb — damit man das Protokollieren nicht vergessen kann.

8.7 templates.py
python

"""Feste Textbausteine für Kundennachrichten. Bewusst kein LLM:
reproduzierbar in der Demo und fachlich kontrolliert."""


def followup_missing_fields(missing: list[str]) -> str:
    """Rückfrage bei unvollständigen Pflichtangaben (Validation-Service).
    Übersetzt die technischen Feldnamen in die Klartextfragen
    aus dem field_catalog und verkettet sie lesbar."""
    ...


def confirmation_damage_received(case_id: str) -> str:
    """Bestätigung, dass der Schaden aufgenommen und weitergeleitet wurde."""
    ...


def confirmation_change_request(change_type: str) -> str:
    """Bestätigung einer Änderungsmeldung (Support-Service)."""
    ...


def escalation_no_contract() -> str:
    """Hinweis an den Kunden, wenn kein gültiger Vertrag gefunden wurde."""
    ...


def agent_mail_subject(case) -> str:
    """Betreff der Sachbearbeiter-Mail.
    z.B. 'Neuer Schadenfall case_0001 - kfz_kollision - Severity mittel'"""
    ...
Funktionen statt Konstanten mit .format(), weil bei followup_missing_fields die technischen Feldnamen in lesbare Klartextfragen übersetzt und sauber verkettet werden müssen. Bewusst kein LLM für Kundennachrichten: reproduzierbar in der Live-Demo, weil kein Modell dazwischen improvisiert.

8.8 Wie die Bausteine im Service zusammenkommen
python

# services/validation_service/main.py  (nur der Aufbau)

app = FastAPI()

logger = get_logger("validation")
cases = CaseClient(CASE_SERVICE_URL)
crm = CrmClient()
llm = LlmClient()
sender = ChannelSender(cases, logger)

contract_check = ContractCheck(crm, logger)
field_check = RequiredFieldsCheck(llm, logger)
Alle Werkzeuge werden einmal in main.py gebaut und per Dependency Injection in die Fachklassen gegeben. Deshalb steht in den Fachklassen nie os.getenv oder open() — sie bekommen ihre Werkzeuge geliefert.

## 9. Die fünf Ablaufverträge
Ein Ablaufvertrag ist die verbindliche, nummerierte Beschreibung dessen, was ein Service macht — von „Request kommt an" bis „ich rufe den nächsten Service" oder „hier ist Ende". Er beantwortet sechs Fragen: welcher Endpoint und welcher Request-Body, welche Schritte in welcher Reihenfolge, was wird per PATCH geschrieben und wann, welche Abbruchbedingungen es gibt, welche if/else-Entscheidung den nächsten Service bestimmt, welcher Status gesetzt wird.

Er enthält bewusst keine Klassennamen und Methodensignaturen — das ist Handwerk. Der Vertrag ist eine Zusage zwischen Services: wenn dort steht „ich schreibe customer_number und contract", darf der nächste Service sich darauf verlassen.

9.1 Case-Service
POST /inbound/{channel}     Body: kanalspezifisches Rohformat

 1. Trennlinie loggen (neuer Durchlauf beginnt)

 2. Adapter aus ADAPTERS[channel] holen
      -> adapter.to_canonical(raw_body) -> CanonicalMessage

 3. Rohnachricht an data/inbox.jsonl anhängen
      unverändert, VOR jeder Verarbeitung

 4. Fallerkennung: neuester Fall zu sender_id,
    dessen Status NICHT in TERMINAL_STATUSES liegt

 5a. KEIN offener Fall gefunden
       -> neuen Fall anlegen (nächste freie Nummer)
       -> status = new
       -> message anhängen
       -> is_new = True

 5b. OFFENER Fall gefunden
       -> message anhängen
       -> is_new = False

 6. Weiterleitung (if/else):
       is_new                            -> POST classifier /classify
       status == awaiting_customer_reply  -> POST SERVICE_URLS[awaiting_by]
       sonst                              -> POST validation /validate

 7. Antwort des Nachfolgers durchreichen
is_new wird zuerst geprüft — ein neuer Fall kann nie auf eine Antwort warten, damit ist die Reihenfolge eindeutig. Schritt 3 ist die einzige Funktion, die vom gestrichenen Ingress Layer übrig geblieben ist — als Schritt, nicht als Container.

GET /cases/{case_id}
   Fall aus data/cases/case_XXXX.json laden -> Case
PATCH /cases/{case_id}     Body: CasePatch

 1. Fall laden
 2. body.set    -> Felder überschreiben
                   (verschachtelte Blöcke KOMPLETT ersetzen)
 3. body.append -> Item an die genannte Liste anhängen
 4. updated_at = jetzt
 5. Atomar schreiben (.tmp-Datei + rename)
 6. Aktualisierten Fall zurückgeben
GET /cases
   Kurzübersicht aller Fälle:
   case_id, sender_id, category, case_type, status, updated_at
Festlegung zur Statusableitung: Die Fachservices schicken den Zielstatus explizit im PATCH mit, z.B. {"set": {"status": "manual_review"}}. Der Case-Service schreibt ihn, leitet ihn aber nicht selbst her.

Begründung: Der Status wird an einer Stelle geschrieben (im Case-Service), aber nur der Fachservice kennt das Fachergebnis. Ein Case-Service, der aus fields.missing und category den Status errät, hätte Fachlogik, die er nicht haben soll.

9.2 Klassifikator-Service
POST /classify     Body: {"case_id": "case_0001"}

 1. Fall holen (CaseClient)

 2. LLM-Aufruf (complete_json) über case.messages
      Ergebnis: { "category": "...", "case_type": "..." }
      Erlaubte Werte im Prompt vorgeben:
        schaden    -> kfz_kollision, wasserschaden,
                      einbruchdiebstahl, glasbruch, haftpflicht
        betreuung  -> auskunft, aenderungsmeldung

 3. PATCH set: category, case_type, status = classified

 4. Weiterleitung (immer, keine Bedingung):
      -> POST validation /validate

 5. Antwort durchreichen
Keine Verzweigung, kein Abbruch. Bewusst — auch bei unsicherer Klassifikation läuft der Fall weiter, die Vertragsprüfung im nächsten Service fängt ohnehin alles auf, was nicht zuordenbar ist.

9.3 Validation-Service
POST /validate     Body: {"case_id": "case_0001"}

 1. Fall holen

 2. VERTRAGSPRUEFUNG (regelbasiert, CRM, kein LLM)
      crm.find_by_identifier(case.sender_id)
      crm.find_active_contract(customer, case.case_type)

    kein Kunde ODER kein aktiver Vertrag
        -> PATCH set: status = manual_review
        -> send_to_agent(Betreff "Manuelle Pruefung", Grund + Nachrichten)
        -> send_to_customer(escalation_no_contract())
        -> ENDE (outcome = "no_contract")

 3. PATCH set: customer_number, contract
      <- GENAU HIER landen die Daten fuer den Damage-Service

 4. Pflichtfelder fuer case.case_type aus field_catalog holen

 5. PFLICHTANGABEN-CHECK (LLM, complete_json)
      Input: alle case.messages + geforderte Feldliste
      Ergebnis: { "collected": {...}, "missing": [...] }

 6. PATCH set: fields = { collected, missing }

    missing nicht leer
        -> send_to_customer(followup_missing_fields(missing))
        -> PATCH set: status = awaiting_customer_reply,
                      awaiting_by = "validation"
        -> ENDE (outcome = "incomplete")

 7. PATCH set: status = ready_for_assignment

 8. VERZWEIGUNG nach case.category:
      schaden    -> POST damage  /handle-damage
      betreuung  -> POST support /handle-support

 9. Antwort durchreichen

Schritt 2 steht vor Schritt 5: kein Vertrag bedeutet kein LLM-Call. Die billige regelbasierte Prüfung läuft vor der teuren.

Schritt 3 steht vor Schritt 5: damit die Vertragsdaten in der Akte stehen, bevor eine Rückfrage rausgeht.

Der Rücksprung läuft ohne Sonderfall: Bei einer Kundenantwort schickt der Case-Service wieder an SERVICE_URLS["validation"], also erneut auf /validate. Der Vertrag läuft von Schritt 1 an neu, jetzt mit mehr Nachrichten in der Akte. Es gibt keinen zweiten Codepfad für Wiedervorlage.

9.4 Damage-Service
POST /handle-damage     Body: {"case_id": "case_0001"}

 1. Fall holen
      contract + customer_number sind vorhanden
      (Zusage aus dem Validation-Vertrag)

 2. SEVERITY-SCHAETZUNG (LLM, complete_json)
      Input: fields.collected + messages + case_type
      Ergebnis: { "severity": "niedrig|mittel|hoch",
                  "severity_reason": "..." }

 3. FALLZUSAMMENFASSUNG (LLM, complete_text)
      Input: messages + fields.collected + contract
      Ergebnis: Prosa fuer den Sachbearbeiter

 4. PATCH set: damage = { severity, severity_reason, summary }

 5. SACHBEARBEITER-MAIL bauen
      Betreff: templates.agent_mail_subject(case)
      Body:   Falldaten, Kunde + Vertrag + Selbstbehalt,
              Pflichtangaben, Severity + Begruendung,
              Zusammenfassung, Nachrichtenverlauf
      + bei severity == "hoch":
          Textbaustein "Gutachter-Einsatz pruefen"

 6. send_to_agent(...)

 7. send_to_customer(confirmation_damage_received(case_id))

 8. PATCH set: status = assigned

 9. ENDE (outcome = "assigned", next_service = None)
Reihenfolge 2 vor 3, damit die Severity-Begründung in die Zusammenfassung einfließen kann — umgekehrt geht es nicht. Der Textbaustein bei severity: hoch ist der Rest der gestrichenen Terminvorschläge für Gutachter. Das vollständige Mockup der Mail steht in Teil 2, Abschnitt 20.

9.5 Support-Service
POST /handle-support     Body: {"case_id": "case_0001"}

 1. Fall holen

 2. WEICHE nach case.case_type:

  --- case_type == "auskunft" ---------------------------
   2a. AUSKUNFT (LLM, complete_text)
         Input: Kundenfrage + contract
                (Produkt, Status, Selbstbehalt)
         Ergebnis: Antworttext
   2b. PATCH set: support = { answer }
   2c. send_to_customer(answer)
   2d. PATCH set: status = closed
   2e. ENDE (outcome = "closed")
         <- kein Sachbearbeiter beteiligt: vollautomatisch
  ------------------------------------------------------

  --- case_type == "aenderungsmeldung" -----------------
   2a. EXTRAKTION (LLM, complete_json)
         Input: messages
         Ergebnis: { "change_type": "adresse|fahrzeugwechsel|kuendigung",
                     "change_values": {...} }
         KEINE Vollstaendigkeitspruefung, KEINE Rueckfrage
   2b. PATCH set: support = { change_type, change_values }
   2c. send_to_agent(Betreff "Aenderungsmeldung",
                     Typ + Werte + Kunde)
   2d. send_to_customer(confirmation_change_request(change_type))
   2e. PATCH set: status = assigned
   2f. ENDE (outcome = "assigned")
  ------------------------------------------------------

WICHTIGSTER HINWEIS DES GANZEN DOKUMENTS: closed vs. assigned ist der entscheidende Unterschied. Eine Auskunft beantwortet das System vollständig selbst — niemand wird beschäftigt. Eine Änderungsmeldung geht an einen Menschen. Das ist eine Zeile Unterschied, aber wenn sie falsch ist, sieht man es nicht im Code, sondern nur daran, dass in der Präsentation ein Fall im falschen Endzustand landet.


Der Änderungspfad läuft bewusst ohne Vollständigkeitsprüfung und bewusst ohne sensible Daten wie Bankverbindung.

## 10. field_catalog.py - vollständiger Inhalt
Einleitung: Der Katalog sagt, welche Angaben das System braucht, bevor ein Fall an den Sachbearbeiter darf - und zwar unterschiedlich je Falltyp. Das ist der Grund, warum der Klassifikator VOR der Validierung läuft: ohne case_type weiss der Validation-Service nicht, welche Feldliste gilt. Pro Feld gibt es zwei Werte: den technischen Namen für die Logik und die Klartextfrage für die Kundenrückfrage.

```python
# services/validation_service/field_catalog.py
FIELD_CATALOG = {
    "kfz_kollision": {
        "schadensdatum": "Wann ist der Unfall passiert?",
        "schadensort": "Wo ist der Unfall passiert?",
        "schadenshergang": "Wie ist der Unfall passiert?",
        "kennzeichen": "Wie lautet Ihr Kennzeichen?",
        "gegenpartei": "War ein anderes Fahrzeug beteiligt?",
    },
    "wasserschaden": {
        "schadensdatum": "Wann haben Sie den Schaden entdeckt?",
        "schadensort": "In welchem Raum ist der Schaden?",
        "schadensursache": "Was war die Ursache (z.B. Rohrbruch)?",
        "betroffene_gegenstaende": "Welche Gegenstände sind beschädigt?",
    },
    "einbruchdiebstahl": {
        "schadensdatum": "Wann ist der Einbruch passiert?",
        "schadensort": "Wo ist der Einbruch passiert?",
        "entwendete_gegenstaende": "Was wurde entwendet?",
        "polizei_aktenzeichen": "Wie lautet das Aktenzeichen der Polizei?",
    },
    "glasbruch": {
        "schadensdatum": "Wann ist der Schaden passiert?",
        "schadensort": "Wo befindet sich die beschädigte Scheibe?",
        "glasart": "Um welche Art von Glas handelt es sich?",
    },
    "haftpflicht": {
        "schadensdatum": "Wann ist der Schaden passiert?",
        "schadenshergang": "Wie ist der Schaden entstanden?",
        "geschaedigter": "Wer wurde geschädigt?",
        "schadensumfang": "Was wurde beschädigt?",
    },
    "auskunft": {"anliegen": "Worum geht es genau?"},
    "aenderungsmeldung": {"aenderungsart": "Was möchten Sie ändern?"},
}

def get_required_fields(case_type: str) -> dict[str, str]:
    """Feldliste für einen Falltyp. Leeres Dict, wenn unbekannt."""
    ...
```

### Entscheidungen dahinter
- Drei bis fünf Felder pro Typ: Demo-Entscheidung, damit eine Rückfragerunde genügt.
- Betreuung hat auch Pflichtfelder, aber nur EINES: So braucht der Validation-Service keinen Sonderfall, der Ablaufvertrag bleibt konsistent.
- Fachwissen ist Konfiguration: Neue Schadensarten werden als Block hinzugefügt, kein Code-Umbau nötig.

## 11. data/customers.json - vollständiger Inhalt
Einleitung: Das sind keine Testdaten, das sind Präsentationsszenarien.

```json
[
  {"customer_number": "K-1001", "name": "Michael Bauer", "phone": "4917123456789", "email": "michael.bauer@gmx.de", "contracts": [{"contract_number": "V-001", "product": "KFZ Vollkasko", "status": "active", "deductible": 500}]},
  {"customer_number": "K-1002", "name": "Sandra Hoffmann", "phone": "4917234567890", "email": "sandra.hoffmann@gmx.de", "contracts": [{"contract_number": "V-002", "product": "Hausratversicherung", "status": "active", "deductible": 250}]},
  {"customer_number": "K-1003", "name": "Thomas Richter", "phone": "4917345678901", "email": "thomas.richter@gmx.de", "contracts": [{"contract_number": "V-003", "product": "Privathaftpflicht", "status": "active", "deductible": 150}]},
  {"customer_number": "K-1004", "name": "Julia Wagner", "phone": "4917456789012", "email": "julia.wagner@gmx.de", "contracts": [{"contract_number": "V-004", "product": "KFZ Teilkasko", "status": "expired", "deductible": 300}]},
  {"customer_number": "K-1005", "name": "Andreas Klein", "phone": "4917567890123", "email": "andreas.klein@gmx.de", "contracts": [{"contract_number": "V-005", "product": "KFZ Vollkasko", "status": "active", "deductible": 500}, {"contract_number": "V-006", "product": "Hausratversicherung", "status": "active", "deductible": 250}]},
  {"customer_number": "K-1006", "name": "Petra Schulz", "phone": "4917678901234", "email": "petra.schulz@gmx.de", "contracts": [{"contract_number": "V-007", "product": "Wohngebäudeversicherung", "status": "active", "deductible": 1000}]},
  {"customer_number": "K-1007", "name": "Daniel Fischer", "phone": "4917789012345", "email": "daniel.fischer@gmx.de", "contracts": [{"contract_number": "V-008", "product": "Glasversicherung", "status": "active", "deductible": 100}]},
  {"customer_number": "K-1008", "name": "Nicole Weber", "phone": "4917890123456", "email": "nicole.weber@gmx.de", "contracts": [{"contract_number": "V-009", "product": "Hausratversicherung", "status": "active", "deductible": 250}, {"contract_number": "V-010", "product": "Privathaftpflicht", "status": "active", "deductible": 150}]},
  {"customer_number": "K-1009", "name": "Markus Neumann", "phone": "4917901234567", "email": "markus.neumann@gmx.de", "contracts": [{"contract_number": "V-011", "product": "KFZ Vollkasko", "status": "cancelled", "deductible": 500}]},
  {"customer_number": "K-1010", "name": "Christina Vogel", "phone": "4917012345678", "email": "christina.vogel@gmx.de", "contracts": [{"contract_number": "V-012", "product": "Wohngebäudeversicherung", "status": "active", "deductible": 1000}]}
]
```

### Vertragsauswahl in find_active_contract
- kfz_kollision, glasbruch → Produkt enthält "KFZ" oder "Glas"
- wasserschaden, einbruchdiebstahl → Produkt enthält "Hausrat" oder "Wohngebäude"
- haftpflicht → Produkt enthält "Haftpflicht"
- sonst → erster aktiver Vertrag

## 12. Kanal-Adapter
Adapter-Struktur echt, Transport simuliert. Kanal-Unterscheidung existiert an genau zwei Stellen: Adapter (rein) und channel_sender (raus).

```json
# WhatsApp Rohformat
{"from": "4917123456789", "text": {"body": "Hallo, ich hatte gestern einen Unfall."}, "timestamp": "1756645323"}

# E-Mail Rohformat
{"sender": "michael.bauer@gmx.de", "subject": "Schadenmeldung", "body_plain": "Guten Tag, ...", "date": "2026-08-31T14:22:03"}
```

## 13. Infrastruktur
WICHTIGSTER STOLPERSTEIN DES PROJEKTS: Der Build-Context muss . sein, nicht der Service-Ordner. Sonst findet der Build shared/ nicht.


13.1 docker-compose.yml
yaml

services:

  case-service:
    build:
      context: .                                    # MUSS "." sein!
      dockerfile: services/case_service/Dockerfile
    container_name: case-service
    ports:
      - "8000:8000"                                 # nur dieser nach außen
    volumes:
      - ./data:/app/data
    env_file:
      - .env
    environment:
      - PYTHONUNBUFFERED=1
    command: uvicorn services.case_service.main:app --host 0.0.0.0 --port 8000

  classifier-service:
    build:
      context: .
      dockerfile: services/classifier_service/Dockerfile
    container_name: classifier-service
    volumes:
      - ./data:/app/data
    env_file:
      - .env
    environment:
      - PYTHONUNBUFFERED=1
    command: uvicorn services.classifier_service.main:app --host 0.0.0.0 --port 8000

  validation-service:
    build:
      context: .
      dockerfile: services/validation_service/Dockerfile
    container_name: validation-service
    volumes:
      - ./data:/app/data
    env_file:
      - .env
    environment:
      - PYTHONUNBUFFERED=1
    command: uvicorn services.validation_service.main:app --host 0.0.0.0 --port 8000

  damage-service:
    build:
      context: .
      dockerfile: services/damage_service/Dockerfile
    container_name: damage-service
    volumes:
      - ./data:/app/data
    env_file:
      - .env
    environment:
      - PYTHONUNBUFFERED=1
    command: uvicorn services.damage_service.main:app --host 0.0.0.0 --port 8000

  support-service:
    build:
      context: .
      dockerfile: services/support_service/Dockerfile
    container_name: support-service
    volumes:
      - ./data:/app/data
    env_file:
      - .env
    environment:
      - PYTHONUNBUFFERED=1
    command: uvicorn services.support_service.main:app --host 0.0.0.0 --port 8000
Drei Dinge, die hier wichtig sind:


Nur case-service mappt einen Port nach außen. Die anderen vier sind intern über ihren Containernamen erreichbar (http://validation-service:8000) — genau die URLs aus config.py.

container_name muss dem Containernamen in den URLs entsprechen. Sonst findet der HTTP-Call das Ziel nicht.

PYTHONUNBUFFERED=1 bei allen fünf. Ohne das siehst du in der Demo keine Logs.

13.2 Dockerfile (Muster für alle fünf)
dockerfile

FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY shared/ ./shared/
COPY services/case_service/ ./services/case_service/

ENV PYTHONUNBUFFERED=1

CMD ["uvicorn", "services.case_service.main:app", "--host", "0.0.0.0", "--port", "8000"]
Für die anderen vier Services identisch, nur die beiden case_service-Vorkommen austauschen. shared/ wird immer mitkopiert — das ist der Grund für den Build-Context ..

13.3 requirements.txt
fastapi
uvicorn
pydantic
httpx
openai
python-dotenv
pytest
Ein einziges File im Root statt fünf fast identischer pro Service. Alle fünf brauchen ohnehin dasselbe; fünf Dateien zu pflegen, die sich um eine Zeile unterscheiden, führt nur zu Drift.

13.4 .env.example
OPENAI_API_KEY=
OPENAI_MODEL=gpt-5.6-terra

DATA_DIR=/app/data

CASE_SERVICE_URL=http://case-service:8000
CLASSIFIER_SERVICE_URL=http://classifier-service:8000
VALIDATION_SERVICE_URL=http://validation-service:8000
DAMAGE_SERVICE_URL=http://damage-service:8000
SUPPORT_SERVICE_URL=http://support-service:8000
13.5 .gitignore
.env
__pycache__/
*.pyc
.pytest_cache/
data/cases/*.json
data/inbox.jsonl
13.6 Startbefehle
bash

docker compose up              # alle fünf starten, Logs im Vordergrund
docker compose up --build      # nach jeder Änderung in shared/
docker compose down            # stoppen (Fälle bleiben, data/ ist Volume)
Nach jeder Änderung in shared/ ist --build nötig, sonst läuft der alte Stand im Container. Das ist der zweitgrößte Zeitfresser nach dem Build-Context.

## 14. tools/ - die Demo-Werkzeuge
Laufen auf dem Host, nicht im Container. Brauchen nur httpx.

14.1 send_message.py
Baut je nach Kanal das passende Rohformat und POSTet es an POST /inbound/{channel}.

bash

python tools/send_message.py whatsapp 4917123456789 "Ich hatte gestern einen Unfall"
python tools/send_message.py email michael.bauer@gmx.de "Ich möchte einen Wasserschaden melden"
14.2 show_case.py
Zeigt einen Fall lesbar inklusive Dialogprotokoll. messages und outbound werden chronologisch gemischt ausgegeben, mit Pfeilen für Richtung und Empfänger.

bash

python tools/show_case.py 1
Erwartete Ausgabe:

============================================================
 Fall case_0001                          Status: assigned
============================================================
 Absender:   4917123456789 (whatsapp)
 Kategorie:  schaden / kfz_kollision
 Kunde:      K-1001 Michael Bauer
 Vertrag:    V-001 KFZ Vollkasko (aktiv), SB 500 EUR
 Severity:   mittel

 Pflichtangaben:
   schadensdatum    2026-08-30
   schadensort      Kreuzung Hauptstr./Bahnhofstr., Koeln
   schadenshergang  Auffahrunfall an roter Ampel
   kennzeichen      K-AB 1234
   fehlend:         -

------------------------------------------------------------
 DIALOG
------------------------------------------------------------
 14:22:03  <- Kunde (whatsapp)        Hallo, ich hatte gestern
                                      einen Unfall mit meinem Auto.
 14:22:09  -> Kunde (whatsapp)        Guten Tag, fuer die Bearbeitung
                                      fehlen uns noch: Wann ist der
                                      Unfall passiert? Wo ist der
                                      Unfall passiert? ...
 14:26:12  <- Kunde (whatsapp)        Das war am 30.08. an der
                                      Kreuzung Hauptstr./Bahnhofstr.
                                      in Koeln, Auffahrunfall.
 14:26:41  -> Sachbearbeiter (email)  Neuer Schadenfall case_0001 -
                                      kfz_kollision - Severity mittel
 14:26:42  -> Kunde (whatsapp)        Vielen Dank, Ihre Schadenmeldung
                                      ist bei uns eingegangen.
============================================================
14.3 list_cases.py
Tabelle aller Fälle über GET /cases.

bash

python tools/list_cases.py
Fall        Absender               Kategorie   Typ                 Status
--------------------------------------------------------------------------------
case_0001   4917123456789          schaden     kfz_kollision       assigned
case_0002   4917456789012          schaden     kfz_kollision       manual_review
case_0003   petra.schulz@gmx.de    betreuung   auskunft            closed
case_0004   4917890123456          betreuung   aenderungsmeldung   assigned
Demo-Setup: zwei Terminals. Links docker compose up (Logs), rechts die Tools. Das outbound-Protokoll aus show_case.py ist das stärkste Einzelbild der Präsentation, weil es den kompletten Dialog in beide Richtungen zeigt.

## 15. tests/
Nur leere Testfunktionen als Signal, was testbar sein soll. Keine echten Assertions, keine Testpyramide, kein tests/-Ordner pro Service.

python

# tests/test_adapters.py
def test_whatsapp_adapter_maps_sender():
    pass

def test_email_adapter_maps_sender():
    pass

def test_registry_returns_adapter_for_channel():
    pass
python

# tests/test_case_repository.py
def test_case_numbering_is_sequential():
    pass

def test_atomic_write_creates_file():
    pass

def test_inbox_append_adds_line():
    pass
python

# tests/test_case_manager.py
def test_find_open_ignores_terminal_statuses():
    pass

def test_patch_set_overwrites_block():
    pass

def test_patch_append_adds_to_list():
    pass
python

# tests/test_field_catalog.py
def test_get_required_fields_known_type():
    pass

def test_get_required_fields_unknown_type_returns_empty():
    pass
Bei einem Demo-Projekt ohne Fake-LLM sind echte Tests nur für die Adapter und den Case-Store sinnvoll — genau die sind hier die Kandidaten.

## 16. Die sechs Bauphasen
Phase	Auftrag	Prüfkriterium
1	Grundgerüst: Ordnerstruktur, requirements.txt, .env.example, .gitignore, docker-compose.yml, alle fünf Dockerfiles, leere __init__.py	docker compose build läuft durch
2	shared/ komplett, alle acht Dateien	models.py lesen, Datenmodell passt
3	Case-Service (Adapter, Repository, Manager, main.py) plus data/customers.json	Eine Nachricht erzeugt case_0001.json und eine Zeile in inbox.jsonl
4	Klassifikator-Service plus Validation-Service	Fall wird klassifiziert, Vertrag geprüft, Rückfrage erscheint im Terminal
5	Damage-Service plus Support-Service	Alle drei Endzustände erreichbar
6	tools/, tests/, README.md	Vollständiger Demo-Durchlauf
Arbeitsweise:


Plan Mode zuerst — Plan zeigen lassen, noch keinen Code schreiben. Korrigieren ist billiger als zurückrudern.

Nach jeder Phase git commit — dann ist ein Fehlschlag zehn Sekunden Arbeit statt einer Stunde.

/clear zwischen den Phasen, wenn der Kontext voll wird. CLAUDE.md bleibt erhalten, der Code steht im Repo.

docker compose up nicht im Vordergrund von Claude Code starten — der Befehl endet nie und blockiert die Session.

## 17. Argumente für die Präsentation
- "Kanal-Unterscheidung existiert an genau zwei Stellen."
- "CRM lesen ist direkt, Fälle schreiben nur über den Case-Service."
- "Kein Orchestrator - Choreografie per if/else."

## 18. Was bewusst NICHT gebaut wird
Kein Frontend. Kein Orchestrator. Kein Ingress-Container. Kein Outbound-Container. Kein CRM-Container. Keine echte Datenbank (kein PostgreSQL, kein SQLite). Kein Message Broker. Kein Retry, keine Timeouts, kein Error-Handling. Kein Provider-Interface für das LLM. Kein FakeLlmClient. Kein Rückfrage-Limit (kein followup_count). Keine Terminvorschläge für Gutachter. Kein PDF-Report. Keine Vollständigkeitsprüfung bei Änderungsmeldungen. Keine sensiblen Daten wie Bankverbindung. Keine echte Sachbearbeiter-Verfügbarkeitslogik und keine Mapping-Tabelle (feste Adresse schadenteam@axa.de). Kein Caching im CrmClient. Keine Token-Zählung, kein Kostenlogging. Keine pydantic-Modelle für CRM-Daten (rohe Dictionaries). Kein Enum für case_type und awaiting_by. Keine schnelle Webhook-Bestätigung (bewusst synchron). Keine Authentifizierung, keine Rate Limits.

## 19. Entstehungsgeschichte und Begründungen
Dieser Abschnitt hilft beim Bauen nicht — er ist für die Präsentation und Verteidigung.

Ausgangspunkt war ein draw.io-Diagramm mit zwei getrennten Kanalpfaden, einem eigenen Ingress Layer, einer Validierungsschicht, einem LLM-Klassifikator und einem einzigen „Schaden-Agent" mit Terminvorschlägen für Gutachter. Das war nur eine Diskussionsgrundlage, nichts davon war fix. Ziel war von Anfang an, das System auf die wichtigsten Schichten runterzubrechen.

Nebeneffekt fürs Bauen: Wer liest, dass Ingress Layer und Orchestrator bewusst verworfen wurden, baut sie nicht aus Gewohnheit ein.

Ursprünglich	Heute	Begründung
Zwei getrennte Kanalpfade WhatsApp/E-Mail	Ein dünner Adapter pro Kanal, danach einheitliches internes Format	Der Kanal ist ein Feld, keine Struktur — der Rest des Systems kennt ihn nicht mehr strukturell
Ingress Layer als eigener Container	Erster Schritt im Case-Service (Rohdaten vor Verarbeitung)	Die Funktion bleibt zwingend nötig, ein eigener Service dafür nicht
Freier Agent mit Tool-Auswahl	Feste Services mit deterministischem Ablauf	Der Prozess folgt einem festen Ablauf, wie ein Sachbearbeiter ihn abarbeiten würde
Zentraler Orchestrator	Choreografie per if/else in jedem Service	Bei fünf Services ist der verteilte Ablauf kein echtes Risiko und bleibt schlanker
Severity im gemeinsamen Vorbau	Im Damage-Service	Severity ergibt nur beim Schaden Sinn — bei Adressänderung gibt es keine Schwere
Nur Severity-Kategorie	Severity plus kurze LLM-Begründung	Nachvollziehbarkeit gegenüber dem Sachbearbeiter
Separater Terminvorschlags-Mechanismus	Komplett gestrichen	Bei hoher Severity reicht ein Textbaustein in der Mail
Getrennte Prüfungen in beiden Endpfaden	Gemeinsamer Validation-Service vor der Verzweigung	Vermeidet doppelte Logik in Schaden- und Betreuungspfad
Eigener Outbound-Service als Container	channel_sender als geteiltes Modul	Kein Container nötig, aber ein Modul verhindert Code-Duplikation
Case-Erkennung über Telefonnummer allein	Suche nach dem neuesten offenen Fall	Ein Kunde kann mehrere Fälle gehabt haben — abgeschlossene fallen über TERMINAL_STATUSES raus
Klassifikator hinter die Validierung (erwogen)	Reihenfolge nicht getauscht	Der Pflichtangaben-Check braucht Kategorie und Typ für die richtige Feldliste
PostgreSQL (erwogen)	JSON-Dateien, ein Fall eine Datei	Eine sichtbare case_0001.json schlägt eine unsichtbare DB-Tabelle — und spart Migrationen ohne Lerneffekt
crm-mock als sechster Container (erwogen)	CrmClient mit direktem Dateizugriff	Read-only, also kein Grund zu kapseln — ein Container hätte nur HTTP-Boilerplate produziert
Echte WhatsApp API und IMAP/SMTP (erwogen)	Adapter echt, Transport simuliert	Echter Versand würde bedeuten, in der Demo zwischen Terminal, Handy und Postfach zu wechseln
Rückfrage-Limit followup_count (erwogen)	Gestrichen	Die Schleife ist manuell getrieben — eine Endlosschleife kann strukturell nicht entstehen
Dokumentenanforderung, Sentiment-Analyse, Rückrufwunsch, Antwortentwurf (alle erwogen)	Änderungsmeldung (Adresse, Fahrzeugwechsel, Kündigung)	Bewusst ohne sensible Daten, ohne Vollständigkeitsprüfung, ohne Rückfrage-Kreislauf
Weitere bewusste MVP-Vereinfachungen: Kein Retry- oder Fehlerbehandlungskonzept (Annahme für die Demo: es funktioniert). Sachbearbeiter-Zuordnung über eine feste Adresse statt echter Verfügbarkeitslogik oder Mapping-Tabelle.

Happy Path Fokus

## 20. Mockup der Sachbearbeiter-Mail
So sieht die Mail aus, die der Damage-Service in Schritt 5 und 6 baut. Übernimm dieses Format, erfinde kein eigenes.

An:      schadenteam@axa.de
Betreff: Neuer Schadenfall case_0001 - kfz_kollision - Severity mittel

------------------------------------------------------------
FALLDATEN
------------------------------------------------------------
Fall-ID:        case_0001
Eingang:        31.08.2026, 14:22
Kanal:          WhatsApp
Status:         ready_for_assignment

------------------------------------------------------------
KUNDE UND VERTRAG
------------------------------------------------------------
Kundennummer:   K-1001
Name:           Michael Bauer
Vertrag:        V-001
Produkt:        KFZ Vollkasko
Vertragsstatus: aktiv
Selbstbehalt:   500 EUR

------------------------------------------------------------
PFLICHTANGABEN
------------------------------------------------------------
Schadensdatum:    30.08.2026
Schadensort:      Kreuzung Hauptstr./Bahnhofstr., Koeln
Schadenshergang:  Auffahrunfall an roter Ampel
Kennzeichen:      K-AB 1234

------------------------------------------------------------
EINSCHAETZUNG
------------------------------------------------------------
Severity:       mittel
Begruendung:    Sachschaden am Heck, keine Personenschaeden,
                Fahrzeug fahrbereit.

------------------------------------------------------------
ZUSAMMENFASSUNG
------------------------------------------------------------
Der Kunde meldet einen Auffahrunfall vom 30.08.2026 an einer
Kreuzung in Koeln. Das Fahrzeug ist am Heck beschaedigt und
weiterhin fahrbereit. Personenschaeden liegen nicht vor.
Der Vertrag ist aktiv, der Selbstbehalt betraegt 500 EUR.

------------------------------------------------------------
NACHRICHTENVERLAUF
------------------------------------------------------------
[31.08.2026 14:22] Kunde: Hallo, ich hatte gestern einen
                   Unfall mit meinem Auto.
[31.08.2026 14:26] Kunde: Das war am 30.08. an der Kreuzung
                   Hauptstr./Bahnhofstr. in Koeln,
                   Auffahrunfall. Mein Kennzeichen ist
                   K-AB 1234.
Bei severity: hoch kommt im Abschnitt EINSCHÄTZUNG eine Zeile dazu:

------------------------------------------------------------
EINSCHAETZUNG
------------------------------------------------------------
Severity:       hoch
Begruendung:    Personenschaden moeglich, Fahrzeug nicht
                fahrbereit, hoher Sachschaden.

HINWEIS: Aufgrund der hohen Schadenschwere Gutachter-Einsatz
         pruefen.
Mail bei Änderungsmeldungen (Support-Service)
Deutlich kürzer — keine Severity, keine Zusammenfassung. Beides sind Schadenkonzepte.

An:      schadenteam@axa.de
Betreff: Aenderungsmeldung case_0004 - adresse

------------------------------------------------------------
FALLDATEN
------------------------------------------------------------
Fall-ID:        case_0004
Eingang:        31.08.2026, 15:10
Kanal:          WhatsApp

------------------------------------------------------------
KUNDE UND VERTRAG
------------------------------------------------------------
Kundennummer:   K-1008
Name:           Nicole Weber
Vertrag:        V-009
Produkt:        Hausratversicherung
Vertragsstatus: aktiv

------------------------------------------------------------
AENDERUNG
------------------------------------------------------------
Art:            adresse
Neue Strasse:   Lindenweg 12
Neue PLZ:       50667
Neuer Ort:      Koeln
Gueltig ab:     01.10.2026

------------------------------------------------------------
NACHRICHTENVERLAUF
------------------------------------------------------------
[31.08.2026 15:10] Kunde: Guten Tag, ich ziehe zum 01.10.
                   um. Neue Adresse: Lindenweg 12,
                   50667 Koeln.

## 21. Merksätze auf einen Blick
- Datenhoheit ist nicht Ablaufsteuerung.
- Der Print ist für das Publikum, der outbound-Eintrag für den Fall.
- KI gezielt statt dekorativ.