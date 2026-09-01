# Schadenmelde-Service

Ein verteiltes System, das eingehende Kundennachrichten (Schadenmeldungen und
Serviceanfragen) automatisiert vorverarbeitet und aufbereitet an einen Sachbearbeiter
übergibt. Fünf FastAPI-Services in fünf Containern, die sich per Choreografie
gegenseitig aufrufen — es gibt bewusst keinen zentralen Orchestrator.

Alles ist von Scratch gebaut: kein echtes Bestandssystem, keine Datenbank, keine
echten Kommunikationskanäle. Das CRM ist eine JSON-Datei, jeder Fall eine
`case_XXXX.json`, ausgehende Nachrichten erscheinen im Terminal. Uni-MVP für eine
Terminal-Demo, kein Produktivsystem.

## Kontrollfluss

```text
send_message.py -> POST /inbound/{channel} -> Case-Service (Adapter, inbox.jsonl, Fallerkennung)
  -> neu        -> /classify (Klassifikator, setzt category und case_type)
  -> wartet     -> SERVICE_URLS[awaiting_by]
  -> bestehend  -> /validate

/validate (Validation) -> kein Vertrag    -> manual_review
                       -> unvollständig   -> awaiting_customer_reply
                       -> sonst -> Verzweigung:
                          schaden   -> /handle-damage  -> assigned
                          betreuung -> /handle-support -> auskunft          -> closed
                                                       -> aenderungsmeldung -> assigned
```

Drei Endzustände (`assigned`, `manual_review`, `closed`), ein Wartezustand
(`awaiting_customer_reply`).

## Die fünf Services

| Service | Container | Endpoints | Kernaufgabe |
|---|---|---|---|
| Case-Service | `case-service` | `POST /inbound/{channel}`, `GET /cases`, `GET /cases/{id}`, `PATCH /cases/{id}` | Webhook, Kanal-Adapter, Rohnachricht persistieren, Fallerkennung, Datenhoheit |
| Klassifikator | `classifier-service` | `POST /classify` | Nur bei neuem Fall: LLM bestimmt Kategorie und Typ |
| Validation | `validation-service` | `POST /validate` | Bestandsabgleich regelbasiert, Pflichtangaben-Check per LLM, ggf. Rückfrage |
| Damage | `damage-service` | `POST /handle-damage` | Severity plus Begründung, Fallzusammenfassung, Mail an Sachbearbeiter |
| Support | `support-service` | `POST /handle-support` | Auskunft ODER Änderungsmeldung, Mail plus Kundenbestätigung |

Nur der Case-Service ist von außen erreichbar (Port 8000). Die anderen vier sprechen
sich intern über ihre Containernamen an.

Drei Sätze, die die Architektur erklären:

- Die Kanal-Unterscheidung existiert an genau zwei Stellen: im Adapter (rein) und im
  `channel_sender` (raus). Dazwischen ist der Kanal nur ein Feld.
- CRM lesen geht direkt per Dateizugriff, Fälle schreiben ausschließlich über den
  Case-Service. Datenhoheit ist nicht Ablaufsteuerung.
- Kein Orchestrator — jeder Service entscheidet am Ende selbst per `if/else`, wer als
  Nächstes dran ist.

## Setup

```bash
cp .env.example .env
```

In `.env` eintragen:

- `OPENAI_API_KEY` — ohne den Schlüssel bricht der erste LLM-Aufruf ab
- `OPENAI_MODEL` — sonst greift der Fallback aus `shared/config.py`

Die Service-URLs in `.env.example` sind die internen Docker-Adressen und bleiben
unverändert.

## Starten

```bash
docker compose up --build    # alle fünf Container, Logs im Vordergrund
docker compose down          # stoppen (Fälle bleiben, data/ ist ein Volume)
```

Demo-Setup sind zwei Terminals: links läuft `docker compose up` mit den Logs, rechts
die Werkzeuge aus `tools/`. Nach jeder Änderung in `shared/` ist ein `--build` nötig,
sonst läuft im Container der alte Stand.

Vor der ersten Nachricht abwarten, bis alle fünf Container
`Application startup complete` gemeldet haben. Wer früher sendet, bekommt einen
`ConnectError` aus dem Case-Service — es gibt bewusst keinen Retry.

## Demo-Szenarien

Die Werkzeuge laufen auf dem Host gegen `localhost:8000` und brauchen nur `httpx`.

