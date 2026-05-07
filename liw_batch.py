#!/usr/bin/env python3
"""Generate .html files for every .toml file in one or more directories.

Usage:
    python3 liw_batch.py sample
    python3 liw_batch.py sample other-directory
"""

from __future__ import annotations

import argparse
from pathlib import Path

from liw import load_person, render_html


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "directories",
        nargs="+",
        help="One or more directories containing .toml files",
    )
    return parser.parse_args()


def iter_toml_files(directory: Path) -> list[Path]:
    return sorted(path for path in directory.rglob("*.toml") if path.is_file())


def process_directory(directory: Path) -> int:
    if not directory.exists():
        raise SystemExit(f"Directory not found: {directory}")
    if not directory.is_dir():
        raise SystemExit(f"Not a directory: {directory}")

    count = 0
    for toml_path in iter_toml_files(directory):
        html_path = toml_path.with_suffix(".html")
        person = load_person(str(toml_path))
        html_path.write_text(render_html(person), encoding="utf-8")
        print(f"Wrote {html_path}")
        count += 1
    return count


def main() -> int:
    args = parse_args()
    total = 0

    for directory in args.directories:
        total += process_directory(Path(directory))

    print(f"Generated {total} HTML file(s).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
