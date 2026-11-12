"""Экран выбора инструмента DemonCry."""

from rich.text import Text
from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.screen import ModalScreen
from textual.widgets import Button, Label, OptionList
from textual.widgets.option_list import Option

from demon_cry_tui.api import Tool


class ToolsScreen(ModalScreen[Tool | None]):
    """Список доступных инструментов; Enter выбирает."""

    BINDINGS = [("escape", "cancel", "Cancel")]

    def __init__(self, tools: list[Tool]) -> None:
        super().__init__()
        self._tools = tools

    def compose(self) -> ComposeResult:
        with Vertical(id="tools-dialog"):
            yield Label("Tools", classes="dialog-title")
            yield Label("Enter — run tool", classes="dialog-hint")
            yield OptionList(id="tools-list")
            with Horizontal(id="tools-actions"):
                yield Button("Close", id="tools-close")

    def on_mount(self) -> None:
        options = self.query_one("#tools-list", OptionList)
        options.add_options(
            Option(_tool_label(tool), id=str(index))
            for index, tool in enumerate(self._tools)
        )
        options.highlighted = 0
        options.focus()

    def on_option_list_option_selected(self, event: OptionList.OptionSelected) -> None:
        event.stop()
        self.run_tool()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        self.action_cancel()

    def action_cancel(self) -> None:
        self.dismiss(None)

    def run_tool(self) -> None:
        option = self.query_one("#tools-list", OptionList).highlighted_option
        if option is None or option.id is None:
            return
        self.dismiss(self._tools[int(option.id)])


def _tool_label(tool: Tool) -> Text:
    function = tool.function
    label = Text(function.name, style="bold")
    if function.category:
        label.append(f"  [{function.category}]", style="dim")
    if function.description:
        label.append(f"  {function.description}", style="dim")
    return label