```bash
# 1) KFZ-Kollision, K-1001 Michael Bauer -> Rückfrage -> assigned
python tools/send_message.py whatsapp 4917123456789 "Hallo, ich hatte gestern einen Unfall mit meinem Auto."
python tools/show_case.py 1     # Status: awaiting_customer_reply, Rückfrage im Dialog
python tools/send_message.py whatsapp 4917123456789 "Das war am 30.08.2026 an der Kreuzung Hauptstr./Bahnhofstr. in Koeln. Ein anderes Fahrzeug ist mir an der roten Ampel hinten aufgefahren, Schaden am Heck, Auto faehrt noch. Mein Kennzeichen ist K-AB 1234."
python tools/show_case.py 1     # Status: assigned, Sachbearbeiter-Mail im Dialog

# 2) Abgelaufener Vertrag, K-1004 Julia Wagner -> manual_review
python tools/send_message.py whatsapp 4917456789012 "Ich hatte einen Unfall mit meinem Auto und moechte den Schaden melden."

# 3) Deckungsfrage per E-Mail, K-1006 Petra Schulz -> closed
python tools/send_message.py email petra.schulz@gmx.de "Guten Tag, wie hoch ist mein Selbstbehalt bei der Wohngebaeudeversicherung?"
python tools/show_case.py 3     # kein Sachbearbeiter im Dialog - vollautomatisch beantwortet

# 4) Umzug, K-1008 Nicole Weber -> assigned
python tools/send_message.py whatsapp 4917890123456 "Guten Tag, ich ziehe zum 01.10. um. Meine neue Adresse ist Lindenweg 12, 50667 Koeln."

python tools/list_cases.py
```

Erwartetes Ergebnis:

```text
Fall        Absender               Kategorie   Typ                 Status
--------------------------------------------------------------------------------
case_0001   4917123456789          schaden     kfz_kollision       assigned
case_0002   4917456789012          schaden     kfz_kollision       manual_review
case_0003   petra.schulz@gmx.de    betreuung   auskunft            closed
case_0004   4917890123456          betreuung   aenderungsmeldung   assigned
```

Szenario 1 und 3 sind das stärkste Bild der Präsentation: `show_case.py` zeigt den
kompletten Dialog in beide Richtungen, und bei der Auskunft fehlt der
Sachbearbeiter-Eintrag — weil dort nie einer beteiligt war.

## Werkzeuge

| Befehl | Zweck |
|---|---|
| `python tools/send_message.py <channel> <absender> "<text>"` | Simuliert eine eingehende Nachricht. `channel` ist `whatsapp` oder `email`. Bei E-Mail optional ein Betreff als viertes Argument (Standard: `Nachricht`). |
| `python tools/show_case.py 1` | Zeigt einen Fall lesbar samt Dialogprotokoll. |
| `python tools/list_cases.py` | Tabelle aller Fälle. |

## Wo die Daten liegen

- `data/customers.json` — das simulierte Bestandssystem, read-only, ohne Caching
  (bei laufenden Containern live editierbar)
- `data/cases/case_XXXX.json` — eine Datei je Fall, das einzige Gedächtnis des Systems
- `data/inbox.jsonl` — jede Rohnachricht, append-only, vor jeder Verarbeitung

Fälle und Inbox sind gitignored. Vor der Präsentation `data/cases/*.json` und
`data/inbox.jsonl` löschen, dann startet die Nummerierung wieder bei `case_0001`.

## Tests

```bash
pytest
```

Die Testfunktionen sind bewusst leer. Sie sind ein Signal, was in einem echten Projekt
testbar wäre — Adapter, Case-Repository, Case-Manager und Feldkatalog. Ohne
Fake-LLM-Client wären Tests der Fachservices nur Attrappen.

## Bewusst nicht gebaut

- Kein Frontend, keine Authentifizierung, keine Rate Limits
- Kein Orchestrator, kein Message Broker, kein Ingress- oder Outbound-Container
- Keine echte Datenbank — eine sichtbare `case_0001.json` schlägt eine unsichtbare
  DB-Tabelle
- Kein Retry, keine Timeouts, kein Error-Handling: Fehler sollen in der Demo sichtbar
  brechen
- Kein Provider-Interface und kein Fake-Client für das LLM
- Kein Rückfrage-Limit, keine Vollständigkeitsprüfung bei Änderungsmeldungen, keine
  sensiblen Daten wie Bankverbindungen
