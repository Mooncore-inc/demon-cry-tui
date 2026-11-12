from urllib.parse import urlsplit

import httpx
from textual import work
from textual.app import App, ComposeResult
from textual.containers import Horizontal, Vertical
from textual.widgets import Footer, Header, Label

from demon_cry_tui.api import DemonCryAPI, DemonCryAPIError
from demon_cry_tui.config import (
    ActiveClient,
    CatalogError,
    ConnectionStore,
    SecretStoreError,
    load_config,
)
from demon_cry_tui.screens import ClientsScreen, NamePrompt
from demon_cry_tui.widgets import Sidebar

STORE_ERRORS = (CatalogError, SecretStoreError)


class DemonCryApp(App[None]):
    """Minimal shell for the DemonCry TUI."""

    TITLE = "demon-cry-tui"
    SUB_TITLE = "terminal UI for demon cry core"
    CSS_PATH = "styles/app.tcss"
    BINDINGS = [
        ("ctrl+q", "quit", "Quit"),
        ("ctrl+s", "clients", "Clients"),
        ("ctrl+r", "refresh", "Refresh"),
        ("ctrl+n", "new_investigate", "New investigation"),
    ]

    def __init__(self) -> None:
        super().__init__()
        self.config = load_config()
        self.connections = ConnectionStore()

    def compose(self) -> ComposeResult:
        yield Header()
        with Horizontal(id="main"):
            yield Sidebar()
            with Vertical(id="content"):
                yield Label("DemonCry TUI", id="content-title")
                yield Label(
                    "Select an investigation", id="content-hint", classes="hint"
                )
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

    def action_refresh(self) -> None:
        self._refresh()

    def action_new_investigate(self) -> None:
        active = self._active()
        if active is None or not active.token:
            self.notify("No active client with token", severity="warning", timeout=4)
            return
        self.push_screen(
            NamePrompt("New investigation", placeholder="project"),
            self._new_investigate,
        )

    def on_sidebar_selected(self, event: Sidebar.Selected) -> None:
        investigate = event.investigate
        self.query_one("#content-title", Label).update(investigate.name)
        self.query_one("#content-hint", Label).update(
            f"Investigation #{investigate.id}"
        )

    def on_sidebar_add_requested(self, _event: Sidebar.AddRequested) -> None:
        self.action_new_investigate()

    @property
    def sidebar(self) -> Sidebar:
        return self.query_one(Sidebar)

    def _refresh(self) -> None:
        keyring = self.query_one("#keyring-status", Label)
        keyring.update(f"keyring: {self.connections.backend}")

        active = self._active()
        if active is None:
            self.sidebar.set_client("no client — ctrl+s")
            self.sidebar.set_hint("")
            self._load_investigations()
            return

        host = urlsplit(active.client.api_url).netloc or active.client.api_url
        self.sidebar.set_client(f"{host} | {active.client.name}")
        self._load_investigations()

    @work(exclusive=True)
    async def _load_investigations(self) -> None:
        await self.sidebar.clear()

        active = self._active()
        if active is None:
            return
        if not active.token:
            self.sidebar.set_hint("client has no token")
            return

        self.sidebar.set_hint("loading…")
        try:
            async with DemonCryAPI(
                active.client.api_url,
                active.token,
                self.config.request_timeout,
            ) as api:
                investigations = await api.list_investigates()
        except (DemonCryAPIError, httpx.HTTPError) as exc:
            self.sidebar.set_hint("failed to load")
            self._notify_error(exc)
            return

        await self.sidebar.show(investigations)

    def _new_investigate(self, name: str | None) -> None:
        if name:
            self._create_investigate(name)

    @work(exclusive=True)
    async def _create_investigate(self, name: str) -> None:
        active = self._active()
        if active is None or not active.token:
            self.notify("No active client with token", severity="warning", timeout=4)
            return

        try:
            async with DemonCryAPI(
                active.client.api_url,
                active.token,
                self.config.request_timeout,
            ) as api:
                investigate = await api.create_investigate(name)
        except (DemonCryAPIError, httpx.HTTPError) as exc:
            self._notify_error(exc)
            return

        self.notify(f"Created #{investigate.id} {investigate.name}")
        self._load_investigations()

    def _active(self) -> ActiveClient | None:
        try:
            return self.connections.active()
        except STORE_ERRORS as exc:
            self._notify_error(exc)
            return None

    def _notify_error(self, exc: Exception) -> None:
        message = str(exc)
        if "WRONG_VERSION_NUMBER" in message:
            message += " — server looks like plain HTTP, use http:// in the client URL"
        self.notify(message, severity="error", timeout=10)


def run() -> None:
    DemonCryApp().run()
