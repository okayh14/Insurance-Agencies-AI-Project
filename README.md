# Kurzbeschreibung

Ein verteiltes System, das eingehende Kundennachrichten per WhatsApp oder E-Mail
automatisiert verarbeitet, von der ersten Nachricht bis zur fertig aufbereiteten
Übergabe an einen Sachbearbeiter oder einer vollautomatischen Antwort an den Kunden.

Fünf FastAPI-Services übernehmen dabei je einen Schritt: Ein Case-Service nimmt die
Nachricht entgegen und verwaltet den Fall, ein Klassifikator bestimmt per LLM Kategorie
und Falltyp, ein Validation-Service prüft den Kundenvertrag und fragt bei fehlenden
Angaben automatisch beim Kunden nach, und je nach Anliegen übernimmt entweder der
Damage-Service (Schadenfälle: Schwere-Einschätzung, Fallzusammenfassung, Mail an den
Sachbearbeiter) oder der Support-Service (Auskünfte werden direkt beantwortet,
Änderungsmeldungen gehen an den Sachbearbeiter).

Es gibt bewusst keinen zentralen Orchestrator: Jeder Service entscheidet selbst, an
wen er als Nächstes übergibt. Die Services rufen sich per HTTP gegenseitig auf
("Choreografie"). Ein Fall kann in einem von vier Zuständen enden: automatisch
zugewiesen (`assigned`), automatisch abgeschlossen ohne menschliches Zutun (`closed`),
zur manuellen Prüfung eskaliert (`manual_review`), oder er wartet auf eine Antwort
des Kunden (`awaiting_customer_reply`).

Alles ist von Grund auf simuliert: kein echtes Bestandssystem, keine Datenbank, keine
echten Kommunikationskanäle. Das CRM ist eine einzige JSON-Datei, jeder Fall eine
eigene `case_XXXX.json`, und ausgehende Nachrichten (an Kunden wie an den
Sachbearbeiter) erscheinen lesbar im Terminal statt tatsächlich verschickt zu werden.
Ein MVP für eine Terminal-Demo, kein Produktivsystem.

## Architektur

- Die Kanal-Unterscheidung existiert an genau zwei Stellen: im Adapter (rein) und im
  `channel_sender` (raus). Dazwischen ist der Kanal nur ein Feld.
- CRM lesen geht direkt per Dateizugriff, Fälle schreiben ausschließlich über den
  Case-Service. Datenhoheit ist nicht Ablaufsteuerung.
- Kein Orchestrator — jeder Service entscheidet am Ende selbst per `if/else`, wer als
  Nächstes dran ist.

| Service | Container | Endpoints | Kernaufgabe |
|---|---|---|---|
| Case-Service | `case-service` | `POST /inbound/{channel}`, `GET /cases`, `GET /cases/{id}`, `PATCH /cases/{id}` | Webhook, Kanal-Adapter, Rohnachricht persistieren, Fallerkennung, Datenhoheit |
| Klassifikator | `classifier-service` | `POST /classify` | Nur bei neuem Fall: LLM bestimmt Kategorie und Typ |
| Validation | `validation-service` | `POST /validate` | Bestandsabgleich regelbasiert, Pflichtangaben-Check per LLM, ggf. Rückfrage |
| Damage | `damage-service` | `POST /handle-damage` | Severity plus Begründung, Fallzusammenfassung, Mail an Sachbearbeiter |
| Support | `support-service` | `POST /handle-support` | Auskunft ODER Änderungsmeldung, Mail plus Kundenbestätigung |

Nur der Case-Service ist von außen erreichbar (Port 8000). Die anderen vier sprechen
sich intern über ihre Containernamen an.

## Voraussetzungen

- Docker Desktop mit `docker compose` — die fünf Services laufen ausschließlich in
  Containern
- Python 3.12 auf dem Host für die Skripte in `tools/`. Die brauchen nur `httpx` und
  sprechen `localhost:8000` an, nicht die internen Docker-Adressen.
- Ein OpenAI-API-Key. Ohne ihn läuft der Case-Service zwar an, aber der erste
  LLM-Aufruf im Klassifikator bricht ab.

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
`ConnectError` aus dem Case-Service. Es gibt bewusst keinen Retry.

## Demo-Szenarien

Die Werkzeuge laufen auf dem Host gegen `localhost:8000` und brauchen nur `httpx`.

```bash
# 1) KFZ-Kollision, K-1001 Michael Bauer
python tools/send_message.py whatsapp 4917123456789 "Hallo, ich hatte gestern einen Unfall mit meinem Auto."
python tools/show_case.py 1     # Status: awaiting_customer_reply, Rückfrage im Dialog
python tools/send_message.py whatsapp 4917123456789 "Das war am 30.08.2026 an der Kreuzung Hauptstr./Bahnhofstr. in Koeln. Ein anderes Fahrzeug ist mir an der roten Ampel hinten aufgefahren, Schaden am Heck, Auto faehrt noch. Mein Kennzeichen ist K-AB 1234."
python tools/show_case.py 1     # Status: assigned, Sachbearbeiter-Mail im Dialog

# 2) Abgelaufener Vertrag, K-1004 Julia Wagner
python tools/send_message.py whatsapp 4917456789012 "Ich hatte einen Unfall mit meinem Auto und moechte den Schaden melden."

# 3) Deckungsfrage per E-Mail, K-1006 Petra Schulz 
python tools/send_message.py email petra.schulz@gmx.de "Guten Tag, wie hoch ist mein Selbstbehalt bei der Wohngebaeudeversicherung?"
python tools/show_case.py 3     # kein Sachbearbeiter im Dialog - vollautomatisch beantwortet

# 4) Umzug, K-1008 Nicole Weber
python tools/send_message.py whatsapp 4917890123456 "Guten Tag, ich ziehe zum 01.10. um. Meine neue Adresse ist Lindenweg 12, 50667 Koeln."

python tools/list_cases.py
```
Alle Befehle laufen in **Terminal 2** (rechts), während in **Terminal 1** (links)
`docker compose up --build` durchgehend mitläuft und die Verarbeitung live zeigt.
Jede Zeile einzeln einfügen und abwarten, bis sie fertig ist, bevor die nächste folgt —
`send_message.py` liefert erst eine Antwort, wenn der Fall komplett durch alle
beteiligten Services gelaufen ist

Erwartetes Ergebnis:

```text
Fall        Absender               Kategorie   Typ                 Status
--------------------------------------------------------------------------------
case_0001   4917123456789          schaden     kfz_kollision       assigned
case_0002   4917456789012          schaden     kfz_kollision       manual_review
case_0003   petra.schulz@gmx.de    betreuung   auskunft            closed
case_0004   4917890123456          betreuung   aenderungsmeldung   assigned
```

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
testbar wäre — Adapter, Case-Repository, Case-Manager und Feldkatalog.
