from textual.app import App, ComposeResult
from textual.containers import Center, Middle, Vertical
from textual.widgets import Footer, Header, Label


class DemonCryApp(App[None]):
    """Minimal shell for the DemonCry TUI."""

    TITLE = "demon-cry-tui"
    SUB_TITLE = "terminal UI for demon cry core"
    BINDINGS = [("ctrl+q", "quit", "Quit")]

    CSS = """
    #placeholder {
        width: auto;
        height: auto;
    }

    .hint {
        color: $text-muted;
    }
    """

    def compose(self) -> ComposeResult:
        yield Header()
        with Center(), Middle(), Vertical(id="placeholder"):
            yield Label("DemonCry TUI")
            yield Label("API/backend not wired yet", classes="hint")
        yield Footer()


def run() -> None:
    DemonCryApp().run()
