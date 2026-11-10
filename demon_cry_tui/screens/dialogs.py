"""Модальные диалоги: форма клиента и подтверждение."""

from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.screen import ModalScreen
from textual.widgets import Button, Input, Label

ClientValues = tuple[str, str, str]


class ClientForm(ModalScreen[ClientValues | None]):
    """Название, сервер и токен. Dismiss: значения или None при отмене."""

    BINDINGS = [("escape", "cancel", "Cancel")]

    def __init__(
        self,
        title: str,
        *,
        name: str = "",
        api_url: str = "",
        token: str = "",
    ) -> None:
        super().__init__()
        self._title = title
        self._name = name
        self._api_url = api_url
        self._token = token

    def compose(self) -> ComposeResult:
        with Vertical(id="form-dialog"):
            yield Label(self._title, classes="dialog-title")

            yield Label("Name")
            yield Input(value=self._name, placeholder="personal", id="form-name")

            yield Label("API URL")
            yield Input(
                value=self._api_url,
                placeholder="https://cry.example.com",
                id="form-url",
            )

            yield Label("API token")
            yield Input(
                value=self._token,
                password=True,
                placeholder="optional",
                id="form-token",
            )

            with Horizontal(id="form-actions"):
                yield Button("Cancel", id="form-cancel")
                yield Button("Save", variant="primary", id="form-save")

    def on_mount(self) -> None:
        field = self.query_one("#form-name", Input)
        field.focus()
        field.cursor_position = len(field.value)

    def on_input_submitted(self, event: Input.Submitted) -> None:
        event.stop()
        self.submit()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "form-save":
            self.submit()
        else:
            self.action_cancel()

    def action_cancel(self) -> None:
        self.dismiss(None)

    def submit(self) -> None:
        name = self.query_one("#form-name", Input).value.strip()
        api_url = self.query_one("#form-url", Input).value.strip()
        token = self.query_one("#form-token", Input).value.strip()
        if not name or not api_url:
            self.notify("Name and API URL are required", severity="warning", timeout=3)
            return
        self.call_after_refresh(self._close, (name, api_url, token))

    def _close(self, values: ClientValues) -> None:
        self.dismiss(values)


class ConfirmScreen(ModalScreen[bool]):
    """Подтверждение действия."""

    BINDINGS = [
        ("escape", "cancel", "Cancel"),
        ("n", "cancel", "No"),
        ("y", "confirm", "Yes"),
    ]

    def __init__(self, message: str, *, confirm_label: str = "Delete") -> None:
        super().__init__()
        self._message = message
        self._confirm_label = confirm_label

    def compose(self) -> ComposeResult:
        with Vertical(id="confirm-dialog"):
            yield Label(self._message, id="confirm-message")
            with Horizontal(id="confirm-actions"):
                yield Button("Cancel", id="confirm-cancel")
                yield Button(self._confirm_label, variant="error", id="confirm-ok")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        self.dismiss(event.button.id == "confirm-ok")

    def action_cancel(self) -> None:
        self.dismiss(False)

    def action_confirm(self) -> None:
        self.dismiss(True)
