#!/usr/bin/env python3
"""
list_paths.py — Gyűjtsd ki egy könyvtár összes relatív elérési útját és mentsd .txt-be.

Példa:
  python list_paths.py . -o tree.txt
  python list_paths.py /some/dir -o out.txt --files-only --ignore "__pycache__" --ignore "*.pyc"
"""

from __future__ import annotations
import argparse
import os
from pathlib import Path
from fnmatch import fnmatch

def is_hidden(path: Path) -> bool:
    # Egyszerű, hordozható heurisztika: bármely komponens ponttal kezdődik (POSIX jellegű).
    # Windows "hidden" attribútumát nem vizsgáljuk, de a legtöbb .git/.venv így is szűrhető.
    return any(part.startswith('.') for part in path.parts)

def should_ignore(rel_posix: str, ignore_patterns: list[str]) -> bool:
    return any(fnmatch(rel_posix, pat) for pat in ignore_patterns)

def collect_paths(
    root: Path,
    include_hidden: bool,
    files_only: bool,
    dirs_only: bool,
    ignore_patterns: list[str],
    follow_symlinks: bool,
    slash_dirs: bool,
) -> list[str]:
    items: list[str] = []
    for dirpath, dirnames, filenames in os.walk(root, followlinks=follow_symlinks):
        dpath = Path(dirpath)

        # Könyvtárak kezelése
        if not files_only:
            rel_dir = dpath.relative_to(root)
            if rel_dir != Path('.'):  # a gyökér mappát ne listázzuk
                rel_txt = rel_dir.as_posix()
                if slash_dirs:
                    rel_txt += '/'
                if (include_hidden or not is_hidden(rel_dir)) and not should_ignore(rel_txt, ignore_patterns):
                    items.append(rel_txt)

        # Ha csak mappákat kér a user, felesleges fájlokkal foglalkozni
        if dirs_only:
            # Rejtett szűrés optimalizálás: ha nem kér rejtettet, takarítsuk ki a belépést
            if not include_hidden:
                dirnames[:] = [d for d in dirnames if not d.startswith('.')]
            # Ignore minták szerint is ki lehet dobni mappákat a bejárásból
            if ignore_patterns:
                dirnames[:] = [
                    d for d in dirnames
                    if not should_ignore((Path(dirpath) / d).relative_to(root).as_posix() + ('/' if slash_dirs else ''), ignore_patterns)
                ]
            continue

        # Fájlok kezelése
        for fn in filenames:
            fpath = dpath / fn
            rel = fpath.relative_to(root)
            rel_txt = rel.as_posix()
            if not include_hidden and is_hidden(rel):
                continue
            if should_ignore(rel_txt, ignore_patterns):
                continue
            items.append(rel_txt)

        # Bejárási optimalizálás rejtettekre / ignore-okra
        if not include_hidden:
            dirnames[:] = [d for d in dirnames if not d.startswith('.')]
        if ignore_patterns:
            dirnames[:] = [
                d for d in dirnames
                if not should_ignore((Path(dirpath) / d).relative_to(root).as_posix() + ('/' if slash_dirs else ''), ignore_patterns)
            ]

    # Rendezzük determinisztikusan (case-insensitive, majd tiebreak az eredetivel)
    items.sort(key=lambda s: (s.casefold(), s))
    return items

def main():
    ap = argparse.ArgumentParser(
        description="Relatív elérési utak kigyűjtése egy könyvtárból és mentése .txt-be."
    )
    ap.add_argument("root", type=Path, help="A bejárandó gyökérkönyvtár.")
    ap.add_argument("-o", "--output", type=Path, default=Path("paths.txt"),
                    help="Kimeneti .txt fájl (alapértelmezés: paths.txt).")
    g = ap.add_mutually_exclusive_group()
    g.add_argument("--files-only", action="store_true", help="Csak fájlok listázása.")
    g.add_argument("--dirs-only", action="store_true", help="Csak könyvtárak listázása.")
    ap.add_argument("--include-hidden", action="store_true",
                    help="Rejtett elemek ('.' kezdetű komponensek) felvétele is.")
    ap.add_argument("--ignore", action="append", default=[],
                    help="Glob minta az ignorálandó utakhoz. Többször is megadható. Pl.: --ignore '__pycache__' --ignore '*.pyc'")
    ap.add_argument("--follow-symlinks", action="store_true", help="Szimbolikus linkek követése az os.walk során.")
    ap.add_argument("--slash-dirs", action="store_true", help="Könyvtárak végére '/' kerüljön a listában.")
    ap.add_argument("--append", action="store_true", help="Ne írja felül a kimeneti fájlt, hanem fűzze hozzá.")
    args = ap.parse_args()

    root: Path = args.root.resolve()
    if not root.exists() or not root.is_dir():
        ap.error(f"A megadott gyökér nem létező könyvtár: {root}")

    items = collect_paths(
        root=root,
        include_hidden=args.include_hidden,
        files_only=args.files_only,
        dirs_only=args.dirs_only,
        ignore_patterns=args.ignore or [],
        follow_symlinks=args.follow_symlinks,
        slash_dirs=args.slash_dirs,
    )

    mode = "a" if args.append else "w"
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open(mode, encoding="utf-8", newline="\n") as f:
        for line in items:
            f.write(line + "\n")

    print(f"OK: {len(items)} elem kiírva ide: {args.output}")

if __name__ == "__main__":
    main()
