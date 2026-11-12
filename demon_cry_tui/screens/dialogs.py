"""Модальные диалоги: формы клиента, сущности, инструмента и подтверждение."""

import json
from typing import Any

from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.screen import ModalScreen
from textual.widgets import Button, Input, Label, Select, SelectionList
from textual.widgets.selection_list import Selection

ClientValues = tuple[str, str, str]
EntityValues = tuple[str, str, str]
EntityEditValues = tuple[str | None, dict[str, Any]]


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


class EntityForm(ModalScreen[EntityValues | None]):
    """Value, type и label сущности. Dismiss: значения или None при отмене."""

    BINDINGS = [("escape", "cancel", "Cancel")]

    def __init__(self, title: str) -> None:
        super().__init__()
        self._title = title

    def compose(self) -> ComposeResult:
        with Vertical(id="form-dialog"):
            yield Label(self._title, classes="dialog-title")

            yield Label("Value")
            yield Input(placeholder="example.com", id="entity-value")

            yield Label("Type")
            yield Input(placeholder="domain, optional", id="entity-type")

            yield Label("Label")
            yield Input(placeholder="optional", id="entity-label")

            with Horizontal(id="form-actions"):
                yield Button("Cancel", id="form-cancel")
                yield Button("Create", variant="primary", id="form-save")

    def on_mount(self) -> None:
        self.query_one("#entity-value", Input).focus()

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
        value = self.query_one("#entity-value", Input).value.strip()
        type_ = self.query_one("#entity-type", Input).value.strip()
        label = self.query_one("#entity-label", Input).value.strip()
        if not value:
            self.notify("Value is required", severity="warning", timeout=3)
            return
        self.call_after_refresh(self._close, (value, type_, label))

    def _close(self, values: EntityValues) -> None:
        self.dismiss(values)


class NamePrompt(ModalScreen[str | None]):
    """Ввод одного имени. Dismiss: строка или None при отмене."""

    BINDINGS = [("escape", "cancel", "Cancel")]

    def __init__(self, title: str, *, value: str = "", placeholder: str = "") -> None:
        super().__init__()
        self._title = title
        self._value = value
        self._placeholder = placeholder

    def compose(self) -> ComposeResult:
        with Vertical(id="form-dialog"):
            yield Label(self._title, classes="dialog-title")
            yield Label("Name")
            yield Input(
                value=self._value, placeholder=self._placeholder, id="name-input"
            )
            with Horizontal(id="form-actions"):
                yield Button("Cancel", id="form-cancel")
                yield Button("Create", variant="primary", id="form-save")

    def on_mount(self) -> None:
        field = self.query_one("#name-input", Input)
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
        name = self.query_one("#name-input", Input).value.strip()
        if not name:
            self.notify("Name is required", severity="warning", timeout=3)
            return
        self.call_after_refresh(self._close, name)

    def _close(self, name: str) -> None:
        self.dismiss(name)


class EntityEditForm(ModalScreen[EntityEditValues | None]):
    """Label и data (JSON) сущности."""

    BINDINGS = [("escape", "cancel", "Cancel")]

    def __init__(
        self,
        title: str,
        *,
        label: str | None,
        data: dict[str, Any],
    ) -> None:
        super().__init__()
        self._title = title
        self._label = label
        self._data = data

    def compose(self) -> ComposeResult:
        with Vertical(id="form-dialog"):
            yield Label(self._title, classes="dialog-title")

            yield Label("Label")
            yield Input(
                value=self._label or "", placeholder="optional", id="edit-label"
            )

            yield Label("Data (JSON object)")
            yield Input(
                value=json.dumps(self._data, ensure_ascii=False)
                if self._data
                else "{}",
                placeholder="{}",
                id="edit-data",
            )

            with Horizontal(id="form-actions"):
                yield Button("Cancel", id="form-cancel")
                yield Button("Save", variant="primary", id="form-save")

    def on_mount(self) -> None:
        self.query_one("#edit-label", Input).focus()

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
        label = self.query_one("#edit-label", Input).value.strip()
        raw = self.query_one("#edit-data", Input).value.strip() or "{}"
        try:
            data = json.loads(raw)
        except ValueError:
            self.notify("Data must be valid JSON", severity="warning", timeout=3)
            return
        if not isinstance(data, dict):
            self.notify("Data must be a JSON object", severity="warning", timeout=3)
            return
        self.call_after_refresh(self._close, (label or None, data))

    def _close(self, values: EntityEditValues) -> None:
        self.dismiss(values)


