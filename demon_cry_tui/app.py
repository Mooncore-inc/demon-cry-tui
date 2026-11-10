from textual.app import App, ComposeResult
from textual.containers import Center, Middle, Vertical
from textual.widgets import Footer, Header, Label

from demon_cry_tui.config import (
    CatalogError,
    ConnectionStore,
    SecretStoreError,
    load_config,
)
from demon_cry_tui.screens import ClientsScreen

STORE_ERRORS = (CatalogError, SecretStoreError)


class DemonCryApp(App[None]):
    """Minimal shell for the DemonCry TUI."""

    TITLE = "demon-cry-tui"
    SUB_TITLE = "terminal UI for demon cry core"
    CSS_PATH = "styles/app.tcss"
    BINDINGS = [
        ("ctrl+q", "quit", "Quit"),
        ("ctrl+s", "clients", "Clients"),
    ]

    def __init__(self) -> None:
        super().__init__()
        self.config = load_config()
        self.connections = ConnectionStore()

    def compose(self) -> ComposeResult:
        yield Header()
        with Center(), Middle(), Vertical(id="placeholder"):
            yield Label("DemonCry TUI")
            yield Label("API/backend not wired yet", classes="hint")
            yield Label(id="client-status")
            yield Label(id="token-status", classes="hint")
            yield Label(id="keyring-status", classes="hint")
        yield Footer()

    def on_mount(self) -> None:
        self._refresh()
        try:
            empty = not self.connections.load().clients
        except STORE_ERRORS:
            return
        if empty:
            self.call_after_refresh(self.action_clients)

    def action_clients(self) -> None:
        self.push_screen(ClientsScreen(), callback=lambda _: self._refresh())

    def _refresh(self) -> None:
        status = self.query_one("#client-status", Label)
        token = self.query_one("#token-status", Label)
        keyring = self.query_one("#keyring-status", Label)
        keyring.update(f"keyring: {self.connections.backend}")

        try:
            active = self.connections.active()
        except STORE_ERRORS as exc:
            status.update("No active client")
            token.update("")
            self.notify(str(exc), severity="error", timeout=8)
            return

        if active is None:
            status.update("No active client — press ctrl+s")
            token.update("")
            return

        status.update(f"Client: {active.client.name} — {active.client.api_url}")
        state = "set" if active.token else "missing"
        token.update(f"Token: {state}")


def run() -> None:
    DemonCryApp().run()
