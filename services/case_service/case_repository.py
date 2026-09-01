"""Reiner Dateizugriff auf data/cases/ und data/inbox.jsonl.
Keine Fachlogik - dieses Modul kennt weder Status noch Kategorie."""

import json
import os
from pathlib import Path
from typing import Any

from shared.config import CASES_DIR, INBOX_FILE
from shared.models import Case


class CaseRepository:
    """Kapselt Lesen und Schreiben der Falldateien."""

    def __init__(self, cases_dir: Path = CASES_DIR, inbox_file: Path = INBOX_FILE) -> None:
        self.cases_dir = cases_dir
        self.inbox_file = inbox_file

    def _path(self, case_id: str) -> Path:
        return self.cases_dir / f"{case_id}.json"

    def load(self, case_id: str) -> Case:
        """data/cases/case_XXXX.json -> Case."""
        return Case.model_validate_json(self._path(case_id).read_text(encoding="utf-8"))

    def save(self, case: Case) -> None:
        """Atomar schreiben: erst .tmp, dann umbenennen."""
        ziel = self._path(case.case_id)
        tmp = ziel.with_suffix(".json.tmp")
        tmp.write_text(case.model_dump_json(indent=2), encoding="utf-8")
        os.replace(tmp, ziel)

    def load_all(self) -> list[Case]:
        """Alle Fälle, nach case_id sortiert."""
        return [self.load(p.stem) for p in sorted(self.cases_dir.glob("case_*.json"))]

    def next_case_id(self) -> str:
        """Höchste vorhandene Nummer + 1."""
        nummern = [int(p.stem.split("_")[1]) for p in self.cases_dir.glob("case_*.json")]
        return f"case_{max(nummern, default=0) + 1:04d}"

    def append_inbox(self, raw: dict[str, Any]) -> None:
        """Rohnachricht unverändert an inbox.jsonl anhängen. Append-only."""
        with self.inbox_file.open("a", encoding="utf-8") as datei:
            datei.write(json.dumps(raw, ensure_ascii=False) + "\n")
