from __future__ import annotations

from dataclasses import dataclass
from typing import List, Dict, Iterable, Any, Optional, Tuple
from pathlib import Path
import csv, json
from datetime import datetime

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase.cidfonts import UnicodeCIDFont
from reportlab.platypus import SimpleDocTemplate, Table as RLTable, TableStyle, Paragraph, Spacer


from core.controllers.command_result import CommandResult


# Public API (handler)

def export_handler(ctx, *,
                   format: Optional[str] = None,
                   path: Optional[str] = None,
                   scope: str = "all",
                   columns: Optional[str | List[str]] = None,
                   include_completed: bool = True,
                   sort: str = "",
                   title: Optional[str] = None,
                   theme: str = "glyph-dark",
                   **kwargs) -> CommandResult:
    """
    Universal export command.

    Params (parsed by your registry/command_factory):
      - format:  "csv" | "pdf" | "json" (inferred from path suffix if omitted)
      - path:    output file path (default auto-name)
      - scope:   "all" | "subtree:<id>" | "filter:<text>"
      - columns: comma-separated list or list[str]; if omitted -> auto-discovered ALL
      - include_completed: include completed nodes if True
      - sort:    "<col>" or "<col>:asc|desc"
      - title:   PDF table title
    """
    fmt = (format or _infer_format(path) or "csv").lower()
    if fmt not in {"csv", "pdf", "json"}:
        return CommandResult(code="invalid_format", params={"format": fmt}, outcome=False)

    if path:
        out_path = Path(path)
    else:
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        base = Path(ctx.config.get('paths.export', 'export/', str))
        out_path = base / f"glyph_export_{ts}.{fmt}"


    # Parse columns option: None -> autodetect; "a,b,c" -> ["a","b","c"]
    col_list: Optional[List[str]] = None
    if isinstance(columns, str) and columns.strip():
        col_list = [c.strip() for c in columns.split(",") if c.strip()]
    elif isinstance(columns, list):
        col_list = [str(c).strip() for c in columns if str(c).strip()]

    service = ExportService(ctx)

    try:
        rows, cols = service.collect_rows_and_columns(
            scope=scope,
            requested_columns=col_list,
            include_completed=include_completed,
            sort=sort
        )

        if fmt == "csv":
            service.write_csv(rows, cols, out_path)
        elif fmt == "pdf":
            service.write_pdf(rows, cols, out_path, title=title or "Glyph.Flow Export")
        else:
            service.write_json_tree(scope=scope, path=out_path)

        return CommandResult(
            code="success",
            params={"format": fmt, "path": str(out_path), "rows": len(rows)},
            outcome=True
        )

    except Exception as e:
        ctx.log.error(f"Export failed: {e}")
        return CommandResult(
            code="export_failed",
            params={"format": fmt, "path": str(out_path), "error": str(e)},
            outcome=False
        )



# Service



PREFERRED_ORDER = [
    # base fields from Node
    "id", "type", "name", "created_at", "deadline", "completed",
    "short_desc", "full_desc",
    # derived fields
    "progress", "parent_id", "depth", "children_count",
]

@dataclass
class ExportOptions:
    fmt: str
    path: Path
    scope: str = "all"
    columns: Optional[List[str]] = None
    include_completed: bool = True
    sort: str = ""        # "name:asc" or "progress:desc"
    theme: str = "glyph-dark"