class EnumPicker(ModalScreen[list[Any] | None]):
    """Список с чекбоксами для поля-массива enum."""

    BINDINGS = [("escape", "cancel", "Cancel")]

    def __init__(
        self,
        title: str,
        options: list[Any],
        selected: list[Any],
    ) -> None:
        super().__init__()
        self._title = title
        self._options = list(options)
        self._selected = set(selected)

    def compose(self) -> ComposeResult:
        with Vertical(id="enum-dialog"):
            yield Label(self._title, classes="dialog-title")
            yield Label(
                "space — toggle · enter — toggle · esc — cancel",
                classes="dialog-hint",
            )
            yield SelectionList(
                *[
                    Selection(str(option), option, option in self._selected)
                    for option in self._options
                ],
                id="enum-options",
            )
            with Horizontal(id="enum-actions"):
                yield Button("Cancel", id="enum-cancel")
                yield Button("Done", variant="primary", id="enum-save")

    def on_mount(self) -> None:
        self.query_one("#enum-options", SelectionList).focus()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "enum-save":
            selected = self.query_one("#enum-options", SelectionList).selected
            self.dismiss([option for option in self._options if option in selected])
        else:
            self.action_cancel()

    def action_cancel(self) -> None:
        self.dismiss(None)


class MultiEnumSelect(Button):
    """Кнопка-«дропдаун»: открывает EnumPicker с чекбоксами."""

    def __init__(
        self,
        title: str,
        options: list[Any],
        selected: list[Any],
        *,
        field_id: str,
    ) -> None:
        super().__init__(id=field_id, classes="param-multi")
        self._title = title
        self._options = list(options)
        self._selected = [option for option in selected if option in self._options]
        self._refresh_label()

    @property
    def value(self) -> list[Any]:
        return list(self._selected)

    def _refresh_label(self) -> None:
        self.label = ", ".join(str(option) for option in self._selected) or "— none —"

    def on_button_pressed(self, event: Button.Pressed) -> None:
        event.stop()
        self.app.push_screen(
            EnumPicker(self._title, self._options, self._selected),
            self._apply,
        )

    def _apply(self, selected: list[Any] | None) -> None:
        if selected is None:
            return
        self._selected = selected
        self._refresh_label()


