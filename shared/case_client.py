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
        antwort = httpx.get(f"{self.base_url}/cases/{case_id}")
        antwort.raise_for_status()
        return Case.model_validate(antwort.json())

    def set_fields(self, case_id: str, values: dict) -> Case:
        """PATCH mit {"set": values}. Überschreibt Felder."""
        antwort = httpx.patch(f"{self.base_url}/cases/{case_id}", json={"set": values})
        antwort.raise_for_status()
        return Case.model_validate(antwort.json())

    def append_to(self, case_id: str, list_name: str, item: dict) -> Case:
        """PATCH mit {"append": {list_name: item}}. Hängt an eine Liste an."""
        antwort = httpx.patch(
            f"{self.base_url}/cases/{case_id}", json={"append": {list_name: item}}
        )
        antwort.raise_for_status()
        return Case.model_validate(antwort.json())
