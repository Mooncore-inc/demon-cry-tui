"""Экран клиентов: название, сервер, токен."""

from functools import partial

from rich.text import Text
from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.screen import ModalScreen
from textual.widgets import Button, Label, OptionList
from textual.widgets.option_list import Option

from demon_cry_tui.config import (
    Catalog,
    CatalogError,
    Client,
    ConnectionStore,
    SecretStoreError,
)
from demon_cry_tui.screens.dialogs import ClientForm, ClientValues, ConfirmScreen

STORE_ERRORS = (CatalogError, SecretStoreError)


class ClientsScreen(ModalScreen[None]):
    """Список клиентов; Enter делает клиента активным."""

    BINDINGS = [
        ("escape", "close", "Close"),
        ("a", "add", "Add client"),
        ("e", "edit", "Edit"),
        ("d", "delete", "Delete"),
    ]

    BUTTONS = (
        ("Add client", "primary", "add"),
        ("Edit", "default", "edit"),
        ("Delete", "error", "delete"),
        ("Use", "default", "use"),
        ("Close", "default", "close"),
    )

    def __init__(self) -> None:
        super().__init__()
        self.store = ConnectionStore()
        self.catalog = Catalog()

    def compose(self) -> ComposeResult:
        with Vertical(id="clients-dialog"):
            yield Label("Clients", classes="dialog-title")
            yield Label(f"keyring: {self.store.backend}", classes="dialog-hint")
            yield OptionList(id="clients-list")
            with Horizontal(id="clients-actions"):
                for label, variant, action in self.BUTTONS:
                    yield Button(label, variant=variant, id=f"clients-{action}")

    def on_mount(self) -> None:
        self._reload()
        self.options.focus()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        handlers = {
            "add": self.action_add,
            "edit": self.action_edit,
            "delete": self.action_delete,
            "use": self.action_use,
            "close": self.action_close,
        }
        action = (event.button.id or "").removeprefix("clients-")
        handler = handlers.get(action)
        if handler is not None:
            handler()

    def on_option_list_option_selected(self, event: OptionList.OptionSelected) -> None:
        event.stop()
        if event.option.id is not None:
            self._activate(event.option.id)

    def action_close(self) -> None:
        self.dismiss()

    def action_use(self) -> None:
        client = self._highlighted()
        if client is None:
            self.notify("Select a client first", severity="warning", timeout=3)
            return
        self._activate(client.id)

    def action_add(self) -> None:
        self.app.push_screen(ClientForm("New client"), self._add)

    def action_edit(self) -> None:
        client = self._highlighted()
        if client is None:
            self.notify("Select a client first", severity="warning", timeout=3)
            return
        self.app.push_screen(
            ClientForm(
                "Edit client",
                name=client.name,
                api_url=client.api_url,
                token=self._token(client.id),
            ),
            partial(self._edit, client.id),
        )

    def action_delete(self) -> None:
        client = self._highlighted()
        if client is None:
            self.notify("Select a client first", severity="warning", timeout=3)
            return
        self.app.push_screen(
            ConfirmScreen(f"Delete client '{client.name}'?"),
            partial(self._delete, client.id),
        )

    def _add(self, values: ClientValues | None) -> None:
        if values is None:
            return
        try:
            client = self.store.add_client(*values)
        except STORE_ERRORS as exc:
            self._error(exc)
            return
        self._reload(select_id=client.id)

    def _edit(self, client_id: str, values: ClientValues | None) -> None:
        if values is None:
            return
        try:
            self.store.update_client(client_id, *values)
        except STORE_ERRORS as exc:
            self._error(exc)
            return
        self._reload(select_id=client_id)

    def _delete(self, client_id: str, confirmed: bool) -> None:
        if not confirmed:
            return
        try:
            self.store.delete_client(client_id)
        except STORE_ERRORS as exc:
            self._error(exc)
            return
        self._reload()

    def _activate(self, client_id: str) -> None:
        try:
            self.store.set_active(client_id)
        except STORE_ERRORS as exc:
            self._error(exc)
            return
        self.dismiss()

    def _error(self, exc: Exception) -> None:
        self.notify(str(exc), severity="error", timeout=8)

    @property
    def options(self) -> OptionList:
        return self.query_one("#clients-list", OptionList)

    def _highlighted(self) -> Client | None:
        option = self.options.highlighted_option
        if option is None or option.id is None:
            return None
        return self.catalog.client(option.id)

    def _token(self, client_id: str) -> str:
        try:
            return self.store.token(client_id)
        except SecretStoreError:
            return ""

    def _reload(self, select_id: str | None = None) -> None:
        try:
            self.catalog = self.store.load()
        except STORE_ERRORS as exc:
            self._error(exc)
            self.catalog = Catalog()

        options = self.options
        options.clear_options()
        options.add_options(
            Option(
                _client_label(
                    client,
                    client.id == self.catalog.active_id,
                    bool(self._token(client.id)),
                ),
                id=client.id,
            )
            for client in self.catalog.clients
        )

        target = select_id or self.catalog.active_id
        index = next(
            (
                position
                for position, client in enumerate(self.catalog.clients)
                if client.id == target
            ),
            0,
        )
        if self.catalog.clients:
            options.highlighted = index


def _client_label(client: Client, active: bool, has_token: bool) -> Text:
    label = Text("» " if active else "  ", style="bold")
    label.append(client.name, style="bold")
    label.append(f"  {client.api_url}", style="dim")
    if not has_token:
        label.append("  (no token)", style="dim")
    return label