class ExportService:
    def __init__(self, ctx):
        self.ctx = ctx

        # FONTS
        FONT_REGULAR = self.ctx.base_dir / "assets/fonts/NotoSansJP-Regular.ttf"
        pdfmetrics.registerFont(TTFont("NotoSans", FONT_REGULAR))
        pdfmetrics.registerFont(UnicodeCIDFont("HeiseiMin-W3"))

    # PUBLIC

    def collect_rows_and_columns(self,
                                 scope: str,
                                 requested_columns: Optional[List[str]],
                                 include_completed: bool,
                                 sort: str) -> Tuple[List[Dict[str, Any]], List[str]]:
        """
        Returns (rows, columns). If requested_columns is None, autodetect columns.
        """
        nodes = list(self._select_nodes(scope))
        if not include_completed:
            nodes = [n for n in nodes if not getattr(n, "completed", False)]

        # Autodetect base fields from Node instances (non-callable, simple scalars)
        base_fields = self._discover_simple_fields(nodes)

        # Derived/computed fields we can always provide
        derived_fields = {"progress", "parent_id", "depth", "children_count"}

        # Final column set
        if requested_columns:
            cols = requested_columns
        else:
            # Merge with stable ordering: preferred first, then extras alpha
            all_fields = base_fields | derived_fields
            cols = self._order_columns(all_fields)

        rows = [self._node_to_row(n, cols) for n in nodes]
        rows = self._sort_rows(rows, sort)
        return rows, cols



    def write_csv(self, rows: List[Dict[str, Any]], columns: List[str], path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=columns)
            writer.writeheader()
            writer.writerows(rows)




    def write_pdf(self, rows, columns, path: Path, *, title: str = "Glyph.Flow Export") -> None:
        """
        Render a professional-looking PDF table with ReportLab:
        - repeating header on each page
        - zebra striping
        - grid borders
        - word-wrapped long text
        - auto column widths (heuristic)
        """
        path.parent.mkdir(parents=True, exist_ok=True)

        # doc setup
        pagesize = landscape(A4)
        doc = SimpleDocTemplate(
            str(path),
            pagesize=pagesize,
            leftMargin=15 * mm,
            rightMargin=15 * mm,
            topMargin=12 * mm,
            bottomMargin=12 * mm,
            title=title,
            author="Glyph.Flow",
        )
        story = []

        styles = getSampleStyleSheet()
        h_style = styles["Heading2"]
        h_style.spaceAfter = 6
        p_style = ParagraphStyle(
            "Cell",
            parent=styles["BodyText"],
            fontName="NotoSans",
            fontSize=8,
            leading=10,
        )

        # build table data (Paragraph for wrapping)
        header = [Paragraph(f"<b>{c.upper()}</b>", p_style) for c in columns]
        data = [header]
        for r in rows:
            row_cells = []
            for c in columns:
                val = r.get(c, "")
                if c == "progress" and isinstance(val, (int, float)):
                    txt = f"{int(val)}%"
                else:
                    txt = "" if val is None else str(val)
                # escape minimal XML chars for Paragraph safety
                txt = (txt.replace("&", "&amp;")
                        .replace("<", "&lt;")
                        .replace(">", "&gt;"))
                row_cells.append(Paragraph(txt, p_style))
            data.append(row_cells)



        # heuristic col widths (character-based)
        def col_char_width(col):
            maxlen = max((len(str(rows[i-1].get(columns[col], ""))) for i in range(1, min(len(data), 200))), default=0)
            maxlen = max(maxlen, len(columns[col]) + 2)
            return maxlen

        char_widths = [col_char_width(i) for i in range(len(columns))]
        total_chars = float(sum(char_widths)) or 1.0
        available_mm = pagesize[0] / mm - 30  # left+right margins (15+15)
        # minimum/maximum per col (mm)
        min_w, max_w = 18, 70

        col_widths_mm = []
        for cw in char_widths:
            raw = available_mm * (cw / total_chars)
            col_widths_mm.append(max(min_w, min(max_w, raw)))
        # normalize if overflow/underflow:
        scale = available_mm / max(sum(col_widths_mm), 1.0)
        col_widths_mm = [w * scale for w in col_widths_mm]
        col_widths = [w * mm for w in col_widths_mm]

        # table & style
        table = RLTable(data, colWidths=col_widths, repeatRows=1)

        base_style = TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#555555")),  # header bg (slate-800)
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
            ("ALIGN", (0, 0), (-1, 0), "CENTER"),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("FONTSIZE", (0, 0), (-1, -1), 8),
            ("LEADING", (0, 0), (-1, -1), 10),
            ("LEFTPADDING", (0, 0), (-1, -1), 4),
            ("RIGHTPADDING", (0, 0), (-1, -1), 4),
            ("TOPPADDING", (0, 0), (-1, -1), 2),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
            ("GRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#9CA3AF")),  # grid (gray-400)
        ])
        table.setStyle(base_style)

        # zebra rows (skip header)
        for i in range(1, len(data)):
            if i % 2 == 1:
                table.setStyle(TableStyle([("BACKGROUND", (0, i), (-1, i), colors.HexColor("#F3F4F6"))]))  # gray-100



        # header & footer callbacks
        def _header_footer(canvas, doc):
            canvas.saveState()
            canvas.setFont("NotoSans", 8)
            canvas.drawRightString(pagesize[0] - 15 * mm, 10 * mm, f"Page {doc.page}")
            canvas.restoreState()

        story.append(Paragraph(title, h_style))
        story.append(Spacer(1, 4 * mm))
        story.append(table)

        doc.build(story, onFirstPage=_header_footer, onLaterPages=_header_footer)



    def write_json_tree(self, *, scope: str, path: Path) -> int:
            """
            Write node tree in the same JSON shape as save_node_tree():
            [ node_dict, node_dict, ... ]  (each node_dict includes its children).
            Scope:
            - "all": every root node
            - "subtree:<id>": only that node (as root) with its subtree
            - "filter:<text>": each matching node as a top-level root in the JSON array
            """
            roots = self._select_roots_for_json(scope)
            payload = [n.to_dict() for n in roots]  # same as save_node_tree() shape

            path.parent.mkdir(parents=True, exist_ok=True)
            with path.open("w", encoding="utf-8") as f:
                json.dump(payload, f, indent=2, ensure_ascii=False)
            return len(payload)

    # ---- helpers for JSON scope ----

    def _select_roots_for_json(self, scope: str):
        """Return a list of Node roots to serialize (NOT flattened)."""
        roots = list(self._get_roots())

        if not scope or scope == "all":
            return roots

        all_nodes = [*roots, *self._iter_all(roots)]

        if scope.startswith("subtree:"):
            qid = scope.split(":", 1)[1].strip()
            node = self._find_by_id(all_nodes, qid)
            return [node] if node else []

        if scope.startswith("filter:"):
            q = scope.split(":", 1)[1].strip().lower()
            def hay(n):
                return " ".join([
                    str(getattr(n, "id", "")),
                    str(getattr(n, "name", "")),
                    str(getattr(n, "type", "")),
                    str(getattr(n, "short_desc", "")),
                    str(getattr(n, "full_desc", "")),
                ]).lower()
            # unique by id, keep order
            seen, out = set(), []
            for n in all_nodes:
                if q in hay(n):
                    nid = str(getattr(n, "id", ""))
                    if nid not in seen:
                        seen.add(nid)
                        out.append(n)
            return out

        return roots
    


    # INTERNAL
    def _select_nodes(self, scope: str) -> Iterable[Any]:
        """
        Flatten nodes according to scope.

        Scope:
          - "all" (default)
          - "subtree:<id>"  -> root that subtree
          - "filter:<text>" -> name/desc/type/id contains text (case-insensitive)
        """
        roots = list(self._get_roots())
        all_nodes = list(self._iter_all(roots))

        if not scope or scope == "all":
            return all_nodes

        if scope.startswith("subtree:"):
            qid = scope.split(":", 1)[1].strip()
            root = self._find_by_id(all_nodes, qid)
            return list(self._iter_subtree(root)) if root else []

        if scope.startswith("filter:"):
            q = scope.split(":", 1)[1].strip().lower()
            def hay(n: Any) -> str:
                return " ".join([
                    str(getattr(n, "id", "")),
                    str(getattr(n, "name", "")),
                    str(getattr(n, "type", "")),
                    str(getattr(n, "short_desc", "")),
                    str(getattr(n, "full_desc", "")),
                ]).lower()
            return [n for n in all_nodes if q in hay(n)]

        # Fallback to all
        return all_nodes


    def _get_roots(self) -> Iterable[Any]:
        return self.ctx.nodes or []


    def _iter_all(self, roots: Iterable[Any]) -> Iterable[Any]:
        for r in roots:
            yield r
            yield from self._iter_subtree(r)


    def _iter_subtree(self, node: Any) -> Iterable[Any]:
        for c in getattr(node, "children", []) or []:
            yield c
            yield from self._iter_subtree(c)


    def _find_by_id(self, nodes: Iterable[Any], node_id: str) -> Optional[Any]:
        for n in nodes:
            if str(getattr(n, "id", "")).strip() == str(node_id).strip():
                return n
        return None


    def _discover_simple_fields(self, nodes: List[Any]) -> set[str]:
        """
        Collect attribute names that look like simple data fields from Node instances.
        - skips callables and private
        - skips complex refs (parent, children)
        """
        simple: set[str] = set()
        scalar_types = (str, int, float, bool, type(None))
        for n in nodes:
            for k, v in vars(n).items():
                if k.startswith("_"):
                    continue
                if k in ("parent", "children"):
                    continue
                if callable(v):
                    continue
                if isinstance(v, scalar_types):
                    simple.add(k)
        return simple


    def _order_columns(self, cols: set[str]) -> List[str]:
        ordered: List[str] = []
        for k in PREFERRED_ORDER:
            if k in cols and k not in ordered:
                ordered.append(k)
        # append any extras deterministically
        extras = sorted([c for c in cols if c not in ordered])
        return ordered + extras


    def _node_to_row(self, node: Any, columns: List[str]) -> Dict[str, Any]:
        base = self._extract_base_fields(node)
        derived = self._extract_derived_fields(node)
        row = {**base, **derived}
        # Ensure all requested columns exist
        return {c: row.get(c, "") for c in columns}


    def _extract_base_fields(self, node: Any) -> Dict[str, Any]:
        scalar_types = (str, int, float, bool, type(None))
        out: Dict[str, Any] = {}
        for k, v in vars(node).items():
            if k.startswith("_"): 
                continue
            if k in ("parent", "children"):
                continue
            if callable(v):
                continue
            if isinstance(v, scalar_types):
                out[k] = v
        return out


    def _extract_derived_fields(self, node: Any) -> Dict[str, Any]:
        try:
            progress_val = int(node.progress())
        except Exception:
            progress_val = ""

        # parent_id
        pid = getattr(getattr(node, "parent", None), "id", None)

        # depth (root=0)
        d = 0
        p = getattr(node, "parent", None)
        while p is not None:
            d += 1
            p = getattr(p, "parent", None)

        # children_count
        cc = len(getattr(node, "children", []) or [])

        return {
            "progress": progress_val,
            "parent_id": pid or "",
            "depth": d,
            "children_count": cc,
        }


    def _sort_rows(self, rows: List[Dict[str, Any]], sort: str) -> List[Dict[str, Any]]:
        if not sort:
            return rows
        key, _, dirn = sort.partition(":")
        rev = (dirn.lower() == "desc")
        def keyfunc(r: Dict[str, Any]):
            v = r.get(key)
            # try numeric sort if possible
            try:
                return (float(v), str(v))
            except Exception:
                return (0.0, str(v))
        return sorted(rows, key=keyfunc, reverse=rev)

    @staticmethod
    def _to_str(v: Any) -> str:
        return "" if v is None else str(v)


def _infer_format(path: Optional[str]) -> Optional[str]:
    if not path:
        return None
    ext = Path(path).suffix.lower().lstrip(".")
    return ext if ext in {"csv", "pdf"} else None
