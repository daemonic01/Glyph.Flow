from typing import List, Optional
from core.controllers.command_result import CommandResult
from core.utils import get_level
from core.node import Node

# Fallback schema if no custom/default schema is found in config
DEFAULT_FALLBACK = ["Project", "Phase", "Task", "Subtask"]


class NodeSchema:
    """
    Represents the hierarchical schema of the node tree.
    Defines allowed node types at each depth and provides helpers
    to validate, relabel, and traverse schema depth.
    """

    def __init__(self, hierarchy: List[str]):
        """
        Args:
            hierarchy (list[str]): Ordered list of node types,
                                   e.g. ["Project", "Phase", "Task", "Subtask"].
        """
        self.hierarchy = hierarchy

    def get_expected_child_type(self, parent: Optional[Node]) -> Optional[str]:
        """
        Get the expected child type for a given parent node.

        Args:
            parent (Node | None): Parent node (or None for root-level).

        Returns:
            str | None: Expected child type at the next level,
                        or None if maximum depth reached.
        """
        if parent is None:
            return self.hierarchy[0]
        level = get_level(parent)
        return self.hierarchy[level + 1] if level + 1 < len(self.hierarchy) else None

    def is_valid_child(self, parent: Optional[Node], child_type: str) -> bool:
        """
        Validate whether a child of type `child_type` is allowed under given parent.

        Args:
            parent (Node | None): Parent node.
            child_type (str): Proposed type of child.

        Returns:
            bool: True if valid, False otherwise.
        """
        return self.get_expected_child_type(parent) == child_type

    def validate_tree_depth(self, node: Node) -> int:
        """
        Compute the maximum depth of a tree rooted at the given node.

        Args:
            node (Node): Root node of a subtree.

        Returns:
            int: Depth of the tree (1 = just this node).
        """
        if not node.children:
            return 1
        return 1 + max(self.validate_tree_depth(child) for child in node.children)

    def relabel_tree_to_match(self, node: Node, level: int = 0):
        """
        Update node types recursively to match the schema.

        Args:
            node (Node): Node whose type (and children's types) to relabel.
            level (int): Current depth (default 0 = root).
        """
        if level < len(self.hierarchy):
            node.type = self.hierarchy[level]
        for child in node.children:
            self.relabel_tree_to_match(child, level + 1)


def _get_default_levels(ctx) -> List[str]:
    """
    Return a default schema.

    Tries to read from ctx.config["default_schema"], falling back to DEFAULT_FALLBACK.
    """
    if hasattr(ctx.config, "default_schema"):
        return list(ctx.config["default_schema"])
    return list(DEFAULT_FALLBACK)


def schema_handler(ctx, *, hierarchy: Optional[List[str]] = None, use_default: bool = False) -> CommandResult:
    """
    Handler for the 'schema' command.

    Switches the active schema (hierarchy of node types) at runtime.
    Relabels existing nodes to match the new schema, if possible.

    Args:
        ctx: Application context (must provide ctx.nodes, ctx.schema, ctx.config).
        hierarchy (list[str] | None): New schema levels if provided.
        use_default (bool): If True, resets schema to default (from config or fallback).

    Returns:
        CommandResult:
            - code="usage" if no schema provided.
            - code="set_success" if schema was set for the first time.
            - code="switch_success" if schema was switched successfully.
            - code="switch_default_success" if default schema was restored.
            - code="length_mismatch" if current nodes conflict with new schema depth.
            - code="error" for unexpected exceptions.
    """
    levels: List[str] = []
    if use_default:
        levels = _get_default_levels(ctx)
    else:
        levels = list(hierarchy or [])

    if not levels:
        return CommandResult(code="usage", params={}, outcome=False)

    new_schema_str = " > ".join(levels)
    new_len = len(levels)

    try:
        has_nodes = bool(getattr(ctx, "nodes", []))
        current_schema = getattr(ctx, "schema", None)

        # --- case: first time schema set ---
        if current_schema is None:
            ctx.schema = NodeSchema(levels)
            ctx.config["custom_schema"] = levels
            return CommandResult(
                code="set_success",
                params={"schema": new_schema_str},
                outcome=True
            )

        # --- case: compare lengths with current schema ---
        try:
            current_len = len(getattr(current_schema, "levels"))
        except Exception:
            # fallback: check alternative attribute names
            for attr in ("names", "hierarchy"):
                if hasattr(current_schema, attr):
                    current_len = len(getattr(current_schema, attr))
                    break
            else:
                raise

        if new_len != current_len and ctx.app.nodes:
            return CommandResult(
                code="length_mismatch",
                params={"depth": current_len, "new_depth": new_len},
                outcome=False
            )

        # --- apply schema + relabel nodes if present ---
        target_schema = NodeSchema(levels)
        if has_nodes:
            for root in ctx.nodes:
                target_schema.relabel_tree_to_match(root)

        ctx.schema = target_schema
        ctx.config["custom_schema"] = levels

        if use_default:
            return CommandResult(
                code="switch_default_success",
                params={"schema": new_schema_str},
                outcome=True
            )
        return CommandResult(
            code="switch_success",
            params={"schema": new_schema_str},
            outcome=True
        )

    except Exception as e:
        return CommandResult(
            code="error",
            params={"error": str(e)},
            outcome=False
        )
