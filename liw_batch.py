#!/usr/bin/env python3
"""Generate .html files for every .toml file in one or more directories.

Usage:
    python3 liw_batch.py sample
    python3 liw_batch.py sample other-directory
"""

from __future__ import annotations

import argparse
import html
from pathlib import Path

from liw import collect_dates, load_person, render_html


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


def build_index(entries: list[tuple[str, str, int]]) -> str:
    items = "\n".join(
        f'      <li>{year} — <a href="{html.escape(href, quote=True)}">{html.escape(name)}</a></li>'
        for href, name, year in entries
    )
    return f"""<!DOCTYPE html>
<html lang=\"en\">
<head>
  <meta charset=\"utf-8\">
  <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\">
  <title>Your Life In Weeks</title>
  <style>
    :root {{
      --base0: #FFF8E6;
      --base5: #617C6D;
      --base7: #0D3A3C;
      --link: #1E86CD;
      --visited: #6A69DB;
    }}
    @media (prefers-color-scheme: dark) {{
      :root {{
        --base0: #002A31;
        --base5: #BBC1AB;
        --base7: #E8E5D1;
        --link: #249FF3;
        --visited: #8082F7;
      }}
    }}
    body {{
      font-family: system-ui, sans-serif;
      max-width: 700px;
      margin: 40px auto;
      padding: 0 16px;
      line-height: 1.5;
      background: var(--base0);
      color: var(--base5);
    }}
    a {{
      color: var(--link);
    }}
    a:visited {{
      color: var(--visited);
    }}
    li {{
      margin-top: 0.4rem;
    }}
  </style>
</head>
<body>
  <h1>Your Life In Weeks</h1>
  <ul>
{items}
  </ul>
</body>
</html>
"""


def extract_start_year(person: dict) -> int:
    return min(collect_dates(person)).year


def build_directory_indexes(root: Path, page_names: dict[Path, str], page_years: dict[Path, int]) -> int:
    directories = sorted(path for path in root.rglob("*") if path.is_dir())
    directories.insert(0, root)

    directory_years: dict[Path, int] = {}
    count = 0
    for directory in reversed(directories):
        entries: list[tuple[str, str, int]] = []
        entry_years: list[int] = []

        for child in sorted(path for path in directory.iterdir() if path.is_dir()):
            year = directory_years.get(child)
            if year is not None and (child / "index.html").exists():
                entries.append((f"{child.name}/", child.name, year))
                entry_years.append(year)

        for child in sorted(path for path in directory.glob("*.html") if path.name != "index.html"):
            year = page_years.get(child)
            if year is None:
                continue
            entries.append((child.name, page_names.get(child, child.stem), year))
            entry_years.append(year)

        if not entries:
            continue

        entries.sort(key=lambda entry: (entry[2], entry[1].casefold()))
        directory_years[directory] = min(entry_years)

        index_path = directory / "index.html"
        index_path.write_text(build_index(entries), encoding="utf-8")
        print(f"Wrote {index_path}")
        count += 1

    return count


def process_directory(directory: Path, output_directory: Path | None = None) -> int:
    if not directory.exists():
        raise SystemExit(f"Directory not found: {directory}")
    if not directory.is_dir():
        raise SystemExit(f"Not a directory: {directory}")

    destination_root = output_directory or directory
    destination_root.mkdir(parents=True, exist_ok=True)

    count = 0
    page_names: dict[Path, str] = {}
    page_years: dict[Path, int] = {}
    for toml_path in iter_toml_files(directory):
        relative = toml_path.relative_to(directory)
        html_path = destination_root / relative.with_suffix(".html")
        html_path.parent.mkdir(parents=True, exist_ok=True)
        person = load_person(str(toml_path))
        html_path.write_text(render_html(person), encoding="utf-8")
        page_names[html_path] = person.get("name", relative.stem)
        page_years[html_path] = extract_start_year(person)
        print(f"Wrote {html_path}")
        count += 1

    return count + build_directory_indexes(destination_root, page_names, page_years)


def main() -> int:
    args = parse_args()
    total = 0

    for directory in args.directories:
        total += process_directory(Path(directory))

    print(f"Generated {total} HTML file(s), including directory indexes.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
