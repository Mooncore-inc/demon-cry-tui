from functools import partial
from typing import Any
from urllib.parse import urlsplit

import httpx
from textual import work
from textual.app import App, ComposeResult
from textual.containers import Horizontal, Vertical
from textual.widgets import Footer, Header, Label

from demon_cry_tui.api import DemonCryAPIError, Investigate, Tool
from demon_cry_tui.client import ClientError, DemonCryClient
from demon_cry_tui.config import (
    ActiveClient,
    CatalogError,
    ConnectionStore,
    SecretStoreError,
    load_config,
)
from demon_cry_tui.screens import (
    ClientsScreen,
    EntityEditForm,
    EntityEditValues,
    EntityForm,
    EntityValues,
    NamePrompt,
    ToolParamsForm,
    ToolsScreen,
)
from demon_cry_tui.widgets import GraphView, Sidebar

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
        ("ctrl+e", "new_entity", "New entity"),
        ("ctrl+t", "tools", "Tools"),
        ("e", "edit", "Edit"),
    ]

    def __init__(self) -> None:
        super().__init__()
        self.config = load_config()
        self.connections = ConnectionStore()
        self.client = DemonCryClient(self.connections, self.config.request_timeout)
        self.selected: Investigate | None = None

    def compose(self) -> ComposeResult:
        yield Header()
        with Horizontal(id="main"):
            yield Sidebar()
            with Vertical(id="content"):
                yield GraphView()
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

    def action_new_entity(self) -> None:
        if self.selected is None:
            self.notify("Select an investigation first", severity="warning", timeout=3)
            return
        active = self._active()
        if active is None or not active.token:
            self.notify("No active client with token", severity="warning", timeout=4)
            return
        self.push_screen(EntityForm("New entity"), self._new_entity)

    def action_tools(self) -> None:
        if self.selected is None:
            self.notify("Select an investigation first", severity="warning", timeout=3)
            return
        self._open_tools()

    def action_edit(self) -> None:
        if self.graph.tree_view.has_focus and self.graph.cursor_entity_id is not None:
            self._edit_entity()
        elif self.sidebar.list_view.has_focus and self.selected is not None:
            self._rename_investigation()
        else:
            self.notify(
                "Focus the graph or the list to edit", severity="warning", timeout=3
            )

    def on_sidebar_selected(self, event: Sidebar.Selected) -> None:
        self.selected = event.investigate
        self.graph.show_loading(event.investigate)
        self.graph.tree_view.focus()
        self._load_graph(event.investigate.id)

    def on_sidebar_add_requested(self, _event: Sidebar.AddRequested) -> None:
        self.action_new_investigate()

    @property
    def sidebar(self) -> Sidebar:
        return self.query_one(Sidebar)

    @property
    def graph(self) -> GraphView:
        return self.query_one(GraphView)

    def _refresh(self) -> None:
        self.selected = None
        self.graph.clear()
        keyring = self.query_one("#keyring-status", Label)
        keyring.update(f"keyring: {self.client.backend}")

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
        investigations = await self._call("list_investigates")
        if investigations is None:
            self.sidebar.set_hint("failed to load")
            return
        await self.sidebar.show(investigations)

    @work(exclusive=True)
    async def _load_graph(self, investigate_id: int) -> None:
        graph = await self._call("get_graph", investigate_id)
        if graph is None:
            self.graph.set_hint("failed to load graph")
            return
        self.graph.show(graph)

    def _new_investigate(self, name: str | None) -> None:
        if name:
            self._create_investigate(name)

    @work(exclusive=True)
    async def _create_investigate(self, name: str) -> None:
        investigate = await self._call("create_investigate", name)
        if investigate is None:
            return
        self.notify(f"Created #{investigate.id} {investigate.name}")
        self._load_investigations()

    def _new_entity(self, values: EntityValues | None) -> None:
        if values is not None and self.selected is not None:
            self._create_entity(self.selected.id, *values)

    @work(exclusive=True)
    async def _create_entity(
        self, investigate_id: int, value: str, type_: str, label: str
    ) -> None:
        entity = await self._call(
            "create_entity", investigate_id, value, type_=type_, label=label
        )
        if entity is None:
            return
        self.notify(f"Created entity #{entity.id} {entity.value}")
        self._load_graph(investigate_id)

    def _edit_entity(self) -> None:
        entity_id = self.graph.cursor_entity_id
        entity = self.graph.entity(entity_id) if entity_id is not None else None
        if entity is None or self.selected is None:
            return
        self.push_screen(
            EntityEditForm("Edit entity", label=entity.label, data=entity.data),
            partial(self._save_entity, self.selected.id, entity.id),
        )

    def _save_entity(
        self,
        investigate_id: int,
        entity_id: int,
        values: EntityEditValues | None,
    ) -> None:
        if values is not None:
            self._update_entity(investigate_id, entity_id, *values)

    @work(exclusive=True)
    async def _update_entity(
        self,
        investigate_id: int,
        entity_id: int,
        label: str | None,
        data: dict[str, Any],
    ) -> None:
        entity = await self._call(
            "update_entity", investigate_id, entity_id, label=label, data=data
        )
        if entity is None:
            return
        self.notify(f"Updated entity #{entity.id}")
        self._load_graph(investigate_id)

    def _rename_investigation(self) -> None:
        if self.selected is None:
            return
        self.push_screen(
            NamePrompt("Rename investigation", value=self.selected.name),
            self._rename,
        )

    def _rename(self, name: str | None) -> None:
        if name and self.selected is not None:
            self._rename_investigate(self.selected.id, name)

    @work(exclusive=True)
    async def _rename_investigate(self, investigate_id: int, name: str) -> None:
        investigate = await self._call("rename_investigate", investigate_id, name)
        if investigate is None:
            return
        self.selected = investigate
        self.graph.set_title(investigate.name)
        self.notify(f"Renamed to {investigate.name}")
        self._load_investigations()

    @work(exclusive=True)
    async def _open_tools(self) -> None:
        tools = await self._call("list_tools")
        if tools is None:
            return
        if not tools:
            self.notify("No tools available", severity="warning", timeout=4)
            return
        self.push_screen(ToolsScreen(tools), self._tool_selected)

    def _tool_selected(self, tool: Tool | None) -> None:
        if tool is None:
            return
        entity_id = self.graph.cursor_entity_id
        entity = self.graph.entity(entity_id) if entity_id is not None else None
        self.push_screen(
            ToolParamsForm(
                tool.function.name,
                tool.function.parameters_model,
                context_value=entity.value if entity is not None else None,
            ),
            partial(self._run_tool, tool),
        )

    def _run_tool(self, tool: Tool, params: dict[str, Any] | None) -> None:
        if params is None or self.selected is None:
            return
        entity_id = self.graph.cursor_entity_id
        context = [entity_id] if entity_id is not None else []
        self._execute_tool(self.selected.id, tool.function.name, params, context)

    @work(exclusive=True)
    async def _execute_tool(
        self,
        investigate_id: int,
        tool_name: str,
        params: dict[str, Any],
        context: list[int],
    ) -> None:
        result = await self._call(
            "execute_tool", investigate_id, tool_name, params, context
        )
        if result is None:
            return
        status = result.get("status", "ok") if isinstance(result, dict) else "ok"
        self.notify(f"{tool_name}: {status}")
        self._load_graph(investigate_id)

    async def _call(self, method: str, *args: Any, **kwargs: Any) -> Any | None:
        try:
            return await self.client.call(method, *args, **kwargs)
        except (ClientError, DemonCryAPIError, httpx.HTTPError) as exc:
            self._notify_error(exc)
            return None

    def _active(self) -> ActiveClient | None:
        try:
            return self.client.active()
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
