#!/usr/bin/env python3
"""Build a static site for GitHub Pages from sample TOML files.

Usage:
    python3 build_site.py sample dist
"""

from __future__ import annotations

import argparse
from pathlib import Path

from liw_batch import process_directory


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", help="Directory containing .toml files")
    parser.add_argument("output", help="Directory to write the site into")
    return parser.parse_args()

def main() -> int:
    args = parse_args()
    source = Path(args.source)
    output = Path(args.output)

    if not source.exists() or not source.is_dir():
        raise SystemExit(f"Source directory not found: {source}")

    output.mkdir(parents=True, exist_ok=True)

    process_directory(source, output)
    (output / ".nojekyll").write_text("", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
