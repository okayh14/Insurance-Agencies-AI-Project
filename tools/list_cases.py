"""Tabelle aller Faelle ueber GET /cases.

    python tools/list_cases.py
"""

import httpx

BASE_URL = "http://localhost:8000"

FALL = 12
ABSENDER = 23
KATEGORIE = 12
TYP = 20

antwort = httpx.get(f"{BASE_URL}/cases")
antwort.raise_for_status()

print(
    "Fall".ljust(FALL)
    + "Absender".ljust(ABSENDER)
    + "Kategorie".ljust(KATEGORIE)
    + "Typ".ljust(TYP)
    + "Status"
)
print("-" * 80)

for fall in antwort.json():
    print(
        fall["case_id"].ljust(FALL)
        + fall["sender_id"].ljust(ABSENDER)
        + (fall["category"] or "-").ljust(KATEGORIE)
        + (fall["case_type"] or "-").ljust(TYP)
        + fall["status"]
    )
