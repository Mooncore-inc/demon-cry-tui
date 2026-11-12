"""Дерево графа расследования: сущности и их связи."""

from collections import defaultdict

from rich.text import Text
from textual.app import ComposeResult
from textual.containers import Vertical
from textual.widgets import Label, Tree
from textual.widgets.tree import TreeNode

from demon_cry_tui.api import Edge, Entity, Graph, Investigate


class GraphView(Vertical):
    """Заголовок расследования и дерево связей."""

    def __init__(self) -> None:
        super().__init__()
        self.graph: Graph | None = None

    def compose(self) -> ComposeResult:
        yield Label("DemonCry TUI", id="content-title")
        yield Label("Select an investigation", id="content-hint", classes="hint")
        yield Tree("Graph", id="graph-tree")

    @property
    def tree_view(self) -> Tree[int | None]:
        return self.query_one("#graph-tree", Tree)

    def set_title(self, text: str) -> None:
        self.query_one("#content-title", Label).update(text)

    def set_hint(self, text: str) -> None:
        self.query_one("#content-hint", Label).update(text)

    def clear(self) -> None:
        self.graph = None
        self.set_title("DemonCry TUI")
        self.set_hint("Select an investigation")
        self.tree_view.clear()

    @property
    def cursor_entity_id(self) -> int | None:
        node = self.tree_view.cursor_node
        if node is None or not isinstance(node.data, int):
            return None
        return node.data

    def entity(self, entity_id: int) -> Entity | None:
        if self.graph is None:
            return None
        return next(
            (node for node in self.graph.nodes if node.id == entity_id),
            None,
        )

    def show_loading(self, investigate: Investigate) -> None:
        self.graph = None
        self.set_title(investigate.name)
        self.set_hint("loading graph…")
        self.tree_view.clear()

    def show(self, graph: Graph) -> None:
        tree = self.tree_view
        tree.clear()
        self.graph = graph

        nodes = {node.id: node for node in graph.nodes}
        children: dict[int, list[Edge]] = defaultdict(list)
        incoming: set[int] = set()
        for edge in graph.edges:
            if edge.source_id in nodes and edge.target_id in nodes:
                children[edge.source_id].append(edge)
                incoming.add(edge.target_id)

        self.set_hint(f"{len(nodes)} entities · {len(graph.edges)} links")
        if not nodes:
            tree.root.add_leaf(Text("empty graph", style="dim"))
            return

        expanded: set[int] = set()

        def add_branch(
            node_id: int,
            parent: TreeNode[int | None],
            relation: str | None,
            depth: int,
        ) -> None:
            entity_node = parent.add(
                _entity_label(nodes[node_id], relation),
                data=node_id,
                expand=depth == 0,
            )
            expanded.add(node_id)
            for edge in children.get(node_id, []):
                target = edge.target_id
                if target in expanded:
                    entity_node.add_leaf(
                        _entity_label(nodes[target], edge.relation, seen=True),
                        data=target,
                    )
                else:
                    add_branch(target, entity_node, edge.relation, depth + 1)

        for node_id in [node.id for node in graph.nodes if node.id not in incoming]:
            add_branch(node_id, tree.root, None, 0)
        for node in graph.nodes:
            if node.id not in expanded:
                add_branch(node.id, tree.root, None, 0)
        tree.root.expand()


def _entity_label(
    entity: Entity,
    relation: str | None = None,
    *,
    seen: bool = False,
) -> Text:
    label = Text()
    if relation:
        label.append(f"{relation} → ", style="dim")
    if entity.type:
        label.append(f"{entity.type} ", style="dim")
    label.append(entity.label or entity.value)
    if entity.label and entity.label != entity.value:
        label.append(f"  {entity.value}", style="dim")
    if seen:
        label.append("  (seen)", style="dim")
    return label
