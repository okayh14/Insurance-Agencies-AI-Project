"""Simuliertes Bestandssystem. Liest data/customers.json, read-only."""

import json
from typing import Any

from shared.config import CUSTOMERS_FILE

# Zuordnung Falltyp -> Produkt. Siehe CLAUDE.md Abschnitt 11.
# Falltypen ohne Eintrag bekommen den ersten aktiven Vertrag.
PRODUCT_KEYWORDS: dict[str, tuple[str, ...]] = {
    "kfz_kollision": ("KFZ", "Glas"),
    "glasbruch": ("KFZ", "Glas"),
    "wasserschaden": ("Hausrat", "Wohngebäude"),
    "einbruchdiebstahl": ("Hausrat", "Wohngebäude"),
    "haftpflicht": ("Haftpflicht",),
}


class CrmClient:
    """Kapselt den Dateizugriff auf die Kundendaten."""

    def __init__(self, customers_file=CUSTOMERS_FILE) -> None:
        self.customers_file = customers_file

    def _load(self) -> list[dict[str, Any]]:
        """Liest die JSON-Datei bei jedem Zugriff neu.
        Kein Caching - dann kannst du in der Demo live editieren."""
        return json.loads(self.customers_file.read_text(encoding="utf-8"))

    def find_by_identifier(self, identifier: str) -> dict[str, Any] | None:
        """Sucht Kunden über Telefonnummer oder E-Mail.
        Unterscheidung über das Vorhandensein von '@'."""
        feld = "email" if "@" in identifier else "phone"
        for kunde in self._load():
            if kunde[feld] == identifier:
                return kunde
        return None

    def find_active_contract(
        self, customer: dict[str, Any], case_type: str | None = None
    ) -> dict[str, Any] | None:
        """Gibt den passenden aktiven Vertrag zurück.
        Zuordnung Falltyp -> Produkt siehe Teil 2, Abschnitt 11."""
        aktive = [v for v in customer["contracts"] if v["status"] == "active"]
        if not aktive:
            return None

        keywords = PRODUCT_KEYWORDS.get(case_type)
        if keywords is None:
            return aktive[0]

        for vertrag in aktive:
            if any(k in vertrag["product"] for k in keywords):
                return vertrag
        return None