class ToolParamsForm(ModalScreen[dict[str, Any] | None]):
    """Поля из JSON Schema инструмента. Dismiss: params или None."""

    BINDINGS = [("escape", "cancel", "Cancel")]

    def __init__(
        self,
        title: str,
        schema: dict[str, Any],
        *,
        context_value: str | None = None,
    ) -> None:
        super().__init__()
        self._title = title
        self._context_value = context_value
        self._fields: list[tuple[str, dict[str, Any], str, str]] = [
            (name, spec, f"param-{index}", _field_kind(spec))
            for index, (name, spec) in enumerate(
                (schema.get("properties") or {}).items()
            )
        ]
        self._required: set[str] = set(schema.get("required") or [])

    def compose(self) -> ComposeResult:
        with Vertical(id="form-dialog"):
            yield Label(self._title, classes="dialog-title")
            context_used = False
            for name, spec, field_id, kind in self._fields:
                title = spec.get("title") or name
                mark = " *" if name in self._required else ""
                yield Label(f"{title}{mark}")
                if kind == "enum":
                    options = [(str(value), value) for value in spec.get("enum") or []]
                    values = [value for _, value in options]
                    value = _enum_default(spec, values, name in self._required)
                    yield Select(
                        options,
                        value=value,
                        allow_blank=value is Select.NULL,
                        id=field_id,
                    )
                elif kind == "multi":
                    options = list((spec.get("items") or {}).get("enum") or [])
                    default = spec.get("default")
                    selected = (
                        [item for item in default if item in options]
                        if isinstance(default, list)
                        else []
                    )
                    yield MultiEnumSelect(title, options, selected, field_id=field_id)
                else:
                    value = _default_text(spec)
                    if not value and self._context_value and not context_used:
                        value = self._context_value
                        context_used = True
                    yield Input(
                        value=value,
                        placeholder=(spec.get("description") or "")[:80],
                        id=field_id,
                    )
            with Horizontal(id="form-actions"):
                yield Button("Cancel", id="form-cancel")
                yield Button("Run", variant="primary", id="form-save")

    def on_mount(self) -> None:
        if self._fields:
            self.query_one(f"#{self._fields[0][2]}").focus()

    def on_input_submitted(self, event: Input.Submitted) -> None:
        event.stop()
        self.submit()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "form-save":
            self.submit()
        elif event.button.id == "form-cancel":
            self.action_cancel()

    def action_cancel(self) -> None:
        self.dismiss(None)

    def submit(self) -> None:
        params: dict[str, Any] = {}
        for name, spec, field_id, kind in self._fields:
            widget = self.query_one(f"#{field_id}")
            if kind == "enum":
                if not isinstance(widget, Select):
                    continue
                value = widget.value
                if value is Select.NULL:
                    value = None
            elif kind == "multi":
                if not isinstance(widget, MultiEnumSelect):
                    continue
                value = widget.value or None
            else:
                if not isinstance(widget, Input):
                    continue
                raw = widget.value.strip()
                if not raw:
                    value = None
                else:
                    try:
                        value = _parse_value(spec, raw)
                    except ValueError:
                        self.notify(
                            f"Invalid value for {name}",
                            severity="warning",
                            timeout=3,
                        )
                        return
            if value is None or value == []:
                if name in self._required:
                    self.notify(f"{name} is required", severity="warning", timeout=3)
                    return
                continue
            params[name] = value
        self.call_after_refresh(self._close, params)

    def _close(self, params: dict[str, Any]) -> None:
        self.dismiss(params)


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


def _field_kind(spec: dict[str, Any]) -> str:
    if spec.get("type") == "array":
        return "multi" if (spec.get("items") or {}).get("enum") else "text"
    if spec.get("enum"):
        return "enum"
    return "text"


def _enum_default(spec: dict[str, Any], values: list[Any], required: bool) -> Any:
    default = spec.get("default")
    if default in values:
        return default
    if required and values:
        return values[0]
    return Select.NULL


def _default_text(spec: dict[str, Any]) -> str:
    default = spec.get("default")
    if default is None:
        return ""
    if isinstance(default, list):
        return ", ".join(str(item) for item in default)
    if isinstance(default, bool):
        return "true" if default else "false"
    if isinstance(default, dict):
        return json.dumps(default, ensure_ascii=False)
    return str(default)


def _parse_value(spec: dict[str, Any], raw: str) -> Any:
    kind = spec.get("type", "string")
    if kind == "array":
        items = [part.strip() for part in raw.split(",") if part.strip()]
        if (spec.get("items") or {}).get("type") == "integer":
            return [int(item) for item in items]
        return items
    if kind == "integer":
        return int(raw)
    if kind == "number":
        return float(raw)
    if kind == "boolean":
        return raw.strip().lower() in {"true", "1", "yes", "on"}
    if kind == "object":
        value = json.loads(raw)
        if not isinstance(value, dict):
            raise ValueError("not an object")
        return value
    return raw
