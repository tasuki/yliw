#!/usr/bin/env python3
"""Generate a simple 'your life in weeks' HTML page from a TOML file.

Usage:
    python3 life_in_weeks.py sample/gregor-mendel.toml > gregor-mendel.html
"""

from __future__ import annotations

import argparse
import datetime as dt
import html
import sys
import tomllib
from typing import Iterable

WEEKS_PER_YEAR = 52
DAYS_PER_WEEK = 7


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("toml_file", help="Input TOML file")
    return parser.parse_args()


def load_person(path: str) -> dict:
    with open(path, "rb") as f:
        data = tomllib.load(f)
    try:
        return data["person"]
    except KeyError as exc:
        raise SystemExit("TOML must contain a [person] table") from exc


def collect_dates(person: dict) -> list[dt.date]:
    dates: list[dt.date] = []

    for section_name in ("places", "occupations"):
        for item in person.get(section_name, []):
            dates.append(item["from"])
            if "to" in item:
                dates.append(item["to"])

    for event in person.get("events", []):
        dates.append(event["date"])

    return dates


def fill_missing_to(items: list[dict]) -> list[dict]:
    ordered = sorted(items, key=lambda item: item["from"])
    result: list[dict] = []

    for index, item in enumerate(ordered):
        item = dict(item)
        if "to" not in item:
            if index + 1 < len(ordered):
                item["to"] = ordered[index + 1]["from"] - dt.timedelta(days=1)
        result.append(item)

    return result


def week_row_start(year: int) -> dt.date:
    return monday_for_week(dt.date(year, 1, 1))



def week_index_in_year(day: dt.date) -> int:
    return min(
        (monday_for_week(day) - week_row_start(day.year)).days // DAYS_PER_WEEK,
        WEEKS_PER_YEAR - 1,
    )



def week_start_date(year: int, week_index: int) -> dt.date:
    return week_row_start(year) + dt.timedelta(days=week_index * DAYS_PER_WEEK)



def week_end_date(year: int, week_index: int) -> dt.date:
    if week_index == WEEKS_PER_YEAR - 1:
        return dt.date(year, 12, 31)
    return week_start_date(year, week_index) + dt.timedelta(days=DAYS_PER_WEEK - 1)



def find_item_for_date(items: Iterable[dict], day: dt.date) -> dict | None:
    for item in items:
        item_to = item.get("to")
        if item["from"] <= day and (item_to is None or day <= item_to):
            return item
    return None



def find_item_for_week(items: Iterable[dict], start: dt.date, end: dt.date) -> dict | None:
    match = None
    for item in items:
        item_to = item.get("to")
        if item["from"] <= end and (item_to is None or start <= item_to):
            match = item
    return match



def events_by_week(events: list[dict]) -> dict[tuple[int, int], list[dict]]:
    grouped: dict[tuple[int, int], list[dict]] = {}
    for event in events:
        key = (event["date"].year, week_index_in_year(event["date"]))
        grouped.setdefault(key, []).append(event)
    return grouped


def monday_for_week(day: dt.date) -> dt.date:
    return day - dt.timedelta(days=day.weekday())


def format_detail_date(day: dt.date) -> str:
    return f'<span class="detail-date">{html.escape(day.isoformat())}</span>'


def build_details_html(
    start: dt.date,
    week_events: list[dict],
    place_occupation_parts: list[str],
) -> str:
    if week_events:
        return "<br>".join(
            f'{format_detail_date(event["date"])} '
            f'{html.escape(event["emoji"])} {html.escape(event["text"])}'
            for event in week_events
        )
    if place_occupation_parts:
        return f'{format_detail_date(monday_for_week(start))} {html.escape("; ".join(place_occupation_parts))}'
    return ""



def style_attr(parts: list[str]) -> str:
    return " ".join(parts)



