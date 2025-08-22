from typing import List, Optional
from core.controllers.command_result import CommandResult
from core.utils import get_level
from core.node import Node

DEFAULT_FALLBACK = ["Project", "Phase", "Task", "Subtask"]

class NodeSchema:
    def __init__(self, hierarchy: List[str]):
        self.hierarchy = hierarchy

    def get_expected_child_type(self, parent: Optional[Node]) -> Optional[str]:
        """Get the expected child type based on the schema and parent node level."""
        if parent is None:
            return self.hierarchy[0]
        level = get_level(parent)
        return self.hierarchy[level + 1] if level + 1 < len(self.hierarchy) else None

    def is_valid_child(self, parent: Optional[Node], child_type: str) -> bool:
        """Check if a child type is valid for the given parent node."""
        return self.get_expected_child_type(parent) == child_type
    
    def validate_tree_depth(self, node: Node) -> int:
        """Return the maximum depth of a given tree."""
        if not node.children:
            return 1
        return 1 + max(self.validate_tree_depth(child) for child in node.children)
    
    def relabel_tree_to_match(self, node: Node, level: int = 0):
        """Update node types throughout the tree to match the schema hierarchy."""
        if level < len(self.hierarchy):
            node.type = self.hierarchy[level]
        for child in node.children:
            self.relabel_tree_to_match(child, level + 1)

def _get_default_levels(ctx) -> List[str]:
    """Try to find a default schema from several possible places."""
    if hasattr(ctx.config, "default_schema"):
        return list(ctx.config["default_schema"])

    # fallback
    return list(DEFAULT_FALLBACK)



def schema_handler(ctx, *, hierarchy: Optional[List[str]] = None, use_default: bool = False) -> CommandResult:
    """
    Switch schema by comparing NEW vs CURRENT schema length only.

    --default: új sémát a defaultból vesszük; <LEVEL...> nélkül is használható.
    """
    levels: List[str] = []
    if use_default:
        levels = _get_default_levels(ctx)
    else:
        levels = list(hierarchy or [])

    if not levels:
        return CommandResult(code="usage", params={})

    new_schema_str = " > ".join(levels)
    new_len = len(levels)

    try:
        has_nodes = bool(getattr(ctx, "nodes", []))
        current_schema = getattr(ctx, "schema", None)

        if current_schema is None:
            ctx.schema = NodeSchema(levels)
            ctx.config["custom_schema"] = levels

            if use_default:
                return CommandResult(code="set_success", params={"schema": new_schema_str})
            return CommandResult(code="set_success", params={"schema": new_schema_str})


        try:
            current_len = len(getattr(current_schema, "levels"))
        except Exception:

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
            )


        target_schema = NodeSchema(levels)
        if has_nodes:
            for root in ctx.nodes:
                target_schema.relabel_tree_to_match(root)

        ctx.schema = target_schema
        ctx.config["custom_schema"] = levels


        if use_default:
            return CommandResult(code="switch_default_success", params={"schema": new_schema_str})
        return CommandResult(code="switch_success", params={"schema": new_schema_str})

    except Exception as e:
        return CommandResult(code="error", params={"error": str(e)})