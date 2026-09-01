"""Einheitliche Terminal-Ausgabe. Ersetzt print() im ganzen Projekt."""

from datetime import datetime

# Feste Breiten, damit die vier Bloecke Spalten bilden.
SERVICE_WIDTH = 12
TAG_WIDTH = 13
OUTBOUND_PREVIEW = 60
SEPARATOR_WIDTH = 78
MAIL_PREFIX = "  | "


class ServiceLogger:
    """Ein Logger pro Service. Kennt seinen Namen, damit der
    Aufrufer ihn nicht bei jedem Aufruf mitgeben muss."""

    def __init__(self, service_name: str) -> None:
        self.service_name = service_name

    def _emit(self, tag: str, message: str) -> None:
        """Baut [zeit] [service] [tag] message und printet mit flush=True."""
        zeit = datetime.now().strftime("%H:%M:%S")
        service = f"[{self.service_name}]".ljust(SERVICE_WIDTH)
        tag_block = f"[{tag}]".ljust(TAG_WIDTH)
        print(f"[{zeit}] {service} {tag_block} {message}", flush=True)

    # --- normale Schritte ---
    def step(self, case_id: str, message: str) -> None:
        """Ein fachlicher Schritt innerhalb eines Falls."""
        self._emit(case_id, message)

    def decision(self, case_id: str, message: str) -> None:
        """Eine Weiche/Entscheidung. Optisch hervorgehoben."""
        self._emit(case_id, f">> {message}")

    # --- Systemgrenzen ---
    def crm(self, message: str) -> None:
        """Zugriff auf das Bestandssystem."""
        self._emit("CRM", message)

    def llm(self, message: str) -> None:
        """LLM-Aufruf."""
        self._emit("LLM", message)

    def outbound(self, channel: str, address: str, text: str) -> None:
        """Ausgehende Nachricht."""
        einzeilig = " ".join(text.split())
        if len(einzeilig) > OUTBOUND_PREVIEW:
            einzeilig = einzeilig[:OUTBOUND_PREVIEW].rstrip() + "..."
        self._emit(f"-> {channel.upper()} an {address}", einzeilig)

    def mail_body(self, text: str) -> None:
        """Vollen Mailtext als Block ausgeben. Bewusst ohne _emit(),
        damit das Spaltenformat der normalen Zeilen unangetastet bleibt."""
        for zeile in text.splitlines():
            print(f"{MAIL_PREFIX}{zeile}", flush=True)

    def next_service(self, target: str) -> None:
        """Weiterleitung an den nächsten Service (Choreografie sichtbar machen)."""
        self._emit("-> NEXT", target)

    def separator(self, message: str = "") -> None:
        """Trennlinie bei neuer eingehender Nachricht."""
        linie = "=" * SEPARATOR_WIDTH
        print(f"\n{linie}", flush=True)
        if message:
            print(f"  {message}", flush=True)
            print(linie, flush=True)


def get_logger(service_name: str) -> ServiceLogger:
    """Wird in jeder main.py einmal aufgerufen."""
    return ServiceLogger(service_name)