def render_html(person: dict) -> str:
    name = person.get("name", "Your Life in Weeks")
    places = fill_missing_to(person.get("places", []))
    occupations = fill_missing_to(person.get("occupations", []))
    events = person.get("events", [])

    all_dates = collect_dates(person)
    if not all_dates:
        raise SystemExit("No dates found in TOML")

    birth_date = min(all_dates)
    end_date = max(all_dates)
    event_map = events_by_week(events)

    years = list(range(birth_date.year, end_date.year + 1))

    rows: list[str] = []
    birth_week = week_index_in_year(birth_date)
    detail_colspan = WEEKS_PER_YEAR + 1

    for year in years:
        cells: list[str] = []

        for week_index in range(WEEKS_PER_YEAR):
            if year == birth_date.year and week_index < birth_week:
                cells.append('<td class="cell pad"></td>')
                continue

            start = week_start_date(year, week_index)
            end = week_end_date(year, week_index)

            if end < birth_date or start > end_date:
                cells.append('<td class="cell pad"></td>')
                continue

            place = find_item_for_week(places, start, end)
            occupation = find_item_for_week(occupations, start, end)
            week_events = event_map.get((year, week_index), [])

            styles = []
            if place:
                styles.append(f"border-color: var(--border-{place['color']});")
            if occupation:
                styles.append(f"background: var(--bg-{occupation['color']});")

            place_occupation_parts = []
            if place:
                place_occupation_parts.append(place['label'])
            if occupation:
                place_occupation_parts.append(occupation['label'])

            details_html = build_details_html(start, week_events, place_occupation_parts)

            details_attr = ""
            extra_classes = ""
            if details_html:
                escaped_details = html.escape(details_html, quote=True)
                details_attr = f' data-details-html="{escaped_details}"'
                extra_classes = " has-details"

            date_attrs = f' data-start="{start.isoformat()}" data-end="{end.isoformat()}"'
            content = html.escape("".join(event["emoji"] for event in week_events))
            cells.append(
                f'<td class="cell{extra_classes}" style="{style_attr(styles)}"{date_attrs}{details_attr}>{content}</td>\n'
            )

        rows.append(
            "<tr>"
            f'<td class="year">{year}</td>\n'
            + "".join(cells)
            + "</tr>\n"
            + (
                f'<tr class="details-row" hidden><td colspan="{detail_colspan}">' 
                '<div class="inline-details"></div>'
                '</td></tr>\n'
            )
        )

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{html.escape(name)}</title>
  <style>
    :root {{
      --cell-size: 22px;
      --gap: 1px;
      --border: 1px;
      --base0: #FFF8E6;
      --base1: #E8E5D1;
      --base2: #D2D3BE;
      --base5: #617C6D;
      --base7: #0D3A3C;
      --base: var(--base7);
      --bg-gray: #ECE9D4;
      --bg-red: #FFE4E3;
      --bg-orange: #FFE5D2;
      --bg-yellow: #FEEEC1;
      --bg-green: #E7F7BB;
      --bg-cyan: #D4F8ED;
      --bg-blue: #DBEEFF;
      --bg-purple: #E7EAFF;
      --bg-magenta: #FFE1F4;
      --border-none: #D2D3BE;
      --border-gray: #617C6D;
      --border-red: #DE1D3F;
      --border-orange: #C9690C;
      --border-yellow: #AB8704;
      --border-green: #819808;
      --border-cyan: #04A388;
      --border-blue: #1E86CD;
      --border-purple: #6A69DB;
      --border-magenta: #C13B9F;
    }}
    @media (prefers-color-scheme: dark) {{
      :root {{
        --base0: #002A31;
        --base1: #0D3A3C;
        --base2: #375B53;
        --base5: #BBC1AB;
        --base7: #E8E5D1;
        --bg-gray: #0D3A3C;
        --bg-red: #542526;
        --bg-orange: #4D2C15;
        --bg-yellow: #3F3414;
        --bg-green: #3A450B;
        --bg-cyan: #044E40;
        --bg-blue: #05436C;
        --bg-purple: #2F3058;
        --bg-magenta: #4D2641;
        --border-none: #375B53;
        --border-gray: #BBC1AB;
        --border-red: #FC4257;
        --border-orange: #EC7C0E;
        --border-yellow: #C7A01E;
        --border-green: #98B224;
        --border-cyan: #21BFA0;
        --border-blue: #249FF3;
        --border-purple: #8082F7;
        --border-magenta: #DD56B8;
      }}
    }}
    body {{
      font-family: system-ui, sans-serif;
      font-size: 16px;
      margin: 24px;
      background-color: var(--base0);
      color: var(--base5);
      text-align: center;
    }}
    h1 {{
      font-size: 24px;
    }}
    .wrapper {{
      width: 100%;
      overflow-x: auto;
      overflow-y: visible;
      -webkit-overflow-scrolling: touch;
    }}
    table {{
      border-collapse: separate;
      border-spacing: var(--gap);
      width: max-content;
      margin: 0 auto;
    }}
    .year {{
      text-align: right;
      padding-right: 10px;
      white-space: nowrap;
    }}
    .cell {{
      width: var(--cell-size);
      min-width: var(--cell-size);
      max-width: var(--cell-size);
      height: var(--cell-size);
      min-height: var(--cell-size);
      max-height: var(--cell-size);
      box-sizing: border-box;
      border: var(--border) solid var(--base1);
      border-radius: 3px;
      text-align: center;
      vertical-align: middle;
      line-height: 1;
      padding: 0;
      overflow: hidden;
    }}
    .cell.has-details {{
      cursor: pointer;
      user-select: none;
      -webkit-user-select: none;
    }}
    .cell.has-details:focus-visible {{
      outline: 2px solid var(--base7);
      outline-offset: 1px;
    }}
    .cell.current-week,
    .cell.expanded {{
      border-color: var(--base) !important;
    }}
    .details-row td {{
      padding: 6px 0 10px;
    }}
    .inline-details {{
      max-width: 500px;
      margin: 0 auto;
      padding: 8px 14px;
      border: 1px solid var(--base2);
      border-radius: 5px;
      background: var(--base0);
      text-align: left;
    }}
    .detail-date {{
      color: var(--base2);
    }}
    .pad {{
      border: none;
      background: transparent;
    }}
    .empty {{
      border-color: var(--base1);
      background: transparent;
    }}
  </style>
