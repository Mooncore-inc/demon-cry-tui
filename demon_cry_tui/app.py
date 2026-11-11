from urllib.parse import urlsplit

import httpx
from textual import work
from textual.app import App, ComposeResult
from textual.containers import Horizontal, Vertical
from textual.widgets import Footer, Header, Label, ListItem, ListView, Rule

from demon_cry_tui.api import DemonCryAPI, DemonCryAPIError, Investigate
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
        ("ctrl+r", "refresh", "Refresh"),
    ]

    def __init__(self) -> None:
        super().__init__()
        self.config = load_config()
        self.connections = ConnectionStore()
        self.investigations: list[Investigate] = []

    def compose(self) -> ComposeResult:
        yield Header()
        with Horizontal(id="main"):
            with Vertical(id="sidebar"):
                yield Label("Investigations", id="sidebar-title")
                yield Label(id="client-status", classes="hint")
                yield Label(id="sidebar-hint", classes="hint")
                yield Rule(id="sidebar-rule")
                yield ListView(id="investigations")
            with Vertical(id="content"):
                yield Label("DemonCry TUI", id="content-title")
                yield Label(
                    "Select an investigation", id="content-hint", classes="hint"
                )
                yield Label(id="keyring-status", classes="hint")
        yield Footer()

    def on_mount(self) -> None:
        self._refresh()
        self.query_one("#investigations", ListView).focus()
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

    def on_list_view_selected(self, event: ListView.Selected) -> None:
        if not 0 <= event.index < len(self.investigations):
            return
        investigate = self.investigations[event.index]
        self.query_one("#content-title", Label).update(investigate.name)
        self.query_one("#content-hint", Label).update(
            f"Investigation #{investigate.id}"
        )

    def _refresh(self) -> None:
        status = self.query_one("#client-status", Label)
        keyring = self.query_one("#keyring-status", Label)
        keyring.update(f"keyring: {self.connections.backend}")

        try:
            active = self.connections.active()
        except STORE_ERRORS as exc:
            status.update("no client")
            self._notify_error(exc)
            return

        if active is None:
            status.update("no client — ctrl+s")
            self._set_hint("")
            self._load_investigations()
            return

        host = urlsplit(active.client.api_url).netloc or active.client.api_url
        status.update(f"{host} | {active.client.name}")
        self._load_investigations()

    @work(exclusive=True)
    async def _load_investigations(self) -> None:
        await self._clear_investigations()

        try:
            active = self.connections.active()
        except STORE_ERRORS as exc:
            self._notify_error(exc)
            return
        if active is None:
            return
        if not active.token:
            self._set_hint("client has no token")
            return

        self._set_hint("loading…")
        try:
            async with DemonCryAPI(
                active.client.api_url,
                active.token,
                self.config.request_timeout,
            ) as api:
                investigations = await api.list_investigates()
        except (DemonCryAPIError, httpx.HTTPError) as exc:
            self._set_hint("failed to load")
            self._notify_error(exc)
            return

        self.investigations = investigations
        if not investigations:
            self._set_hint("no investigations")
            return

        await self.query_one("#investigations", ListView).extend(
            ListItem(Label(f"#{investigate.id} {investigate.name}"))
            for investigate in investigations
        )
        self.query_one("#investigations", ListView).index = 0
        self._set_hint(f"{len(investigations)} total")

    async def _clear_investigations(self) -> None:
        self.investigations = []
        await self.query_one("#investigations", ListView).clear()

    def _notify_error(self, exc: Exception) -> None:
        message = str(exc)
        if "WRONG_VERSION_NUMBER" in message:
            message += " — server looks like plain HTTP, use http:// in the client URL"
        self.notify(message, severity="error", timeout=10)

    def _set_hint(self, text: str) -> None:
        self.query_one("#sidebar-hint", Label).update(text)


def run() -> None:
    DemonCryApp().run()
