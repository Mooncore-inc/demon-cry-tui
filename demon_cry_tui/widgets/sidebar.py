"""Сайдбар со списком расследований активного клиента."""

from textual.app import ComposeResult
from textual.containers import Vertical
from textual.message import Message
from textual.widgets import Label, ListItem, ListView, Rule

from demon_cry_tui.api import Investigate

ADD_INVESTIGATE_ID = "add-investigate"
ADD_INVESTIGATE_LABEL = "+ add investigation"


class Sidebar(Vertical):
    """Список расследований: статус клиента, подсказка и пункт добавления."""

    class Selected(Message):
        """Пользователь выбрал расследование."""

        def __init__(self, investigate: Investigate) -> None:
            super().__init__()
            self.investigate = investigate

    class AddRequested(Message):
        """Пользователь выбрал пункт «добавить расследование»."""

    def __init__(self) -> None:
        super().__init__()
        self.investigations: list[Investigate] = []

    def compose(self) -> ComposeResult:
        yield Label("Investigations", id="sidebar-title")
        yield Label(id="client-status", classes="hint")
        yield Label(id="sidebar-hint", classes="hint")
        yield Rule(id="sidebar-rule")
        yield ListView(id="investigations")

    def on_mount(self) -> None:
        self.list_view.focus()

    @property
    def list_view(self) -> ListView:
        return self.query_one("#investigations", ListView)

    def set_client(self, text: str) -> None:
        self.query_one("#client-status", Label).update(text)

    def set_hint(self, text: str) -> None:
        self.query_one("#sidebar-hint", Label).update(text)

    async def clear(self) -> None:
        self.investigations = []
        await self.list_view.clear()

    async def show(self, investigations: list[Investigate]) -> None:
        await self.clear()
        self.investigations = investigations
        await self.list_view.extend(
            ListItem(Label(f"#{investigate.id} {investigate.name}"))
            for investigate in investigations
        )
        await self.list_view.append(
            ListItem(Label(ADD_INVESTIGATE_LABEL), id=ADD_INVESTIGATE_ID)
        )
        self.list_view.index = 0
        self.set_hint(
            f"{len(investigations)} total" if investigations else "no investigations"
        )

    def on_list_view_selected(self, event: ListView.Selected) -> None:
        event.stop()
        if event.item.id == ADD_INVESTIGATE_ID:
            self.post_message(self.AddRequested())
            return
        if 0 <= event.index < len(self.investigations):
            self.post_message(self.Selected(self.investigations[event.index]))