</head>
<body>
  <h1>{html.escape(name)}</h1>
  <div class="wrapper">
    <table>
      <tbody>
        {''.join(rows)}
      </tbody>
    </table>
  </div>
  <script>
    (() => {{
      let openRow = null;
      let openCell = null;

      function markCurrentWeek() {{
        const today = new Date().toISOString().slice(0, 10);
        const currentCell = Array.from(document.querySelectorAll('.cell[data-start][data-end]')).find(
          (cell) => cell.dataset.start <= today && today <= cell.dataset.end
        );
        if (currentCell) currentCell.classList.add('current-week');
      }}

      function showDetails(cell) {{
        const detailsHtml = cell.dataset.detailsHtml;
        if (!detailsHtml) return;

        if (openCell && openCell !== cell) {{
          openCell.removeAttribute('aria-pressed');
          openCell.classList.remove('expanded');
        }}

        if (openRow && openRow !== cell.parentElement.nextElementSibling) {{
          openRow.hidden = true;
        }}

        const detailsRow = cell.parentElement.nextElementSibling;
        const detailsBox = detailsRow.querySelector('.inline-details');
        const isSameCell = openCell === cell && !detailsRow.hidden;

        if (isSameCell) {{
          detailsRow.hidden = true;
          cell.removeAttribute('aria-pressed');
          cell.classList.remove('expanded');
          openRow = null;
          openCell = null;
          return;
        }}

        detailsBox.innerHTML = detailsHtml;
        detailsRow.hidden = false;
        cell.setAttribute('aria-pressed', 'true');
        cell.classList.add('expanded');
        openRow = detailsRow;
        openCell = cell;
      }}

      markCurrentWeek();

      document.addEventListener('click', (event) => {{
        const cell = event.target.closest('.cell.has-details');
        if (!cell) return;
        showDetails(cell);
      }});

      document.addEventListener('keydown', (event) => {{
        if (event.key !== 'Enter' && event.key !== ' ') return;
        const cell = event.target.closest('.cell.has-details');
        if (!cell) return;
        event.preventDefault();
        showDetails(cell);
      }});
    }})();
  </script>
</body>
</html>
"""


def main() -> int:
    args = parse_args()
    person = load_person(args.toml_file)
    sys.stdout.write(render_html(person))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
