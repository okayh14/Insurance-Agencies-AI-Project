"""Reine Fachkonfiguration: welche Angaben braucht welcher Falltyp.

Technischer Feldname fuer die Logik, Klartextfrage fuer die Kundenrueckfrage.
Neue Schadensarten kommen als Block dazu, ohne Code-Umbau."""

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
    return FIELD_CATALOG.get(case_type, {})
